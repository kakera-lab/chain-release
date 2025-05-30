import logging
import os
from urllib.parse import urlparse, urlunparse

import boto3
from flask import Flask, Response, redirect, render_template, request, session, url_for
from sqlalchemy.engine.url import make_url

from src.engine import (
    add,
    all_projects,
    check_activerun_db,
    get_project_by_name,
    get_service_port_by_id,
    init_user,
    remove,
    return_url,
    start_activerun_db,
    stop_activerun_db,
)
from src.webui import start_chaser, start_mlflow, start_optuna, stop_container_by_name

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
with app.app_context():
    init_user()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
url = urlparse(os.getenv("CHAIN_URI"))
parsed = make_url(os.getenv("STORE_URI"))


def construct_uri(port: int) -> str:
    return urlunparse(url._replace(netloc=f"{url.hostname}:{port}"))


@app.before_request
def set_admin_user() -> None:
    session.setdefault("user", "admin")


@app.route("/")
def index() -> str:
    return render_template("index.html", projects=all_projects())


@app.route("/add/prj", methods=["POST"])
def add_project() -> Response:
    add(prj_name=request.form.get("prj_name"))
    return redirect(url_for("index"))


@app.route("/remove/prj", methods=["POST"])
def remove_project() -> Response:
    remove(prj_id=request.form.get("prj_id"))
    return redirect(url_for("index"))


@app.route("/get/prj/<name>")
def get_project(name: str) -> Response:
    project = get_project_by_name(name)
    if project is None:
        return Response("Project not found", status=404)
    return Response(str(project.id), status=200)


# dvc, mlflow, optuna, chaser
@app.route("/get/<service>/<prj_id>")
def get_uri(service: str, prj_id: str) -> Response:
    project = get_service_port_by_id(prj_id)
    if project is None:
        return Response("Project not found", status=404)
    return Response(construct_uri(project[service]), status=200)


@app.route("/up/mlflow/<prj_id>")
def mlflow_server(prj_id: str) -> Response:
    project = get_service_port_by_id(prj_id)
    if project is None:
        return Response("Project not found", status=404)
    start_mlflow(
        prj_id=prj_id,
        port=project["mlflow"],
        backend_uri=return_url(parsed, f"mlflow-{prj_id}"),
        s3_path=f"s3://{prj_id}/mlflow/artifacts",
    )
    return redirect(construct_uri(project["mlflow"]))


@app.route("/up/optuna/<prj_id>")
def optuna_server(prj_id: str) -> Response:
    project = get_service_port_by_id(prj_id)
    if project is None:
        return Response("Project not found", status=404)
    start_optuna(
        prj_id=prj_id,
        port=project["optuna"],
        backend_uri=return_url(parsed, f"optuna-{prj_id}"),
        s3_path=f"s3://{prj_id}/optuna/artifacts",
        grpc=project["grpc"],
    )
    return redirect(construct_uri(project["optuna"]))


@app.route("/up/chaser/<prj_id>")
def chaser_server(prj_id: str) -> Response:
    project = get_service_port_by_id(prj_id)
    if project is None:
        return Response("Project not found", status=404)
    start_chaser(
        prj_id=prj_id,
        port=project["chaser"],
        backend_uri=return_url(parsed, f"chaser-{prj_id}"),
        s3_path=f"s3://{prj_id}/chaser/artifacts",
        grpc=project["metric"],
    )
    return redirect(construct_uri(project["chaser"]))


@app.route("/up/prj/<prj_id>")
def prj_server(prj_id: str) -> Response:
    project = get_service_port_by_id(prj_id)
    if project is None:
        return Response("Project not found", status=404)
    mlflow_server(prj_id)
    optuna_server(prj_id)
    chaser_server(prj_id)
    return Response(status=200)


@app.route("/down/<service>/<prj_id>")
def stop_container(service: str, prj_id: str) -> Response:
    container_name = f"{service}-{prj_id}"
    stop_container_by_name(container_name)
    return Response(container_name, status=200)


@app.route("/down/prj/<prj_id>")
def stop_prj_container(prj_id: str) -> Response:
    stop_container("mlflow", prj_id)
    stop_container("optuna", prj_id)
    stop_container("chaser", prj_id)
    return Response(status=200)


@app.route("/dvc/<prj_id>/<path:key>", methods=["GET", "HEAD", "PUT", "POST"])
def dvc_proxy(prj_id: str, key: str) -> Response:
    bucket = prj_id
    s3_key = f"dvc/artifacts/{key}"

    if request.method in ["PUT", "POST"]:
        try:
            s3.put_object(Bucket=bucket, Key=s3_key, Body=request.data)
            return Response("Uploaded", status=200)
        except Exception as e:
            return Response(f"Upload failed: {e}", status=500)

    elif request.method in ["GET", "HEAD"]:
        try:
            s3_obj = s3.get_object(Bucket=bucket, Key=s3_key)
            data = s3_obj["Body"].read()
            return Response(data, status=200, content_type="application/octet-stream")
        except Exception as e:
            return Response(f"Download failed: {e}", status=404)

    return Response("Method Not Allowed", status=405)


# @app.route("/start/activerun/<user_id>/<prj_id>")
# def start_activerun(user_id: str, prj_id: str) -> Response:
#     start_activerun_db(user_id, prj_id)
#     return Response("Set", status=200)


# @app.route("/stop/activerun/<user_id>/<prj_id>")
# def stop_activerun(user_id: str, prj_id: str) -> Response:
#     stop_activerun_db(user_id, prj_id)
#     return Response("Set", status=200)


# @app.route("/check/activerun/<user_id>/<prj_id>")
# def check_activerun(user_id: str, prj_id: str) -> Response:
#     return check_activerun_db(user_id, prj_id)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8180)
