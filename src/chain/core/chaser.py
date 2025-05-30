import logging
import queue
import threading
import time
from collections.abc import Generator
from urllib.parse import urlparse

import grpc
import mlflow
import numpy as np
import requests
from mlflow.tracking import MlflowClient

from .. import settings
from ..chaser_server import metric_pb2, metric_pb2_grpc

logger = logging.getLogger(__name__)

run_context = threading.local()


class ChaserActiveRun:
    def __init__(self, run: mlflow.ActiveRun):
        self.run = run

        self.prj_id = settings.prj_id
        self.experiment_id = self.run.info.experiment_id
        self.experiment_name = MlflowClient().get_experiment(self.experiment_id).name
        self.parent = self.run.data.tags.get("mlflow.parentRunId")
        self.run_name = self.run.info.run_name
        self.run_uuid = self.run.info.run_uuid

        self.batch: list[metric_pb2.MetricRequest] = []  # バッチバッファ
        self.batch_size = 100  # バッチ送信単位
        self.flush_interval = 1.0  # 秒
        self.last_flush = time.time()

        self.queue = queue.Queue()
        self.stop_event = threading.Event()

    def setup(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.channel = grpc.insecure_channel(f"{self.host}:{self.port}")
        self.stub = metric_pb2_grpc.MetricServiceStub(self.channel)
        self.worker_thread = threading.Thread(target=self.worker, daemon=True)
        self.worker_thread.start()

    def log_metric(self, key: str, value: np.ndarray) -> None:
        """メトリクスを送信キューに登録"""
        self.queue.put((key, value))

    def worker(self):
        while not self.stop_event.is_set():
            try:
                key, value = self.queue.get(timeout=0.2)
                self.batch.append(
                    metric_pb2.MetricRequest(
                        prj_id=self.prj_id,
                        experiment_id=self.experiment_id,
                        run_uuid=self.run_uuid,
                        key=key,
                        dim=len(value),
                        value=value.astype(np.float32).tobytes(),
                    )
                )

                now = time.time()
                if len(self.batch) >= self.batch_size or (now - self.last_flush) >= self.flush_interval:
                    self.send_batch()
                    self.last_flush = now

            except queue.Empty:
                now = time.time()
                if self.batch and (now - self.last_flush) >= self.flush_interval:
                    self.send_batch()
                    self.last_flush = now

    def send_batch(self) -> None:
        try:

            def generator() -> Generator[metric_pb2.MetricRequest]:
                for req in self.batch:
                    yield req

            self.stub.SendMetrics(generator())  # ストリーミング送信
            self.batch.clear()
        except grpc.RpcError as e:
            logger.warning(f"[AsyncBatchLogger] Batch send failed: {e.details()}")

    def stop(self) -> None:
        """バックグラウンドスレッドの停止"""
        self.send_batch()
        self.stop_event.set()
        self.worker_thread.join()


def get_run_stack():
    if not hasattr(run_context, "stack"):
        run_context.stack = []
    return run_context.stack


def start_run() -> None:
    if (mlflow_run := mlflow.active_run()) is None:
        raise RuntimeError
    run = ChaserActiveRun(mlflow_run)

    url = f"{settings.chaser_uri}/start_run/{settings.prj_id}/{run.experiment_id}/{run.run_uuid}"
    data = {"experiment_name": run.experiment_name, "parent": run.parent, "run_name": run.run_name}
    response = requests.post(url, data=data, timeout=40)
    response.raise_for_status()

    url = f"{settings.chaser_uri}/grpc"
    response = requests.get(url, timeout=40)
    response.raise_for_status()
    port_info = response.json()  # or res.text if it's just a number
    port = port_info["port"] if isinstance(port_info, dict) else int(port_info)

    uri = settings.chaser_uri.rstrip("/")
    parsed = urlparse(uri)

    run.setup(parsed.hostname, port)

    run_stack = get_run_stack()
    run_stack.append(run)


def end_run() -> None:
    run_stack = get_run_stack()
    run = run_stack.pop()
    run.stop()

    url = f"{configs.chaser_uri}/end_run/{configs.prj_id}/{run.experiment_id}/{run.run_uuid}"
    response = requests.post(url, timeout=40)
    response.raise_for_status()


def log_metric(key: str, value: np.ndarray) -> None:
    run_stack = get_run_stack()
    run = run_stack[-1]
    run.log_metric(key, value)


if __name__ == "__main__":
    pass
