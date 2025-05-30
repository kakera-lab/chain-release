import logging
import subprocess
import sys

import click
from tomlkit import dumps, table

from .. import settings

logger = logging.getLogger(__name__)


def modify_info(target: str, info: str) -> None:
    try:
        # 安全に project, chain を初期化
        if "project" not in settings.pyproject:
            settings.pyproject["project"] = table()
        if "chain" not in settings.pyproject["project"]:
            settings.pyproject["project"]["chain"] = table()
        settings.pyproject["project"]["chain"][target] = info
        with open(settings.pyproject_path, "w") as f:
            f.write(dumps(settings.pyproject))
    except Exception as e:
        msg = f"Failed to write pyproject.toml: {e}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)


def modify_dvc(info: str) -> None:
    try:
        cmd = ["dvc", "remote", "add", "--force", settings.prj_name, info]
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
    if target not in settings.info_targets:
        msg = f"Unsupported target: {target}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)

    if not opt or (len(opt) == 1 and opt[0] == ""):
        msg = "No option provided"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)

    modify_info(target, opt[0])
    if target == "dvc" and settings.dvc_path.exists():
        modify_dvc(opt[0])
    msg = f"Updated target '{target}' with option '{opt[0]}' successfully."
    logger.info(msg)
    click.secho(msg, fg="green")


if __name__ == "__main__":
    pass
