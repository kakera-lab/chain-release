import logging
import os
import socket
import uuid
from contextlib import contextmanager
from typing import Any
from urllib.parse import urlparse, urlunparse

import boto3
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

import docker

from .orm import AccessORM, ActiveRunORM, Base, ProjectORM, ServicePortORM, UserORM
from .webui import stop_container_by_name

# Constants
ID_NUM = 32
SERVICE = ("mlflow", "chaser", "optuna")
SERVICE_PORT = SERVICE + ("grpc", "metric")

# Logger setup
logger = logging.getLogger(__name__)

# Environment variable check
assert os.getenv("CHAIN_URI", "") != "", "system error"

# Database and S3 setup
url = urlparse(os.getenv("CHAIN_URI"))
parsed = make_url(os.getenv("STORE_URI"))

engine = create_engine(os.getenv("STORE_URI"))
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

client = docker.from_env()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


@contextmanager
def get_session() -> Any:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def execute(query: str) -> Any:
    with engine.connect() as connection:
        result = connection.execute(text(query))
    return result


def create_id() -> str:
    return uuid.uuid4().hex


def init_user() -> None:
    with get_session() as session:
        admin_user = session.query(UserORM).filter_by(name="admin").first()
        if not admin_user:
            session.add(
                UserORM(
                    name="admin",
                    id=create_id(),
                    password=generate_password_hash("admin", method="pbkdf2:sha256"),
                    email="admin@example.com",
                    type="local",
                )
            )
            session.commit()


def safe_url(port: int) -> str | None:
    if port:
        return urlunparse(url._replace(netloc=f"{url.hostname}:{str(port)}"))
    return None


def return_url(parsed: URL, database: str) -> str:
    return str(
        URL.create(
            drivername=parsed.drivername,
            username=parsed.username,
            password=parsed.password,
            host=parsed.host,
            port=parsed.port,
            database=database,
            query=parsed.query,
        ).render_as_string(hide_password=False)
    )


def get_free_port_from_db(start: int = 30000, end: int = 39999) -> int:
    with get_session() as session:
        used_ports = {p for (p,) in session.query(ServicePortORM.port).all()}
        for port in range(start, end):
            if port in used_ports:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("0.0.0.0", port)) != 0:
                    return port
    raise RuntimeError("空きポートが見つかりませんでした")


def get_project_by_name(name: str) -> Any:
    with get_session() as session:
        return session.query(ProjectORM).filter_by(name=name).first()


def get_service_port_by_id(prj_id: str) -> Any:
    with get_session() as session:
        return {s.name: s.port for s in session.query(ServicePortORM).filter_by(prj_id=prj_id).all()}


def get_user_id(user_name: str) -> str:
    # user_name から user_id を取得する
    with get_session() as session:
        user = session.query(UserORM).filter_by(name=user_name).first()
        if not user:
            raise ValueError(f"ユーザー '{user_name}' が見つかりませんでした")
        return user.id


def all_projects(user_id: str = "") -> list:
    with get_session() as session:
        if user_id == "":
            user = session.query(UserORM).filter_by(name="admin").first()
            if not user:
                raise ValueError(f"ユーザー 'admin' が見つかりませんでした")
            user_id = user.id
        projects = session.query(ProjectORM).filter(ProjectORM.user_id == user_id).all()
        results = []
        for prj in projects:
            ports = {s.name: s.port for s in session.query(ServicePortORM).filter_by(prj_id=prj.id).all()}
            results.append(
                {
                    "id": prj.id,
                    "name": prj.name,
                    "mlflow-uri": safe_url(ports.get("mlflow")),
                    "optuna-uri": safe_url(ports.get("optuna")),
                    "dvc-uri": safe_url(ports.get("dvc")),
                    "chaser-uri": safe_url(ports.get("chaser")),
                }
            )
        return results


def add(prj_name: str, user_id: str = "") -> None:
    assert prj_name.islower() and len(prj_name) <= 255, "prj name format error"

    prj_id = create_id()
    s3.create_bucket(Bucket=prj_id)
    if user_id == "":
        with get_session() as session:
            user = session.query(UserORM).filter_by(name="admin").first()
            if not user:
                raise ValueError(f"ユーザー 'admin' が見つかりませんでした")
            user_id = user.id
    # 各サービス用のデータベースを作成
    for s in SERVICE:
        execute(f"CREATE DATABASE IF NOT EXISTS `{s}-{prj_id}`")
    # プロジェクト情報とアクセス権、ポート情報を登録
    with get_session() as session:
        prj = ProjectORM(id=prj_id, name=prj_name, user_id=user_id)
        session.add(prj)
        acc = AccessORM(prj_id=prj_id, user_id=user_id)
        session.add(acc)
        cmd = ServicePortORM(prj_id=prj_id, name="dvc", port=url.port)
        session.add(cmd)
        session.commit()
        for s in SERVICE_PORT:
            cmd = ServicePortORM(prj_id=prj_id, name=s, port=get_free_port_from_db())
            session.add(cmd)
            session.commit()


def remove(prj_id: str) -> None:
    try:
        for s in SERVICE:
            stop_container_by_name(f"{s}-{prj_id}")
            execute(f"DROP DATABASE IF EXISTS `{s}-{prj_id}`")
    except docker.errors.NotFound:
        pass
    try:
        objects = s3.list_objects_v2(Bucket=prj_id).get("Contents", [])
        for obj in objects:
            s3.delete_object(Bucket=prj_id, Key=obj["Key"])
        s3.delete_bucket(Bucket=prj_id)
    except s3.exceptions.NoSuchBucket:
        logger.warning(f"Bucket {prj_id} not found")
    with get_session() as session:
        session.query(AccessORM).filter_by(prj_id=prj_id).delete()
        session.query(ServicePortORM).filter_by(prj_id=prj_id).delete()
        session.query(ProjectORM).filter(ProjectORM.id == prj_id).delete()
        session.commit()


def start_activerun_db(user_id: str, prj_id: str) -> None:
    with get_session() as session:
        run = ActiveRunORM(user_id=user_id, prj_id=prj_id)
        session.add(run)
        session.commit()


def stop_activerun_db(user_id: str, prj_id: str) -> None:
    with get_session() as session:
        run = session.query(ActiveRunORM).filter_by(user_id=user_id, prj_id=prj_id, status=True).first()
        if run:
            run.status = False
            session.commit()


def check_activerun_db(user_id: str, prj_id: str) -> list[dict]:
    with get_session() as session:
        results = (
            session.query(ProjectORM.id, ProjectORM.name)
            .join(ActiveRunORM, ActiveRunORM.prj_id == ProjectORM.id)
            .filter(
                ActiveRunORM.user_id == user_id,
                ActiveRunORM.prj_id == prj_id,
                ActiveRunORM.status == True,
            )
            .all()
        )
        return [{"id": r.id, "name": r.name} for r in results]


if __name__ == "__main__":
    pass
