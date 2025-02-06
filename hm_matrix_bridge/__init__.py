from hm_matrix_bridge.matrixapi import MatrixBot
from ovos_hivemind_solver import HiveMindSolver
from ovos_utils.log import LOG


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
        if self.bot.bot_mention in utt:
            LOG.debug("bot mentioned")
            utt = utt.replace(f"@{self.bot.bot_mention}", "") \
                .replace(f"{self.bot.bot_mention}:", "") \
                .replace(self.bot.bot_mention, "").strip()

            # TODO - lang detection plugin here
            LOG.debug(f"asking hivemind: {utt}")
            utterance = self.solver.get_spoken_answer(utt)
            LOG.info(f"HiveMind: {utterance}")
            self.bot.room.send_text(utterance or "Error")
        else:
            LOG.debug("bot not mentioned. ignoring")
