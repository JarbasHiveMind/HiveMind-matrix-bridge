from jarbas_hive_mind.slave.terminal import HiveMindTerminalProtocol, HiveMindTerminal
from ovos_utils.log import LOG
from ovos_utils import create_daemon
from ovos_utils.messagebus import Message
from time import sleep
from matrix_bridge.matrixapi import MatrixBot


class JarbasMatrixBridgeProtocol(HiveMindTerminalProtocol):
    """"""


class JarbasMatrixBridge(HiveMindTerminal):
    protocol = JarbasMatrixBridgeProtocol
    platform = "JarbasMatrixBridgeV0.1"

    def __init__(self,host, token, room_alias, bot_mention=None,
                 greeting=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = MatrixBot(host, token, room_alias, bot_mention, greeting)
        self.bot.on_message = self.handle_matrix_utterance

    def handle_matrix_utterance(self, event):
        utt = event['content']['body']
        LOG.info("{0}: {1}".format(event['sender'], utt))
        mention = "@" + self.bot_mention
        if mention in utt:
            utt = utt.replace(mention, "")
        msg = {"data": {"utterances": [utt],
                        "lang": "en-us"},
               "type": "recognizer_loop:utterance",
               "context": {"source": self.client.peer,
                           "destination": "hive_mind",
                           "platform": self.platform}}
        self.send_to_hivemind_bus(msg)

    # terminal
    def speak(self, utterance):
        LOG.info("Mycroft:", utterance)
        self.bot.room.send_text(utterance)

    # parsed protocol messages
    def handle_incoming_mycroft(self, message):
        assert isinstance(message, Message)
        if message.msg_type == "speak":
            utterance = message.data["utterance"]
            self.speak(utterance)
        elif message.msg_type == "hive.complete_intent_failure":
            LOG.error("complete intent failure")
            self.speak('I don\'t know how to answer that')
        else:
            LOG.info(message.data)

