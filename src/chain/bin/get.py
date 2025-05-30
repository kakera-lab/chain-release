import logging
import sys
from typing import Any

import click
import requests

from .. import settings

logger = logging.getLogger(__name__)


def main(cmd: str, target: str, env: str, opt: list[str]) -> Any:
    if target not in settings.info_targets:
        msg = f"Unsupported target: {target}"
        logger.warning(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)

    try:
        if target == "prj":
            identifier = settings.prj_name
        else:
            prj_id = settings.pyproject.get("project", {}).get("chain", {}).get("prj", "")
            if prj_id == "":
                raise ValueError("Project ID is missing in pyproject.toml")
            identifier = prj_id
        url = f"{settings.chain_uri}/{cmd}/{target}/{identifier}"
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        msg = f"Info '{target}' request succeeded '{response.text}': {response.status_code}"
        logger.info(msg)
        click.secho(msg, fg="green")
        return response.text
    except Exception as e:
        msg = f"Info request failed: {e}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    pass
