import logging
import os
import time

import docker
from docker.types import LogConfig

logger = logging.getLogger(__name__)

client = docker.from_env()


def stop_container_by_name(container_name: str) -> None:
    try:
        container = client.containers.get(container_name)
        if container.status == "running":
            container.stop()
            logger.info(f"Container '{container_name}' has been stopped.")
        else:
            logger.info(f"Container '{container_name}' is already stopped.")
        container.remove(force=True)
        logger.info(f"Container '{container_name}' has been removed.")
    except docker.errors.NotFound:
        logger.error(f"Container '{container_name}' was not found.")
    except docker.errors.APIError as e:
        logger.error(f"An error occurred while stopping or removing container '{container_name}': {e}")


def start_mlflow(prj_id: str, port: int, backend_uri: str, s3_path: str) -> None:
    try:
        container = client.containers.get(f"mlflow-{prj_id}")
        if container.status != "running":
            container.start()
            logger.info(f"Started existing container chaser-{prj_id}.")
        else:
            logger.info(f"Container chaser-{prj_id} is already running.")
    except docker.errors.NotFound:
        client.images.build(path="/mlflow", tag="mlflow:3.12")
        logger.info(f"Container mlflow-{prj_id} not found. Building image and running container.")
        client.containers.run(
            "mlflow:3.12",
            detach=True,
            name=f"mlflow-{prj_id}",
            ports={"5000/tcp": port},
            labels={"auto-stop": "true", "auto-remove": "true"},
            environment={
                "PRJ_ID": prj_id,
                "MLFLOW_S3_ENDPOINT_URL": os.getenv("S3_ENDPOINT_URL"),
                "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
                "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
                "MLFLOW_BACKEND_STORE_URI": backend_uri,
                "MLFLOW_ARTIFACTS_DESTINATION": s3_path,
                "MLFLOW_ENABLE_PROXY_MULTIPART_UPLOAD": True,
                "MLFLOW_ENABLE_ARTIFACTS_SERVER": True,
                "MLFLOW_HOST": "0.0.0.0",
                "MLFLOW_PORT": 5000,
                "MLFLOW_WORKERS": 1,
            },
            network="chain",
            log_config=LogConfig(type=LogConfig.types.JSON),
        )
        logger.info(f"Started new container mlflow-{prj_id}.")
        time.sleep(5)
    except Exception as e:
        logger.error(f"Error in start_mlflow for {prj_id}: {e}", exc_info=True)
        raise


def start_optuna(prj_id: str, port: int, backend_uri: str, s3_path: str, grpc: int) -> None:
    try:
        container = client.containers.get(f"optuna-{prj_id}")
        if container.status != "running":
            container.start()
            logger.info(f"Started existing container optuna-{prj_id}.")
        else:
            logger.info(f"Container optuna-{prj_id} is already running.")
    except docker.errors.NotFound:
        client.images.build(path="/optuna", tag="optuna:3.12")
        logger.info(f"Container optuna-{prj_id} not found. Building image and running container.")
        client.containers.run(
            "optuna:3.12",
            detach=True,
            name=f"optuna-{prj_id}",
            ports={"8000/tcp": port, "13000": grpc},
            labels={"auto-stop": "true", "auto-remove": "true"},
            environment={
                "PRJ_ID": prj_id,
                "S3_ENDPOINT_URL": os.getenv("S3_ENDPOINT_URL"),
                "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
                "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
                "GRPC_PORT": grpc,
                "DB_STORAGE": backend_uri,
                "S3_PATH": s3_path,
            },
            network="chain",
            log_config=LogConfig(type=LogConfig.types.JSON),
        )
        logger.info(f"Started new container optuna-{prj_id}.")
        time.sleep(5)
    except Exception as e:
        logger.error(f"Error in start_optuna for {prj_id}: {e}", exc_info=True)
        raise


def start_chaser(prj_id: str, port: int, backend_uri: str, s3_path: str, grpc: int) -> None:
    try:
        container = client.containers.get(f"chaser-{prj_id}")
        if container.status != "running":
            container.start()
            logger.info(f"Started existing container chaser-{prj_id}.")
        else:
            logger.info(f"Container chaser-{prj_id} is already running.")
    except docker.errors.NotFound:
        client.images.build(path="/chaser", tag="chaser:3.12")
        logger.info(f"Container chaser-{prj_id} not found. Building image and running container.")
        client.containers.run(
            "chaser:3.12",
            detach=True,
            name=f"chaser-{prj_id}",
            ports={"8050/tcp": port, "14000": grpc},
            labels={"auto-stop": "true", "auto-remove": "true"},
            environment={
                "PRJ_ID": prj_id,
                "S3_ENDPOINT_URL": os.getenv("S3_ENDPOINT_URL"),
                "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
                "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
                "GRPC_PORT": grpc,
                "DB_STORAGE": backend_uri,
                "S3_PATH": s3_path,
            },
            network="chain",
            log_config=LogConfig(type=LogConfig.types.JSON),
        )
        logger.info(f"Started new container chaser-{prj_id}.")
        time.sleep(5)
    except Exception as e:
        logger.error(f"Error in start_chaser for {prj_id}: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    pass
