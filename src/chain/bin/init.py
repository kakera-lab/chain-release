import logging
import sys

import click

from . import add, set

logger = logging.getLogger(__name__)


def main(cmd: str, target: str, env: str, opt: list[str]) -> None:
    if target not in ("prj"):
        msg = f"Unsupported target: {target}"
        logger.warning(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)

    add.main("add", target, env, opt)  # 内部で例外
    set.main("set", target, env, opt)  # 内部で例外


if __name__ == "__main__":
    pass
