import logging
import sys

import click
import requests

from .. import settings

logger = logging.getLogger(__name__)


def main(cmd: str, target: str, env: str, opt: list[str]) -> None:
    if target not in ("prj"):
        msg = f"Unsupported target: {target}"
        logger.warning(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)

    try:
        url = f"{settings.chain_uri}/{cmd}/{target}"
        response = requests.post(url, data={"prj_name": settings.prj_name}, timeout=40)
        response.raise_for_status()
        msg = f"Project '{settings.prj_name}' added successfully: {response.status_code}"
        logger.info(msg)
        click.secho(msg, fg="green")
    except Exception as e:
        msg = f"Add request failed: {e}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    pass
