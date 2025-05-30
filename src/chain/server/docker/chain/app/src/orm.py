import logging
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

logger = logging.getLogger(__name__)

Base = declarative_base()
ID_NUM = 32


class UserORM(Base):
    __tablename__ = "users"
    num = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(ID_NUM), unique=True, nullable=False)
    name = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))


class ProjectORM(Base):
    __tablename__ = "projects"
    num = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(ID_NUM), unique=True, nullable=False)
    name = Column(String(255), unique=True, nullable=False)
    user_id = Column(String(ID_NUM), ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    user = relationship("UserORM", backref="projects")


class ServicePortORM(Base):
    __tablename__ = "ports"
    num = Column(Integer, primary_key=True, autoincrement=True)
    prj_id = Column(String(ID_NUM), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)

    project = relationship("ProjectORM", backref="ports")

    __table_args__ = (UniqueConstraint("prj_id", "name", name="uq_project_service"),)


class AccessORM(Base):
    __tablename__ = "accesses"
    num = Column(Integer, primary_key=True, autoincrement=True)
    prj_id = Column(String(ID_NUM), ForeignKey("projects.id"), nullable=False)
    user_id = Column(String(ID_NUM), ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    project = relationship("ProjectORM", backref="accesses")
    user = relationship("UserORM", backref="accesses")

    __table_args__ = (UniqueConstraint("prj_id", "user_id", name="uq_project_user"),)


class ActiveRunORM(Base):
    __tablename__ = "runs"
    num = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(255), unique=True, nullable=False)
    prj_id = Column(String(ID_NUM), ForeignKey("projects.id"), nullable=False)
    user_id = Column(String(ID_NUM), ForeignKey("users.id"), nullable=False)
    status = Column(Boolean, nullable=False, default=True)
    date = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    project = relationship("ProjectORM", backref="runs")
    user = relationship("UserORM", backref="runs")


if __name__ == "__main__":
    pass
