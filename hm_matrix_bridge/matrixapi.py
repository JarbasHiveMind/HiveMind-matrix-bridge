import threading
import time

from matrix_client.client import MatrixClient
from matrix_client.api import MatrixRequestError
from requests.exceptions import MissingSchema, InvalidSchema
from ovos_utils.log import LOG
from ovos_utils import wait_for_exit_signal


#: Seconds to leave between two sends. A homeserver rate limits a client
#: that talks faster than its own budget, and matrix_client answers a 429 by
#: sleeping the `retry_after_ms` the server names and trying again — on the
#: calling thread, with no bound on the number of retries. In this bridge the
#: caller is the listener thread, so every message the bridge waits out is a
#: message it is not receiving. Pacing is what keeps it out of that state.
DEFAULT_MIN_SEND_INTERVAL = 1.0

#: A send that takes longer than this was almost certainly held by the
#: server's own rate limit. matrix_client sleeps silently, so without this
#: the stall has no log line at all.
SLOW_SEND_WARNING_SECONDS = 2.0


class MatrixBot:
    def __init__(self, host, token, room_id_alias, bot_mention=None,
                 greeting=None, min_send_interval=None):
        self.client = None
        self.host = host
        self.bot_mention = bot_mention
        self.greeting = None
        self.min_send_interval = (DEFAULT_MIN_SEND_INTERVAL
                                  if min_send_interval is None
                                  else float(min_send_interval))
        self._send_lock = threading.Lock()
        self._last_send = 0.0
        self.connect_to_matrix(host, token)
        self.room = self.client.join_room(room_id_alias)
        self.room.add_listener(self.handle_message)
        self.client.start_listener_thread()
        self.on_connected()

    def send_text(self, text: str):
        """Send one message, no faster than ``min_send_interval``.

        Every send in this bridge goes through here so the interval is kept
        across all of them, not per caller. The lock serialises senders: two
        threads that both waited would otherwise send together and defeat the
        pacing they each observed.

        A send that the server holds anyway is reported. ``matrix_client``
        handles a 429 by sleeping ``retry_after_ms`` and retrying, without a
        log line and without a retry bound, so a rate-limited bridge would
        otherwise look like a bridge that has stopped.
        """
        with self._send_lock:
            wait = self.min_send_interval - (time.monotonic() - self._last_send)
            if wait > 0:
                LOG.debug(f"pacing the next matrix send by {wait:.2f}s")
                time.sleep(wait)
            started = time.monotonic()
            try:
                return self.room.send_text(text)
            finally:
                self._last_send = time.monotonic()
                held = self._last_send - started
                if held >= SLOW_SEND_WARNING_SECONDS:
                    LOG.warning(
                        f"the homeserver held this send for {held:.1f}s, "
                        "which is what its rate limit looks like. The bridge "
                        "receives nothing while it waits; raise "
                        "min_send_interval if this repeats")

    def on_connected(self):
        pass

    def on_joined(self, event):
        LOG.info("{0} joined".format(event['content']['displayname']))

        if self.greeting:
            self.send_text(self.greeting +
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