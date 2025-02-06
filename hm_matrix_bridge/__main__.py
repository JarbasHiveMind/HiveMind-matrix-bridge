import click
from hm_matrix_bridge import HiveMindMatrixBridge
from ovos_utils import wait_for_exit_signal
from ovos_utils.log import LOG

LOG.set_level("DEBUG")


@click.group()
def main():
    pass


@main.command(help="connect a matrix chatroom to hivemind", name="run")
@click.option("--botname", help="thehivebot", type=str)
@click.option("--matrixtoken", help="", type=str)
@click.option("--matrixhost", help="https://matrix.org", default="https://matrix.org", type=str)
@click.option("--room", help="#hivemind-bots:matrix.org", type=str, default="#hivemind-bots:matrix.org")
def launch_bot(botname: str, matrixtoken: str, matrixhost: str, room: str):
    print(matrixhost, matrixtoken)
    node = HiveMindMatrixBridge(matrix_host=matrixhost, matrix_token=matrixtoken,
                                room_alias=room, bot_mention=botname)

    wait_for_exit_signal()


if __name__ == "__main__":
    main()
