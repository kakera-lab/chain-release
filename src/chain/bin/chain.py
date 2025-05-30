import logging
import sys

import click

from .. import settings
from . import add, agent, get, init, modify, remove, reset, server, set, webui

# コマンドマッピング
COMMANDS = {
    "add": add.main,
    "remove": remove.main,
    "init": init.main,
    "get": get.main,
    "set": set.main,
    "modify": modify.main,
    "up": webui.main,
    "down": webui.main,
    "reset": reset.main,
}
logger = logging.getLogger(__name__)


@click.command()
@click.argument("cmd", type=click.Choice(tuple(COMMANDS.keys()), case_sensitive=False))
@click.argument("target", type=click.Choice(settings.targets, case_sensitive=False))
@click.option(
    "-e",
    "--env",
    default="docker",
    type=click.Choice(settings.env, case_sensitive=False),
    help="Execution environment (default: docker)",
)
@click.argument("opt", nargs=-1, type=click.UNPROCESSED)
def main(cmd: str, target: str, env: str, opt: list[str]) -> None:
    """Unified CLI entry point for chain cli."""
    try:
        if target == "server":
            server.main(cmd.lower(), target.lower(), env.lower(), list(opt))
        elif target == "agent":
            raise NotImplementedError
            # agent.main(cmd.lower(), target.lower(), env.lower(), list(opt))
        else:
            COMMANDS[cmd.lower()](cmd.lower(), target.lower(), env.lower(), list(opt))
    except Exception as e:
        logger.exception("Command execution failed")
        click.secho(f"Command execution failed: {e}", fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
