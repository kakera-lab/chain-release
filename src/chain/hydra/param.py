from typing import Any

import mlflow
from omegaconf import DictConfig, ListConfig


def log_params(configs: DictConfig) -> None:
    def _wrapper(tag: str, configs: DictConfig | ListConfig | Any) -> None:
        if isinstance(configs, DictConfig):
            for key, value in configs.items():
                _wrapper(f"{str(tag)}.{str(key)}", value)
        elif isinstance(configs, ListConfig):
            for key, value in enumerate(configs):
                _wrapper(f"{str(tag)}.{str(key)}", value)
        else:
            mlflow.log_param(tag, configs)

    for key, value in configs.items():
        _wrapper(str(key), value)


if __name__ == "__main__":
    pass
