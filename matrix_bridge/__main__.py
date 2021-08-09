from matrix_bridge import JarbasMatrixBridge
from jarbas_hive_mind import HiveMindConnection
from jarbas_hive_mind.discovery import LocalDiscovery
from ovos_utils.log import LOG
from time import sleep


def connect_to_hivemind(matrix_host, token, room,
                        alias=None, greeting=None,
                        host="ws://127.0.0.1",
                        port=5678, name="JarbasMatrixBridge",
                        access_key="erpDerPerrDurHUr",
                        crypto_key=None):
    con = HiveMindConnection(host, port)

    terminal = JarbasMatrixBridge(matrix_host, token, room, alias, greeting,
        crypto_key=crypto_key, headers=con.get_headers(name, access_key))

    con.connect(terminal)



def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--token",
                        help="access token for bot account")
    parser.add_argument("--bot_alias",
                        help="only answer messages that start with @{bot_alias}",
                        default=None)
    parser.add_argument("--greeting",
                        help="when a user joins say {greeting}",
                        default=None)
    parser.add_argument("--room", help="room_alias eg, #openvoiceos-bots:matrix.org")
    parser.add_argument("--matrix_host", help="matrix server",
                        default="https://matrix.org")
    parser.add_argument("--access_key", help="access key",
                        default="erpDerPerrDurHUr")
    parser.add_argument("--crypto_key", help="payload encryption key",
                        default=None)
    parser.add_argument("--name", help="human readable device name",
                        default="JarbasMatrixBridge")
    parser.add_argument("--host", default="ws://127.0.0.1",
                        help="HiveMind host")
    parser.add_argument("--port", help="HiveMind port number", default=5678)

    args = parser.parse_args()
    # Direct Connection
    connect_to_hivemind(args.matrix_host, args.token, args.room,
                        args.bot_alias, args.greeting,
                        args.host, int(args.port),
                        args.name, args.access_key,
                        args.crypto_key)


if __name__ == '__main__':
    main()
