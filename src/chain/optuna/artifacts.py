from __future__ import annotations

import io
from typing import BinaryIO

import requests
from optuna.artifacts.exceptions import ArtifactNotFound


class APIBoto3ArtifactStore:
    def __init__(self, uri: str) -> None:
        self.base_uri = uri.rstrip("/")

    def open_reader(self, artifact_id: str) -> BinaryIO:
        """指定したartifact_idのバイナリデータを読み込む（ダウンロード）。"""
        url = f"{self.base_uri}/open_reader/{artifact_id}"
        try:
            res = requests.get(url, stream=True, timeout=40)
            if res.status_code == 404:
                raise ArtifactNotFound(f"Artifact {artifact_id} not found at {url}")
            res.raise_for_status()
            return io.BytesIO(res.content)
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to open reader for {artifact_id}: {e}") from e

    def write(self, artifact_id: str, content_body: bytes | BinaryIO) -> None:
        """指定したartifact_idへバイナリデータを書き込む（アップロード）。"""
        if isinstance(content_body, bytes):
            content_body = io.BytesIO(content_body)
        url = f"{self.base_uri}/write/{artifact_id}"
        files = {"file": ("artifact.bin", content_body)}
        try:
            res = requests.post(url, files=files, timeout=40)
            res.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to write artifact {artifact_id}: {e}") from e

    def remove(self, artifact_id: str) -> None:
        """指定したartifact_idのアーティファクトを削除する。"""
        url = f"{self.base_uri}/remove/{artifact_id}"
        try:
            res = requests.delete(url, timeout=40)
            if res.status_code not in (200, 204):
                res.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to remove artifact {artifact_id}: {e}") from e


if __name__ == "__main__":
    pass
