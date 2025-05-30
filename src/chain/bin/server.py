import logging
import sys

import click
from python_on_whales import DockerClient

from .. import settings

logger = logging.getLogger(__name__)
docker = DockerClient(compose_files=settings.compose_files, compose_env_files=settings.compose_env_file)


def start_chain_server(local: bool = False) -> None:
    try:
        docker.compose.build()
        if local:
            docker.compose.up(detach=True)
        else:
            docker.compose.up(services="chain", detach=True)
        msg = "Chain Server started."
        logger.info(msg)
        click.secho(msg, fg="green")
    except Exception as e:
        msg = f"Failed to start Chain Server: {e}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)


def stop_chain_server() -> None:
    try:
        docker.compose.down()
        msg = "Chain Server stopped."
        logger.info(msg)
        click.secho(msg, fg="green")
    except Exception as e:
        msg = f"Failed to stop Chain Server: {e}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)


def cleanup_auto_remove_containers() -> None:
    try:
        containers = docker.container.list(all=True, filters={"label": "auto-remove=true"})
        logger.debug(f"Found {len(containers)} containers with auto-remove=true")
        for container in containers:
            click.secho(f"Stopping and removing container: {container.name} ({container.id})", fg="green")
            try:
                if container.state.status == "running":
                    container.stop()
                container.remove(force=True)
            except Exception as e:
                msg = f"Error stopping/removing container {container.name}: {e}"
                logger.error(msg)
                click.secho(msg, fg="red", err=True)
    except Exception as e:
        msg = f"Error listing containers: {e}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)


def main(cmd: str, target: str, env: str, opt: list[str]) -> None:
    if target not in ("server"):
        msg = f"Unsupported target: {target}"
        logger.error(msg)
        click.secho(msg, fg="red", err=True)
        sys.exit(1)

    if cmd == "up":
        if env == "local":
            start_chain_server(True)
        else:
            start_chain_server()
    elif cmd == "down":
        stop_chain_server()
        cleanup_auto_remove_containers()
    else:
        raise NotImplementedError


if __name__ == "__main__":
    pass
