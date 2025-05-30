from pathlib import Path

import mlflow


def upload_artifact(dirpath: Path, suffix: list[str], artifact_path: str) -> None:
    if dirpath.exists():
        for ext in suffix:
            for file in dirpath.glob(ext):
                mlflow.log_artifact(str(file), artifact_path)


if __name__ == "__main__":
    pass
