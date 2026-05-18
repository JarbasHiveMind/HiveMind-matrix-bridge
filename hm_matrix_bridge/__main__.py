"""CLI entry point — asyncio main with signal-driven shutdown."""
from __future__ import annotations

import asyncio
import signal

import click
from hivemind_bus_client.identity import NodeIdentity
from ovos_utils.log import LOG

from hm_matrix_bridge import HiveMindMatrixBridge

LOG.set_level("DEBUG")


async def _amain(botname: str, matrixtoken: str, matrixhost: str,
                 room: str, key: str, password: str,
                 host: str, port: int) -> None:
    identity = NodeIdentity()
    password = password or identity.password
    key = key or identity.access_key
    host = host or identity.default_master

    if host and not host.startswith("ws://") and not host.startswith("wss://"):
        host = "ws://" + host

    if not key or not password or not host:
        raise RuntimeError(
            "NodeIdentity not set, please pass key/password/host or "
            "call 'hivemind-client set-identity'"
        )

    bridge = HiveMindMatrixBridge(
        matrix_host=matrixhost, matrix_token=matrixtoken,
        room_alias=room, bot_mention=botname,
        key=key, password=password, host=host, port=port,
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    await bridge.start()
    try:
        await stop_event.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await bridge.stop()


@click.group()
def main():
    pass


@main.command(help="connect a matrix chatroom to hivemind", name="run")
@click.option("--botname", help="thehivebot", type=str)
@click.option("--matrixtoken", help="", type=str)
@click.option("--matrixhost", help="https://matrix.org", default="https://matrix.org", type=str)
@click.option("--room", help="#hivemind-bots:matrix.org", type=str,
              default="#hivemind-bots:matrix.org")
@click.option("--key", help="HiveMind access key (default read from identity file)",
              type=str, default="")
@click.option("--password", help="HiveMind password (default read from identity file)",
              type=str, default="")
@click.option("--host", help="HiveMind host (default read from identity file)",
              type=str, default="")
@click.option("--port", help="HiveMind port number (default: 5678)",
              type=int, default=5678)
def launch_bot(botname: str, matrixtoken: str, matrixhost: str, room: str,
               key: str, password: str, host: str, port: int) -> None:
    asyncio.run(_amain(botname, matrixtoken, matrixhost, room,
                       key, password, host, port))


if __name__ == "__main__":
    main()
