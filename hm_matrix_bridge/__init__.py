import json
import time

from matrix_client.api import MatrixRequestError

from hm_matrix_bridge.matrixapi import MatrixBot
from ovos_hivemind_solver import HiveMindSolver
from ovos_utils.log import LOG

# Matrix homeservers answer a send with HTTP 429 and a retry_after_ms once a
# client sends too fast (M_LIMIT_EXCEEDED). Retry that same send a bounded
# number of times, waiting the server's own retry_after_ms; if it never
# recovers, drop the message instead of raising out of the event handler.
MAX_SEND_ATTEMPTS = 3
DEFAULT_RATE_LIMIT_WAIT_MS = 1000  # fallback when the server omits retry_after_ms


class HiveMindMatrixBridge:
    platform = "HiveMindMatrixBridgeV0.2"

    def __init__(self, matrix_host, matrix_token, room_alias, bot_mention=None, greeting=None):
        self.bot = MatrixBot(matrix_host, matrix_token, room_alias, bot_mention, greeting)
        self.bot.on_message = self.handle_matrix_utterance
        LOG.info("== connected to Matrix")
        self.solver = HiveMindSolver(config={"site_id": "matrix",
                                             "useragent": self.platform,
                                             "autoconnect": True})
        LOG.info("== connected to HiveMind")

    def handle_matrix_utterance(self, event):
        utt = event['content']['body']
        LOG.debug(f"{event['sender']}: {utt}")
        mention = self.bot.bot_mention
        if mention and mention not in utt:
            LOG.debug("bot not mentioned. ignoring")
            return

        if mention:
            LOG.debug("bot mentioned")
            utt = utt.replace(f"@{mention}", "") \
                .replace(f"{mention}:", "") \
                .replace(mention, "").strip()

        # TODO - lang detection plugin here
        room_id = self.bot.room.room_id
        context = {"session": {"session_id": f"matrix-{room_id}"}}
        LOG.debug(f"asking hivemind: {utt}")
        utterance = self.solver.get_spoken_answer(utt, context=context)
        LOG.info(f"HiveMind: {utterance}")
        self._send_text(utterance or "Error")

    def _send_text(self, text):
        for attempt in range(1, MAX_SEND_ATTEMPTS + 1):
            try:
                self.bot.room.send_text(text)
                return
            except MatrixRequestError as e:
                if e.code != 429:
                    raise
                if attempt == MAX_SEND_ATTEMPTS:
                    LOG.error(f"Matrix rate limit exceeded after {MAX_SEND_ATTEMPTS} "
                              "attempts, dropping message")
                    return
                wait_ms = DEFAULT_RATE_LIMIT_WAIT_MS
                try:
                    wait_ms = json.loads(e.content)["retry_after_ms"]
                except (TypeError, ValueError, KeyError):
                    pass
                LOG.warning(f"Matrix rate-limited us (attempt {attempt}/{MAX_SEND_ATTEMPTS}), "
                            f"retrying in {wait_ms}ms")
                time.sleep(wait_ms / 1000)
