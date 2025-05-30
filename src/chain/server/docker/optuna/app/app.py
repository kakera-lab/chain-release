import io
import logging
import os
from threading import Thread

import boto3
import optuna
from bottle import Bottle, HTTPResponse, request, run
from optuna.artifacts import Boto3ArtifactStore
from optuna.storages import RDBStorage, get_storage, run_grpc_proxy_server
from optuna_dashboard import wsgi

logger = logging.getLogger(__name__)

storage = get_storage(os.getenv("DB_STORAGE"))


def start_grpc_background():
    def start():
        run_grpc_proxy_server(storage, host="0.0.0.0", port=13000)

    Thread(target=start, daemon=True).start()


optuna.create_study(
    study_name="Default",
    storage=os.getenv("DB_STORAGE"),
    load_if_exists=True,
)

app = Bottle()
start_grpc_background()
app.mount("/", wsgi(RDBStorage(url=os.getenv("DB_STORAGE"))))


s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
artifacts = Boto3ArtifactStore(bucket_name=os.getenv("PRJ_ID"), client=s3, avoid_buf_copy=False)


@app.get("/grpc")
def get_grpc_port():
    return {"port": os.getenv("GRPC_PORT")}


@app.get("/open_reader/<artifact_id>")
def open_reader_artifact(artifact_id):
    try:
        artifact_id = f"optuna/{artifact_id}"
        result = artifacts.open_reader(artifact_id=artifact_id)
        return HTTPResponse(body=result.read(), content_type="application/octet-stream")
    except Exception as e:
        return HTTPResponse(status=404, body=str(e))


@app.post("/write/<artifact_id>")
def write_artifact(artifact_id):
    file = request.files.get("file")
    content_body = io.BytesIO(file.file.read())
    artifact_id = f"optuna/{artifact_id}"
    artifacts.write(artifact_id=artifact_id, content_body=content_body)
    return {"status": "write"}


@app.post("/remove/<artifact_id>")
def remove_artifact(artifact_id):
    artifact_id = f"optuna/{artifact_id}"
    artifacts.remove(artifact_id=artifact_id)
    return {"status": "remove"}


if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000)
