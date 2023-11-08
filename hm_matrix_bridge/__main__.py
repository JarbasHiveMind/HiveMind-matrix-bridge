from hm_matrix_bridge import HiveMindMatrixBridge
from ovos_utils.log import LOG
from ovos_utils import wait_for_exit_signal
from time import sleep
import json

import click
from ovos_bus_client import Message
from ovos_utils.log import LOG
from ovos_utils.messagebus import FakeBus

from hivemind_bus_client.client import HiveMessageBusClient
from hivemind_bus_client.message import HiveMessage, HiveMessageType
from hivemind_bus_client.identity import NodeIdentity

LOG.set_level("DEBUG")


@click.group()
def main():
    pass

@main.command(help="connect a matrix chatroom to hivemind", name="run")
@click.option("--botname", help="thehivebot", type=str)
@click.option("--matrixtoken", help="", type=str)
@click.option("--matrixhost", help="https://matrix.org", default="https://matrix.org", type=str)
@click.option("--room", help="#hivemind-bots:matrix.org", type=str, default="#hivemind-bots:matrix.org")
@click.option("--key", help="HiveMind access key (default read from identity file)", type=str, default="")
@click.option("--password", help="HiveMind password (default read from identity file)", type=str, default="")
@click.option("--host", help="HiveMind host (default read from identity file)", type=str, default="")
@click.option("--port", help="HiveMind port number (default: 5678)", type=int, default=5678)
def launch_bot(botname:str, matrixtoken: str, matrixhost: str,  room: str,
             key: str, password: str, host: str, port: int):
    identity = NodeIdentity()
    password = password or identity.password
    key = key or identity.access_key
    host = host or identity.default_master
    siteid = "matrix"

    if not host.startswith("ws://") and not host.startswith("wss://"):
        host = "ws://" + host

    if not key or not password or not host:
        raise RuntimeError("NodeIdentity not set, please pass key/password/host or "
                           "call 'hivemind-client set-identity'")
    print(matrixhost, matrixtoken)
    node = HiveMindMatrixBridge(matrix_host=matrixhost, matrix_token=matrixtoken, room_alias=room, bot_mention=botname,
                                key=key, host=host, port=port, password=password)

    wait_for_exit_signal()


if __name__ == "__main__":
    main()
