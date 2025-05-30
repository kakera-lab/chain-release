import logging
import sys

import click

from .. import settings
from . import get, modify

logger = logging.getLogger(__name__)


def main(cmd: str, target: str, env: str, opt: list[str]) -> None:
    try:
        for t in settings.info_targets:
            data = get.main("get", t, env, opt)
            modify.main("modify", t, env, [str(data)])
        msg = "All targets processed successfully."
        logger.info(msg)
        click.secho(msg, fg="green")
    except Exception as e:
        msg = f"Error during processing: {e}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    pass
