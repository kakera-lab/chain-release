from urllib.parse import urlparse

import requests
from optuna.storages import GrpcStorageProxy


class APIGrpcStorageProxy(GrpcStorageProxy):
    def __init__(self, uri: str) -> None:
        self.uri = uri.rstrip("/")
        self.parsed = urlparse(self.uri)

        try:
            res = requests.get(f"{self.uri}/grpc", timeout=40)
            res.raise_for_status()
            port_info = res.json()  # or res.text if it's just a number
            self.port = port_info["port"] if isinstance(port_info, dict) else int(port_info)
        except Exception as e:
            raise RuntimeError(f"Failed to get gRPC port from {self.uri}/grpc: {e}")

        super().__init__(host=self.parsed.hostname, port=self.port)


if __name__ == "__main__":
    pass
