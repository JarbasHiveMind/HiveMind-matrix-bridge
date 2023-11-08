from ovos_utils.log import LOG
from ovos_utils import create_daemon
from ovos_utils.messagebus import Message
from time import sleep
from hm_matrix_bridge.matrixapi import MatrixBot
from hivemind_bus_client.client import HiveMessageBusClient
from hivemind_bus_client.message import HiveMessage, HiveMessageType
from hivemind_bus_client.identity import NodeIdentity
from ovos_utils.messagebus import FakeBus


class HiveMindMatrixBridge(HiveMessageBusClient):
    platform = "HiveMindMatrixBridgeV0.1"

    def __init__(self, matrix_host, matrix_token, room_alias, bot_mention=None,
                 greeting=None, *args, **kwargs):
        self.bot = MatrixBot(matrix_host, matrix_token, room_alias, bot_mention, greeting)
        self.bot.on_message = self.handle_matrix_utterance
        LOG.info("== connected to Matrix")
        super().__init__(*args, **kwargs)
        self.connect(FakeBus(), site_id="matrix")
        self.on_mycroft("speak", self.handle_incoming_mycroft)
        LOG.info("== connected to HiveMind")

    def handle_matrix_utterance(self, event):
        utt = event['content']['body']
        LOG.debug(f"{event['sender']}: {utt}")
        if self.bot.bot_mention in utt:
            LOG.debug("bot mentioned")
            utt = utt.replace(f"@{self.bot.bot_mention}", "")\
                .replace(f"{self.bot.bot_mention}:", "")\
                .replace(self.bot.bot_mention, "").strip()

            # TODO - lang detection plugin here
            LOG.debug(f"asking hivemind: {utt}")
            self.emit_mycroft(
                Message("recognizer_loop:utterance",
                        {"utterances": [utt]},
                        {"destination": "skills"})
            )
        else:
            LOG.debug("bot not mentioned. ignoring")

    def handle_incoming_mycroft(self, message):
        utterance = message.data["utterance"]
        LOG.info(f"HiveMind: {utterance}")
        self.bot.room.send_text(utterance)
