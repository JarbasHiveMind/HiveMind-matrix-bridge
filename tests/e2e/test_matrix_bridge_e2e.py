"""REAL end-to-end test for HiveMind-matrix-bridge.

This drives the bridge's *actual* HiveMind code path against a *real*
hivemind-core hub running over a real localhost WebSocket (hivescope's
``LoopbackNetworkProtocol``). Only the Matrix side is mocked — a full Matrix
loop would need a self-hosted homeserver (see the TODO below).

What is exercised for real
--------------------------
  * ``HiveMindMatrixBridge`` (the production bridge class)
  * ``ovos_hivemind_solver.HiveMindSolver`` (the bridge's HiveMind brain)
  * ``hivemind_bus_client.HiveMessageBusClient`` over a real WebSocket
  * a real ``hivemind-core`` hub (handshake, encryption, whitelist ACL,
    BUS message routing) booted by hivescope ``TopologyBuilder``

What is mocked
--------------
  * ``matrix-client`` / ``MatrixBot`` — no live homeserver. The mocked
    ``MatrixClient.join_room`` returns a fake room whose ``send_text`` we
    capture so we can assert the bridge's *outbound* Matrix reply. We do NOT
    ``importorskip`` matrix-client: it is a hard dependency, installed and
    imported; we patch the network-touching client class explicitly.

The proven round-trip
---------------------
  inbound Matrix message
    -> bridge.handle_matrix_utterance()
    -> HiveMindSolver.get_spoken_answer()
    -> HiveMessageBusClient.emit_mycroft("recognizer_loop:utterance")  [WebSocket]
    -> real hivemind-core hub admits it (whitelist ACL) and routes to its agent bus
    -> agent-bus responder emits "speak"                               [WebSocket back]
    -> HiveMessageBusClient on_mycroft("speak") -> solver._receive_answer()
    -> get_spoken_answer() returns the reply text
    -> bridge calls bot.room.send_text(reply)  [captured outbound Matrix message]

TODO (natural follow-up): a FULL Matrix loop test that boots a containerized
homeserver (Conduit or Synapse) instead of mocking matrix-client, registers a
bot user + room, posts a real Matrix message, and asserts the reply lands back
in the room over the real Matrix protocol. That closes the only mocked seam
here. Out of scope for this test because it needs a homeserver container.
"""
import threading
import time
from unittest.mock import MagicMock, patch

import pytest
from ovos_bus_client.message import Message

from hivemind_bus_client.client import HiveMessageBusClient
from hivemind_bus_client.identity import NodeIdentity
from hivescope.topology import TopologyBuilder


SAT_KEY = "matrix-bridge-key"
SAT_PASSWORD = "matrix-bridge-password"
BOT_MENTION = "thehivebot"
HUB_REPLY = "the answer from the real hivemind hub"


def _extract_host_port(url: str):
    """Extract (host, port) from a ``ws://127.0.0.1:PORT/`` loopback URL."""
    parts = url.replace("ws://", "").replace("wss://", "").rstrip("/").split(":")
    return parts[0], int(parts[1])


def _make_real_client(url: str, key: str, password: str,
                      name: str = "matrix-bridge") -> HiveMessageBusClient:
    """A real HiveMessageBusClient pointed at the loopback hub."""
    host, port = _extract_host_port(url)
    identity = NodeIdentity()
    identity.access_key = key
    identity.password = password
    identity.default_master = f"ws://{host}"
    identity.default_port = port
    identity.name = name
    identity.site_id = "matrix"
    return HiveMessageBusClient(
        key=key,
        password=password,
        host=f"ws://{host}",
        port=port,
        useragent=name,
        self_signed=False,
        identity=identity,
    )


def _setup_agent_responder(master_node, answer: str = HUB_REPLY):
    """Make the real hub's agent answer utterances with a ``speak``.

    hivescope's ``TestAgentProtocol`` forwards inbound
    ``recognizer_loop:utterance`` onto the master's internal agent bus. We
    register a handler there that mimics a skill: emit a ``speak`` carrying the
    answer, then ``ovos.utterance.handled`` to end the turn.

    Reverse routing is destination-based: hivemind-core stamps the injected
    utterance with ``context["peer"]`` / ``context["source"]`` = the
    originating satellite, and the agent protocol's ``handle_internal_mycroft``
    only forwards a bus message back to a satellite whose peer matches the
    message's ``context["destination"]``. A real skill achieves this with
    ``message.response()`` (which swaps source→destination); we do the same via
    ``msg.reply(...)`` so the ``speak`` carries ``destination`` = the bridge's
    peer and routes back over the WebSocket, exactly as a live deployment would.
    """
    bus = master_node.agent_protocol.bus

    def _responder(msg: Message):
        # msg.reply swaps source/destination, so the speak is addressed back to
        # the originating satellite (the bridge), matching real skill behaviour.
        bus.emit(msg.reply("speak", {"utterance": answer}))
        bus.emit(msg.reply("ovos.utterance.handled", {}))

    bus.on("recognizer_loop:utterance", _responder)


