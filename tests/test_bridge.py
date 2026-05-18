"""Tests for HiveMindMatrixBridge.

Same shape as the deltachat-bridge test suite:
- HiveMind side replaced with AsyncFakeHiveMessageBus.
- Matrix bot replaced with _StubBot that records send_text calls and
  exposes a hook to simulate an incoming Matrix room event.
"""
from __future__ import annotations

import asyncio
import threading
import unittest
from unittest.mock import MagicMock

from hivemind_bus_client.fakebus import AsyncFakeHiveMessageBus
from hivemind_bus_client.message import HiveMessage, HiveMessageType
from ovos_bus_client.message import Message

from hm_matrix_bridge import HiveMindMatrixBridge


class _StubRoom:
    def __init__(self):
        self.sent: list[str] = []

    def send_text(self, text):
        self.sent.append(text)


class _StubBot:
    """Stand-in for MatrixBot. Records sends; exposes a hook to fire a
    fake room event from any thread."""

    def __init__(self, bot_mention="thehivebot"):
        self.bot_mention = bot_mention
        self.room = _StubRoom()
        self.on_message = None

    def fire_event(self, body: str, sender: str = "alice@matrix",
                   *, from_thread: bool = False) -> None:
        event = {
            "content": {"body": body, "msgtype": "m.text"},
            "sender": sender,
        }
        cb = self.on_message
        assert cb is not None, "bridge.start() not called"
        if from_thread:
            done = threading.Event()
            def _go():
                cb(event)
                done.set()
            threading.Thread(target=_go, daemon=True).start()
            done.wait(timeout=2)
        else:
            cb(event)


def _make_bridge(*, timeout: float = 0.3) -> HiveMindMatrixBridge:
    return HiveMindMatrixBridge(
        bot=_StubBot(),
        client=AsyncFakeHiveMessageBus(site_id="test-matrix"),
        response_timeout=timeout,
    )


def _run(coro):
    return asyncio.run(coro)


class TestLifecycle(unittest.TestCase):
    def test_start_stop_idempotent(self):
        bridge = _make_bridge()

        async def scenario():
            await bridge.start()
            self.assertTrue(bridge._started)
            self.assertTrue(bridge.client.connected_event.is_set())
            await bridge.start()  # second call is a no-op
            await bridge.stop()
            await bridge.stop()  # second close is a no-op
            self.assertFalse(bridge._started)

        _run(scenario())

    def test_stop_before_start(self):
        bridge = _make_bridge()
        _run(bridge.stop())  # must not raise


class TestMatrixToHivemind(unittest.TestCase):
    def test_mention_triggers_round_trip(self):
        bridge = _make_bridge(timeout=0.2)

        async def scenario():
            await bridge.start()
            try:
                # auto-respond with a speak message when an utterance arrives
                def auto_reply(env):
                    payload = env.payload
                    asyncio.create_task(
                        bridge.client.emit(Message(
                            "speak",
                            {"utterance": "9am"},
                            payload.context,
                        ))
                    )
                bridge.client.on(HiveMessageType.BUS, auto_reply)

                bridge.bot.fire_event(
                    "@thehivebot what time is it",
                    from_thread=True,
                )
                # let the scheduled task run + the wait_for_response complete
                await asyncio.sleep(0.1)
            finally:
                await bridge.stop()

        _run(scenario())
        self.assertEqual(bridge.bot.room.sent, ["9am"])

    def test_no_mention_is_ignored(self):
        bridge = _make_bridge()

        async def scenario():
            await bridge.start()
            try:
                bridge.bot.fire_event("hello world", from_thread=True)
                await asyncio.sleep(0.05)
            finally:
                await bridge.stop()

        _run(scenario())
        # No utterance forwarded, no reply sent.
        self.assertEqual(bridge.client.emitted, [])
        self.assertEqual(bridge.bot.room.sent, [])

    def test_mention_strip_variants(self):
        bridge = _make_bridge(timeout=0.2)

        async def scenario():
            await bridge.start()
            try:
                # @bot prefix, bot: prefix, and bare bot mention should all
                # strip cleanly before forwarding to HiveMind.
                bridge.bot.fire_event("@thehivebot   foo", from_thread=True)
                bridge.bot.fire_event("thehivebot: bar", from_thread=True)
                bridge.bot.fire_event("thehivebot baz", from_thread=True)
                await asyncio.sleep(0.05)
            finally:
                await bridge.stop()

        _run(scenario())
        emitted_utts = [
            env.payload.data["utterances"][0]
            for env in bridge.client.emitted
        ]
        self.assertEqual(sorted(emitted_utts), ["bar", "baz", "foo"])

    def test_empty_after_strip_is_dropped(self):
        bridge = _make_bridge()

        async def scenario():
            await bridge.start()
            try:
                bridge.bot.fire_event("@thehivebot", from_thread=True)
                await asyncio.sleep(0.05)
            finally:
                await bridge.stop()

        _run(scenario())
        self.assertEqual(bridge.client.emitted, [])

    def test_event_before_start_is_dropped(self):
        bridge = _make_bridge()
        bridge.bot.on_message = bridge._on_matrix_message
        bridge.bot.fire_event("@thehivebot hi")  # no start() called
        self.assertEqual(bridge.client.emitted, [])
        self.assertEqual(bridge.bot.room.sent, [])


class TestHivemindReplyFailure(unittest.TestCase):
    def test_timeout_returns_error_text(self):
        # No auto-responder registered, so wait_for_response times out.
        bridge = _make_bridge(timeout=0.05)

        async def scenario():
            await bridge.start()
            try:
                bridge.bot.fire_event("@thehivebot orphan", from_thread=True)
                await asyncio.sleep(0.2)
            finally:
                await bridge.stop()

        _run(scenario())
        self.assertEqual(bridge.bot.room.sent, ["Error"])

    def test_send_text_exception_is_logged(self):
        bridge = _make_bridge(timeout=0.05)
        bridge.bot.room.send_text = MagicMock(side_effect=RuntimeError("boom"))

        async def scenario():
            await bridge.start()
            try:
                bridge.bot.fire_event("@thehivebot x", from_thread=True)
                await asyncio.sleep(0.2)
            finally:
                await bridge.stop()

        # must not raise
        _run(scenario())


if __name__ == "__main__":
    unittest.main()
