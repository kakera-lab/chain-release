import logging
import os
import platform
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import click
import daemon
from daemon import pidfile

from .. import settings

logger = logging.getLogger(__name__)


def send_notification(title: str, message: str) -> None:
    system = platform.system()
    if system == "Darwin":
        cmd = ["osascript", "-e", f'display notification "{message}" with title "{title}"']
    elif system == "Linux":
        cmd = ["notify-send", title, message]
    else:
        print(f"[通知] {title}: {message} (対応外OS)")
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", check=True)  # noqa


def agent() -> None:
    while True:
        send_notification("完了", "学習処理が終了しました")
        time.sleep(10)


def start_agent() -> None:
    if PID_FILE.exists():
        print("Agent is already running.")
        return
    with daemon.DaemonContext(
        pidfile=pidfile.TimeoutPIDLockFile(str(PID_FILE)),
        stdout=sys.stdout,
        stderr=sys.stderr,
    ):
        agent()


def stop_agent() -> None:
    if not PID_FILE.exists():
        print("Agent is not running.")
        return
    with open(PID_FILE) as f:
        pid = int(f.read())
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Agent (PID {pid}) stopped.")
    except ProcessLookupError:
        print("Agent process not found.")
    PID_FILE.unlink()


def main(cmd: str, target: str, env: str, opt: list[str]) -> None:
    if target not in ("agent"):
        msg = f"Unsupported target: {target}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)

    if cmd == "up":
        start_agent()
    elif cmd == "down":
        stop_agent()
    else:
        raise NotImplementedError


if __name__ == "__main__":
    pass
