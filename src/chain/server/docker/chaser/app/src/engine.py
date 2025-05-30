import json
import logging
import os
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import boto3
import numpy as np
import plotly.graph_objs as go
from boto3.s3.transfer import TransferConfig
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .orm import Base, ExperimentORM, RunORM, TagORM

TRANSFER_CONFIG = TransferConfig(multipart_threshold=8 * 1024 * 1024, max_concurrency=10)
DATA_DIR = Path("/data/experiments")

logger = logging.getLogger(__name__)

engine = create_engine(os.getenv("DB_STORAGE"))
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


##########################################
# 追加系
##########################################
def add_experiment(id: int, name: str) -> ExperimentORM:
    with get_session() as session:
        existing = session.query(ExperimentORM).filter((ExperimentORM.id == id) | (ExperimentORM.name == name)).first()
        if not existing:
            experiment = ExperimentORM(id=id, name=name)
            session.add(experiment)
            session.commit()
            session.refresh(experiment)
            return experiment
        return existing


def add_run(id: str, name: str, experiment_id: int) -> RunORM:
    with get_session() as session:
        existing = session.query(RunORM).filter(RunORM.id == id).first()
        if not existing:
            run = RunORM(id=id, name=name, experiment_id=experiment_id)
            session.add(run)
            session.commit()
            session.refresh(run)
            return run
        return existing


def add_tag(run_id: int, key: str, value: str) -> TagORM:
    with get_session() as session:
        existing = session.query(TagORM).filter((TagORM.run_id == run_id) & (TagORM.key == key)).first()
        if not existing:
            tag = TagORM(run_id=run_id, key=key, value=value)
            session.add(tag)
            session.commit()
            session.refresh(tag)
            return tag
        return existing


##########################################
# 取得系
##########################################
def get_experiments() -> list:
    with get_session() as session:
        return session.query(ExperimentORM).order_by(ExperimentORM.date.desc()).all()


def get_runs_by_experiment(experiment_id: int) -> list:
    with get_session() as session:
        return session.query(RunORM).filter(RunORM.experiment_id == experiment_id).order_by(RunORM.date.desc()).all()


def get_plot_state(run_id: str) -> Any:
    with get_session() as session:
        run = session.query(RunORM).filter(RunORM.id == run_id).first()
        return json.loads(run.state) if run is not None else {}


def get_tag(run_id: str, key: str = "mlflow.parentRunId") -> str | None:
    with get_session() as session:
        tag = session.query(TagORM).filter_by(run_id=run_id, key=key).first()
        return tag.value if tag else None


def get_dim(experiment_id: int, run_id: str, metric: str) -> int:
    meta_path = DATA_DIR / str(experiment_id) / run_id / f"{metric}.meta"
    if meta_path.exists():
        with open(meta_path) as f:
            return int(f.read().strip())
    return 1


def get_data(experiment_id: int, run_id: str, metric: str) -> np.ndarray:
    file_path = DATA_DIR / str(experiment_id) / run_id / f"{metric}.bin"
    if file_path.exists():
        with open(file_path) as f:
            return np.fromfile(file_path, dtype=np.float32)
    return np.array([])


def list_experiments() -> list:
    with get_session() as session:
        return [
            {"name": exp.name, "id": exp.id}
            for exp in session.query(ExperimentORM).order_by(ExperimentORM.date.desc()).all()
        ]


def list_runs(experiment_id: str, tag_name: str = "mlflow.parentRunId") -> list:
    with get_session() as session:
        return [
            {"name": run.name, "id": run.id, "parent": tag.value if tag else None}
            for run, tag in (
                session.query(RunORM, TagORM)
                .outerjoin(
                    TagORM,
                    (RunORM.id == TagORM.run_id) & (TagORM.key == tag_name),
                )
                .filter(RunORM.experiment_id == experiment_id)
                .order_by(RunORM.date.desc())
                .all()
            )
        ]


def list_runs_hierarchy(experiment_id: str) -> dict:
    hierarchy = defaultdict(list)
    for run in list_runs(experiment_id):
        parent_id = run["parent"]
        hierarchy[parent_id].append(run)
    return hierarchy


def list_metrics(experiment_id: int, run_id: str) -> list:
    run_path = DATA_DIR / str(experiment_id) / run_id
    pull_all_from_s3(run_path, experiment_id, run_id)
    if not run_path.exists():
        return []
    return sorted([p.stem for p in run_path.glob("*.bin")])


##########################################
# 更新系
##########################################
def update_plot_state(run_id: str, state: dict) -> None:
    with get_session() as session:
        run = session.query(RunORM).filter(RunORM.id == run_id).first()
        plot_states = json.loads(run.state)
        plot_states[state["plot_id"]] = state
        run.state = json.dumps(plot_states)
        session.commit()


def delete_plot_state(run_id: str, plot_id: str) -> None:
    with get_session() as session:
        run = session.query(RunORM).filter(RunORM.id == run_id).first()
        plot_states = json.loads(run.state)
        if plot_id in plot_states:
            plot_states.pop(plot_id)
            run.state = json.dumps(plot_states)
            session.commit()


##########################################
# S3系
##########################################
def push_all_to_s3(dir_path: Path) -> None:
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            s3.upload_file(
                Filename=str(file_path),
                Bucket=os.getenv("PRJ_ID"),
                Key=f"chain/{str(file_path.relative_to('/data'))}",
                Config=TRANSFER_CONFIG,
            )


def pull_all_from_s3(dir_path: Path, exp_id: int, run_id: str) -> None:
    if not dir_path.exists():
        bucket = os.getenv("PRJ_ID")
        prefix = f"chain/experiments/{exp_id}/{run_id}/"
        relative_root = Path(prefix)
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        contents = response.get("Contents", [])
        if not contents:
            return
        for obj in contents:
            s3_key = obj["Key"]
            relative_path = Path(s3_key).relative_to(relative_root)
            local_path = dir_path / relative_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(Bucket=bucket, Key=s3_key, Filename=str(local_path))


##########################################
# そのほか
##########################################
def check_prj_id(prj_id: str) -> None:
    assert os.getenv("PRJ_ID") == prj_id, "id error"


##########################################
# 図関連
##########################################
def save_plot_state(experiment_id: int, run_id: str, plot_id: str, metric: str = "", dim: int = 1):
    if metric == "":
        metrics_list = list_metrics(experiment_id, run_id)
        if not metrics_list:
            raise ValueError("No available metrics for the specified experiment and run")
        metric = metrics_list[0]

    n_dim = get_dim(experiment_id, run_id, metric)
    dim = max(1, min(dim, n_dim))

    state = {
        "type": "lines",
        "experiment_id": experiment_id,
        "run_id": run_id,
        "plot_id": plot_id,
        "metrics": [
            {
                "metric": [metric],
                "option": {
                    "dim": dim,
                    "n_dim": n_dim,
                },
            }
        ],
    }
    update_plot_state(run_id, state)


def generate_plot(experiment_id: int, run_id: str, metric: str, n_dim: int = 1, dim: int = 1):
    try:
        data = get_data(experiment_id, run_id, metric)
        data = data.reshape((-1, n_dim))
        x = np.arange(data.shape[0])
        lines = [go.Scatter(x=x, y=data[:, i], mode="lines", name=f"{metric} dim{i + 1}") for i in range(dim)]
        return {"data": lines, "layout": {"title": f"{metric} for Run {run_id}", "height": 300}}
    except Exception as e:
        return {"data": [], "layout": {"title": f"{metric} (load error)", "height": 300}}


if __name__ == "__main__":
    pass
