import logging
import sys

import click
import requests

from .. import settings

logger = logging.getLogger(__name__)


def main(cmd: str, target: str, env: str, opt: list[str]) -> None:
    if target not in settings.webui:
        msg = f"Unsupported target: {target}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)

    prj_id = settings.pyproject.get("project", {}).get("chain", {}).get("prj", "")
    if prj_id == "":
        msg = "Project ID is missing in pyproject.toml"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)

    try:
        url = f"{settings.chain_uri}/{cmd}/{target}/{prj_id}"
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        msg = f"WebUI '{target}' stop successfully (status {response.status_code})"
        logger.info(msg)
        click.secho(msg, fg="green")
    except requests.RequestException as e:
        msg = f"WebUI stop failed: {e}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    pass
