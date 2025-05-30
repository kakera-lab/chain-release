import logging
import subprocess
import sys

import click
from tomlkit import dumps

from .. import settings

logger = logging.getLogger(__name__)


def reset_info() -> None:
    try:
        if "chain" in settings.pyproject["project"]:
            del settings.pyproject["project"]["chain"]
        with open(settings.pyproject_path, "w") as f:
            f.write(dumps(settings.pyproject))
    except Exception as e:
        msg = f"Failed to reset pyproject.toml: {e}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)


def reset_dvc() -> None:
    try:
        cmd = ["dvc", "remote", "remove", settings.prj_name]
        subprocess.run(  # noqa
            cmd,
            cwd=settings.dvc_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            check=True,
        )
    except subprocess.CalledProcessError as e:
        msg = f"DVC command failed: {e}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)


def main(cmd: str, target: str, env: str, opt: list[str]) -> None:
    if target not in ("prj"):
        msg = f"Unsupported target: {target}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)

    reset_info()
    reset_dvc()
    msg = f"Reset project successfully."
    logger.info(msg)
    click.secho(msg, fg="green")


if __name__ == "__main__":
    pass
