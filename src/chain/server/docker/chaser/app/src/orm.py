from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ExperimentORM(Base):
    __tablename__ = "experiments"

    num = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), unique=True, nullable=False)
    date = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    runs = relationship("RunORM", back_populates="experiment", cascade="all, delete-orphan")


class RunORM(Base):
    __tablename__ = "runs"

    num = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(100), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    state = Column(Text, nullable=False, default="{}")
    date = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    experiment = relationship("ExperimentORM", back_populates="runs")
    tags = relationship("TagORM", back_populates="run", cascade="all, delete-orphan")


class TagORM(Base):
    __tablename__ = "tags"

    num = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), ForeignKey("runs.id"), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(String(100), nullable=False)
    date = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    run = relationship("RunORM", back_populates="tags")


if __name__ == "__main__":
    pass
