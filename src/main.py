import logging
from collections.abc import Callable
from pathlib import Path

import mlflow
import numpy as np
import optuna
import toml
from mlflow import ActiveRun
from omegaconf import DictConfig
from optuna.artifacts import upload_artifact

import chain
from chain import chaser
from chain.optuna.artifacts import APIBoto3ArtifactStore
from chain.optuna.storages import APIGrpcStorageProxy

logger = logging.getLogger(__name__)
pyproject_path = Path("./pyproject.toml")
pyproject = toml.load(pyproject_path)

optuna_uri = pyproject.get("project", {}).get("chain", {}).get("optuna", "")
storage = APIGrpcStorageProxy(optuna_uri)
artifact_store = APIBoto3ArtifactStore(optuna_uri)


# 引数を渡すためにラップする
def wrap(configs: DictConfig, parent: ActiveRun) -> Callable:
    # OptunaのTrial, mlflowは必ず子Runとして開始, 親RunのIDを指定(並列化対策)
    def objective(trial: optuna.Trial) -> float:
        run_name = f"trial_{trial.number}"
        file_path = Path(configs.run.out_dir) / f"{run_name}.txt"
        x = trial.suggest_float("x", -5, 5)
        y = trial.suggest_float("y", -5, 5)
        with open(file_path, "w") as f:
            f.write(run_name)
        with mlflow.start_run(run_name=run_name, parent_run_id=parent.info.run_id, nested=True) as child:
            chaser.start_run()
            upload_artifact(artifact_store=artifact_store, file_path=file_path, study_or_trial=trial)
            for i in range(1000):
                chaser.log_metric("test", np.random.random(100))
            chaser.end_run()
        return x**2 + y**2

    return objective


@chain.hydra.main(version_base=None, config_path="./configs", config_name="sample")
def main(configs: DictConfig, run: ActiveRun) -> None:
    # 親のMLFlow(run)が起動している状態
    study = optuna.create_study(storage=storage, study_name=configs.optuna.study_name, load_if_exists=True)
    study.optimize(wrap(configs, run), n_trials=configs.optuna.n_trials, n_jobs=configs.optuna.n_jobs)


if __name__ == "__main__":
    main()
