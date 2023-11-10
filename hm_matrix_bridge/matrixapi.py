from matrix_client.client import MatrixClient
from matrix_client.api import MatrixRequestError
from requests.exceptions import MissingSchema, InvalidSchema
from ovos_utils.log import LOG
from ovos_utils import wait_for_exit_signal


class MatrixBot:
    def __init__(self, host, token, room_id_alias, bot_mention=None,
                 greeting=None):
        self.client = None
        self.host = host
        self.bot_mention = bot_mention
        self.greeting = None
        self.connect_to_matrix(host, token)
        self.room = self.client.join_room(room_id_alias)
        self.room.add_listener(self.handle_message)
        self.client.start_listener_thread()
        self.on_connected()

    def on_connected(self):
        pass

    def on_joined(self, event):
        LOG.info("{0} joined".format(event['content']['displayname']))

        if self.greeting:
            self.room.send_text(self.greeting +
                                f" @{event['content']['displayname']}")

    def on_message(self, event):
        LOG.info("{0}: {1}".format(event['sender'], event['content']['body']))

    @property
    def user_id(self):
        if self.client:
            return self.client.user_id
        return None

    def connect_to_matrix(self, host, token):
        """run the example."""

        try:
            LOG.info('token login')
            self.client = MatrixClient(host, token=token)
        except MatrixRequestError as e:
            LOG.exception(e)
            if e.code == 403:
                LOG.error("Bad username or password")
                exit(2)
            elif e.code == 401:
                LOG.error("Bad username or token")
                exit(3)
            else:
                LOG.error("Verify server details.")
                exit(4)
        except MissingSchema as e:
            LOG.exception(e)
            LOG.error("Bad formatting of URL.")
            exit(5)
        except InvalidSchema as e:
            LOG.exception(e)
            LOG.error("Invalid URL schema")
            exit(6)

    def handle_message(self, room, event):
        if event['type'] == "m.room.member":
            if event["content"]['membership'] == "join":
                self.on_joined(event)
        elif event['type'] == "m.room.message":
            if event["content"].get('m.relates_to', {}).get('m.in_reply_to', {}):
                pass # TODO - get text of original message
            if event['content']['msgtype'] == "m.text":
                if self.bot_mention:
                    if self.bot_mention in event['content']['body']:
                        self.on_message(event)
                elif event['sender'] != self.user_id:
                    self.on_message(event)


def main():
    url = "https://matrix.org"
    room_id_alias = "#hivemind-bots:matrix.org"
    tok = "xxxx"
    client = MatrixBot(url, tok, room_id_alias, bot_mention="thehivebot")
    wait_for_exit_signal()


if __name__ == "__main__":
    main()