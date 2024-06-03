from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ..settings import PSQL_SCHEMA, USER_AGENT


# Declare models
class Base(DeclarativeBase):
    pass


class AirflowDagRun(Base):
    __tablename__ = "airflow_dag_run"
    __table_args__ = {
        "schema": PSQL_SCHEMA,
        "comment": USER_AGENT,
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    dag_id = Column(String, index=True)
    dag_description = Column(String)
    run_id = Column(String)
    state = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Float, comment="in seconds")
    saved_at = Column(DateTime)
    airflow_env = Column(String)

    task_runs: Mapped[list["AirflowDagTaskRun"]] = relationship(back_populates="run")

    def __repr__(self) -> str:
        return f"AirflowDagRun(dag_id={self.dag_id}, run_id={self.run_id})"


class AirflowDagTaskRun(Base):
    __tablename__ = "airflow_dag_task_run"
    __table_args__ = {
        "schema": PSQL_SCHEMA,
        "comment": USER_AGENT,
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    dag_id = Column(String, index=True)
    run_id = Column(String)
    task_id = Column(String)
    operator = Column(String)
    state = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Float, comment="in seconds")
    try_number = Column(Integer)
    run_db_id: Mapped[int] = mapped_column(
        ForeignKey(f"{PSQL_SCHEMA}.airflow_dag_run.id")
    )

    run: Mapped["AirflowDagRun"] = relationship(back_populates="task_runs")

    def __repr__(self) -> str:
        return f"AirflowDagTaskRun(dag_id={self.dag_id}, run_id={self.run_id}, task_id={self.task_id})"
