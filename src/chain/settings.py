import logging
import os
import sys
from pathlib import Path

import click
import optuna
from dotenv import load_dotenv
from tomlkit import parse

# optunaのlogを流す
optuna.logging.disable_default_handler()
optuna.logging.enable_propagation()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# command
webui = ("prj", "mlflow", "optuna", "chaser")
info_targets = webui + ("dvc",)
targets = info_targets + ("server", "agent")
# local : chain + storage on docker
# docker: only chain on docker
# k8s: chain on k8s
env = ("local", "docker", "k8s")
# env file
env_path = Path("src/.env")
if not env_path.exists():
    click.secho(f"[ERROR] .env file not found: {env_path}", fg="red", err=True)
    sys.exit(1)

load_dotenv(env_path)
# dvc
dvc_path = Path(".dvc")
# chain server
compose_env_file = [env_path]
compose_files = [Path(__file__).parent / "server/docker/docker-compose.yaml"]
# chain uri
chain_uri = os.getenv("CHAIN_URI")
if chain_uri is None:
    msg = "[ERROR] CHAIN_URI is not set in the environment."
    logger.info(msg)
    click.secho(msg, fg="red", err=True)
    sys.exit(1)


# pyproject
pyproject_path = Path("pyproject.toml")
if not pyproject_path.exists():
    raise FileExistsError("error")
try:
    with open(pyproject_path, encoding="utf-8") as f:
        pyproject = parse(f.read())
except Exception as e:
    msg = f"[ERROR] Failed to load pyproject.toml: {e}"
    logger.info(msg)
    click.secho(msg, fg="red", err=True)
    sys.exit(1)


prj_name = pyproject.get("project", {}).get("name", "")
if prj_name == "":
    msg = "Project Name is missing in pyproject.toml"
    logger.error(msg)
    click.secho(msg, fg="red", err=True)
    sys.exit(1)

# warning
prj_id = pyproject.get("project", {}).get("chain", {}).get("prj", "")
if prj_id == "":
    msg = "Project ID is missing in pyproject.toml"
    logger.warning(msg)
    click.secho(msg, fg="yellow", err=True)

chaser_uri = pyproject.get("project", {}).get("chain", {}).get("chaser", "")
if chaser_uri == "":
    msg = "Chaser URI is missing in pyproject.toml"
    logger.warning(msg)
    click.secho(msg, fg="yellow", err=True)

mlflow_uri = pyproject.get("project", {}).get("chain", {}).get("mlflow", "")
if mlflow_uri == "":
    msg = "MLFlow URI is missing in pyproject.toml"
    logger.warning(msg)
    click.secho(msg, fg="yellow", err=True)

if __name__ == "__main__":
    pass
