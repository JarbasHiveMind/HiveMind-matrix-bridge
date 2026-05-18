"""HiveMind <-> Matrix bridge (async).

Composition design (replaces the previous HiveMindSolver wrapper):

- :class:`hm_matrix_bridge.matrixapi.MatrixBot` wraps the classic
  ``matrix_client`` Python library, runs its blocking listener on a
  daemon thread (``start_listener_thread()``), and fires ``on_message``
  from that thread when a chat message arrives.
- :class:`AsyncHiveMessageBusClient` is the asyncio-native HiveMind
  client (``hivemind-bus-client[async]>=0.8.0``). Runs on the
  application's event loop.
- :class:`HiveMindMatrixBridge` composes the two. The Matrix callback
  (which fires on the matrix-client thread) is bridged onto the asyncio
  loop with :func:`asyncio.run_coroutine_threadsafe`. The full
  ask-and-reply happens as an async task; the matrix callback returns
  immediately so it does not block matrix-client's listener.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from hivemind_bus_client.async_client import AsyncHiveMessageBusClient
from hivemind_bus_client.identity import NodeIdentity
from ovos_bus_client.message import Message
from ovos_utils.log import LOG

from hm_matrix_bridge.matrixapi import MatrixBot


class HiveMindMatrixBridge:
    platform = "HiveMindMatrixBridgeV0.3"

    def __init__(self,
                 matrix_host: Optional[str] = None,
                 matrix_token: Optional[str] = None,
                 room_alias: Optional[str] = None,
                 bot_mention: Optional[str] = None,
                 greeting: Optional[str] = None,
                 key: Optional[str] = None,
                 password: Optional[str] = None,
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 identity: Optional[NodeIdentity] = None,
                 *,
                 client: Optional[AsyncHiveMessageBusClient] = None,
                 bot: Optional[MatrixBot] = None,
                 response_timeout: float = 30.0):
        self.bot = bot or MatrixBot(matrix_host, matrix_token, room_alias,
                                    bot_mention, greeting)
        self.client = client or AsyncHiveMessageBusClient(
            key=key,
            password=password,
            host=host,
            port=port,
            useragent=self.platform,
            identity=identity,
        )
        self.response_timeout = response_timeout
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._started = False

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self._started:
            return
        self._loop = asyncio.get_running_loop()
        self.bot.on_message = self._on_matrix_message
        LOG.info("== connected to Matrix")
        await self.client.connect(site_id="matrix")
        LOG.info("== connected to HiveMind")
        self._started = True

    async def stop(self) -> None:
        if not self._started:
            return
        try:
            await self.client.close()
        except Exception:
            LOG.exception("error closing HiveMind client")
        self._started = False

    # ------------------------------------------------------------------
    # Matrix -> HiveMind (callback runs on matrix-client thread)
    # ------------------------------------------------------------------

    def _on_matrix_message(self, event: dict) -> None:
        """Schedule the ask-and-reply round-trip onto the asyncio loop.

        The matrix-client library calls this on its own listener thread.
        We don't want to block it, so we schedule the async task and
        return immediately. The reply is sent back to the Matrix room
        from within the async task.
        """
        utt = event["content"]["body"]
        sender = event["sender"]
        LOG.debug(f"{sender}: {utt}")

        if not self.bot.bot_mention or self.bot.bot_mention not in utt:
            LOG.debug("bot not mentioned; ignoring")
            return

        # strip the @bot_mention prefix the user used to invoke us
        for mention in (f"@{self.bot.bot_mention}",
                        f"{self.bot.bot_mention}:",
                        self.bot.bot_mention):
            utt = utt.replace(mention, "")
        utt = utt.strip()
        if not utt:
            return

        if self._loop is None or self._loop.is_closed():
            LOG.warning("got matrix message before bridge started; dropping")
            return

        asyncio.run_coroutine_threadsafe(self._ask_and_reply(utt), self._loop)

    async def _ask_and_reply(self, utt: str) -> None:
        """Send the utterance to HiveMind, wait for the spoken reply,
        and send the result back to the Matrix room."""
        LOG.debug(f"asking hivemind: {utt}")
        # Send as a Mycroft message; wait for the speak reply that the
        # OVOS pipeline produces on the other end. AsyncHiveMessageBusClient
        # routes Mycroft messages through HivePayloadWaiter — it matches
        # by inner payload.msg_type.
        try:
            reply = await self.client.wait_for_response(
                Message("recognizer_loop:utterance", {"utterances": [utt]}),
                reply_type="speak",
                timeout=self.response_timeout,
            )
        except Exception:
            LOG.exception("HiveMind round-trip failed")
            reply = None

        if reply is not None:
            answer = reply.payload.data.get("utterance") or "Error"
        else:
            answer = "Error"
        LOG.info(f"HiveMind: {answer}")
        # send_text is sync (requests-based); fine to call from the loop.
        # If it ever becomes slow we can offload via loop.run_in_executor.
        try:
            self.bot.room.send_text(answer)
        except Exception:
            LOG.exception("failed to send reply to matrix room")
