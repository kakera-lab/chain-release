import logging
import os
import shutil
import traceback
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

import hydra
import mlflow
from hydra.core.hydra_config import HydraConfig
from hydra.types import RunMode
from omegaconf import DictConfig

from .. import settings
from ..core import chaser
from ..core.email import Email
from ..core.git import Git
from ..core.mattermost import Mattermost
from ..core.setup import Setup
from . import param, upload

logger = logging.getLogger(__name__)


def main(version_base: Any | None = None, config_path: str = "../../configs", config_name: str = "sample") -> Callable:
    def decorator(func: Callable[[DictConfig], Any]) -> Callable[[], Any]:
        # 注：Hydraではconfig_pathの探索がこのファイル基準で行われる。
        # 運用上はプロジェクトルートから解決したい(config_pathが実行ファイルからの相対Pathであると期待している)。
        # 無理やり相対パスに書き換える
        from_path = Path(__file__).resolve()
        to_path = Path(config_path).resolve()
        if from_path.is_file():
            from_path = from_path.parent
        rel_config_path = Path(os.path.relpath(to_path, start=from_path))

        @wraps(func)
        @hydra.main(version_base=version_base, config_path=str(rel_config_path), config_name=config_name)
        def wrapped(configs: DictConfig) -> Any:
            if HydraConfig.get().mode == RunMode.MULTIRUN:
                raise RuntimeError("Multirun mode is not supported")
            Git.diff(configs.debug)
            mlproject = True
            if (run := mlflow.active_run()) is None:
                # 進行中の親Runなし
                mlproject = False
                mlflow.set_tracking_uri(uri=settings.mlflow_uri)
                mlflow.set_experiment(configs.exp)
                run = mlflow.start_run(run_name=configs.run.name, log_system_metrics=True)
            try:
                # out_dir = Path(HydraConfig.get().runtime.output_dir)
                out_dir = Path(configs.run.out_dir)
                config_dir = Path(configs.run.config_dir)
                docs_dir = Path(configs.run.docs_dir)
                mlflow.set_tag("Python", Setup.get_version())
                mlflow.set_tag("debug", "ON" if configs.debug else "OFF")
                mlflow.set_tag("hash", Git.hash())
                mlflow.set_tag("branch", Git.branch())
                Setup.get_env(out_dir / "requirements.txt")
                Setup.get_command(out_dir / "cmd.txt")
                Setup.set_seed(configs.run.seed)
                chaser.start_run()
                result = func(configs, run)
            except Exception:
                (out_dir / "error.log").write_text(traceback.format_exc(), encoding="utf-8")
                logger.error("例外が発生しました:\n%s", traceback.format_exc())
                result = None
            finally:
                # 親RUN用
                param.log_params(configs)
                upload.upload_artifact(out_dir, ["*.pkl", "*.ckpt", "*.pth"], "checkpoints")
                upload.upload_artifact(out_dir, ["*jpg", "*.png", "*.html"], "figure")
                upload.upload_artifact(out_dir, ["*.csv"], "csv")
                upload.upload_artifact(out_dir, ["*.sqlite3", "*.db"], "database")
                upload.upload_artifact(out_dir, ["*.txt"], "env")
                upload.upload_artifact(out_dir, ["*.log"], "log")
                upload.upload_artifact(config_dir, ["*.yaml"], "configs")
                upload.upload_artifact(docs_dir, ["*.md", "*.pdf"], "docs")
                if not configs.local_save:
                    shutil.rmtree(out_dir)
                Email(configs.notification.email)
                Mattermost(configs.notification.mattermost)
                chaser.end_run()
                if not mlproject:
                    mlflow.end_run()
            return result

        return wrapped

    return decorator


if __name__ == "__main__":
    pass