def _build_bridge_with_mocked_matrix(captured_sends):
    """Construct the REAL HiveMindMatrixBridge with only the Matrix side mocked.

    Returns ``(bridge, hm_client_holder)`` where the bridge is the production
    class. ``MatrixClient`` (the only network-touching Matrix piece) is patched
    so ``MatrixBot.__init__`` runs for real but talks to a fake homeserver; the
    fake room's ``send_text`` appends to ``captured_sends``. ``HiveMindSolver``
    is patched to *not* autoconnect during construction (no identity on disk in
    CI); the test binds a real loopback client afterwards.
    """
    import hm_matrix_bridge

    fake_room = MagicMock(name="matrix_room")
    fake_room.send_text.side_effect = lambda text: captured_sends.append(text)

    fake_client = MagicMock(name="matrix_client")
    fake_client.join_room.return_value = fake_room
    fake_client.user_id = "@thehivebot:matrix.example"

    # Patch MatrixClient where matrixapi imports it so MatrixBot.__init__ runs
    # for real against a fake homeserver (no live network).
    matrix_client_patch = patch(
        "hm_matrix_bridge.matrixapi.MatrixClient", return_value=fake_client
    )

    # Patch HiveMindSolver so the bridge constructs without autoconnecting to a
    # configured identity. We bind a real loopback client to the solver next.
    from ovos_hivemind_solver import HiveMindSolver
    real_solver_holder = {}

    def _solver_factory(config=None, **kwargs):
        cfg = dict(config or {})
        cfg["autoconnect"] = False  # we connect explicitly to the loopback hub
        solver = HiveMindSolver(config=cfg, **kwargs)
        real_solver_holder["solver"] = solver
        return solver

    solver_patch = patch("hm_matrix_bridge.HiveMindSolver",
                         side_effect=_solver_factory)

    with matrix_client_patch, solver_patch:
        bridge = hm_matrix_bridge.HiveMindMatrixBridge(
            matrix_host="https://matrix.example",
            matrix_token="fake-token",
            room_alias="#hivemind-bots:matrix.example",
            bot_mention=BOT_MENTION,
        )

    return bridge, real_solver_holder["solver"]


def _bind_real_hivemind(solver, hub_url):
    """Wire the bridge's real solver to a real HiveMessageBusClient + hub.

    Replicates exactly what ``HiveMindSolver.connect()`` does (creates the
    client, connects, registers ``on_mycroft`` handlers for ``speak`` and
    ``ovos.utterance.handled``) but points the client at our loopback hub.
    """
    client = _make_real_client(hub_url, SAT_KEY, SAT_PASSWORD)
    client.connect(site_id="matrix")
    client.wait_for_handshake(timeout=10)
    assert client.handshake_event.is_set(), "handshake to real hub did not complete"

    solver.bind(client)
    client.on_mycroft("speak", solver._receive_answer)
    client.on_mycroft("ovos.utterance.handled", solver._end_of_response)
    # give the encrypted HELLO time to register the peer on the hub
    time.sleep(1)
    return client


class TestMatrixBridgeRealHiveMindE2E:
    """The genuine round-trip across a real hub."""

    def test_inbound_matrix_to_hub_to_outbound_matrix(self):
        captured_sends = []

        b = TopologyBuilder()
        m = b.add_master("M0", use_loopback=True)
        # hivemind-core is whitelist-only / deny-by-default. Grant the satellite
        # exactly the type the bridge injects.
        m.register_satellite(SAT_KEY, password=SAT_PASSWORD,
                             allowed_types=["recognizer_loop:utterance"])
        b.start_all()

        client = None
        try:
            _setup_agent_responder(m, answer=HUB_REPLY)

            bridge, solver = _build_bridge_with_mocked_matrix(captured_sends)
            client = _bind_real_hivemind(solver, m.network_protocol.url)

            assert len(m.connected_peers()) == 1, \
                f"bridge satellite not connected to hub: {m.connected_peers()}"

            # Inject an inbound Matrix message addressed to the bot. This is the
            # exact event shape MatrixBot delivers to bridge.handle_matrix_utterance.
            inbound = {
                "sender": "@human:matrix.example",
                "content": {"body": f"{BOT_MENTION} what is the answer"},
            }
            bridge.handle_matrix_utterance(inbound)

            # The bridge sent the reply outbound to Matrix (our captured room).
            assert captured_sends, \
                "bridge did not send any outbound Matrix message"
            assert captured_sends[-1] == HUB_REPLY, (
                f"outbound Matrix reply {captured_sends[-1]!r} "
                f"did not match the real hub's speak {HUB_REPLY!r}"
            )

            # And the round-trip really crossed the hub: the hub's agent bus saw
            # the utterance the bridge injected over the WebSocket.
            m.agent_protocol.assert_injected("recognizer_loop:utterance", count=1)
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
            b.stop_all()

    def test_unmentioned_message_does_not_reach_hub(self):
        """A Matrix message without the bot mention is ignored — no hub traffic."""
        captured_sends = []

        b = TopologyBuilder()
        m = b.add_master("M0", use_loopback=True)
        m.register_satellite(SAT_KEY, password=SAT_PASSWORD,
                             allowed_types=["recognizer_loop:utterance"])
        b.start_all()

        client = None
        try:
            _setup_agent_responder(m)
            bridge, solver = _build_bridge_with_mocked_matrix(captured_sends)
            client = _bind_real_hivemind(solver, m.network_protocol.url)

            bridge.handle_matrix_utterance({
                "sender": "@human:matrix.example",
                "content": {"body": "just chatting, no mention here"},
            })

            assert captured_sends == [], \
                "bridge sent an outbound Matrix message for an unmentioned event"
            m.agent_protocol.assert_injected("recognizer_loop:utterance", count=0)
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
            b.stop_all()
