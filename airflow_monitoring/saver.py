import datetime
import time
import typing

import sqlalchemy
import structlog

from .airflow_api import AirflowApi
from .db import queries
from .db.models import AirflowDagRun, AirflowDagTaskRun


def iso_to_dt(time_str: str) -> datetime.datetime | None:
    if not time_str:
        return None
    return datetime.datetime.fromisoformat(time_str)


class Saver:
    def __init__(
        self,
        airflow_api: AirflowApi,
        db_session: sqlalchemy.orm.session.Session,
        logger: structlog._config.BoundLoggerLazyProxy = None,
    ) -> None:
        self.airflow_api = airflow_api
        self.db_session = db_session
        self.log = logger or structlog.get_logger("saver")

    def _find_save_since_dt(self, dag_id: str) -> typing.Optional[datetime.datetime]:
        dag_run = queries.get_newest_dag_run(dag_id, self.db_session)
        if dag_run:
            return dag_run.end_time + datetime.timedelta(seconds=0.1)
        return None

    def _process_run(self, dag_id: str, run_id: str, run: dict) -> AirflowDagRun | None:
        # Skip run with empty start_date
        if not run["start_date"]:
            self.log.warning("start_date.empty", run_id=run_id)
            return None
        # Get tasks
        api_tasks = self.airflow_api.get_tasks(dag_id=dag_id, dag_run_id=run_id)
        db_tasks = []
        for task in api_tasks:
            self.log.debug("process_run.task_found", task_id=task["task_id"])
            _start_time = (
                iso_to_dt(task["start_date"])
                if task["start_date"]
                else iso_to_dt(task["execution_date"])
            )
            _item = AirflowDagTaskRun(
                dag_id=dag_id,
                run_id=run_id,
                task_id=task["task_id"],
                operator=task["operator"],
                state=task["state"],
                start_time=_start_time,
                end_time=iso_to_dt(task["end_date"]),
                duration=task["duration"],
                try_number=task["try_number"],
            )
            db_tasks.append(_item)
        # Save dag run with task runs
        _start_time = iso_to_dt(run["start_date"])
        _end_time = iso_to_dt(run["end_date"])
        _duration = _end_time - _start_time
        db_run = AirflowDagRun(
            dag_id=dag_id,
            run_id=run_id,
            state=run["state"],
            start_time=_start_time,
            end_time=_end_time,
            duration=_duration.total_seconds(),
            task_runs=db_tasks,
        )
        return db_run

    def run(
        self,
        save_since_dt_manual: datetime.datetime = None,
        save_only_dag: str = None,
        commit_db_changes: bool = True,
        save_max_dag_runs: int = None,
        sleep_after_dag: float = None,
    ):
        # pylint: disable=too-many-arguments
        # Check if AF server available.
        self.airflow_api.check_access()
        # Find dags
        dags = self.airflow_api.get_dags()
        self.log.info("run.got_dags", total_count=len(dags))
        runs_save_time = datetime.datetime.now()
        for dag in dags:
            dag_id = dag["dag_id"]
            # Process only specific dag.
            if save_only_dag and dag_id != save_only_dag:
                continue
            self.log = self.log.bind(dag_id=dag_id)
            self.log.info("run.dag")
            # Manually entered date - save all runs.
            if save_since_dt_manual:
                save_since_dt = save_since_dt_manual
                self.log.info("run.save_since_dt", manual_dt=str(save_since_dt))
            # Save only runs not already in DB.
            else:
                save_since_dt = self._find_save_since_dt(dag_id)
                self.log.info("run.save_since_dt", newest_dag_run=str(save_since_dt))
            # Find runs
            dag_runs = self.airflow_api.get_runs(
                dag_id=dag_id, end_time_since=save_since_dt, max_runs=save_max_dag_runs
            )
            if not dag_runs:
                self.log.warning("run.no_new_dag_runs_found")
                continue
            self.log.info("run.dag_runs_found", runs_count=len(dag_runs))
            # For each run, get tasks and add to DB
            for run in dag_runs:
                run_id = run["dag_run_id"]
                self.log.info("run.got_dag_run", run_id=run_id)
                db_run = self._process_run(dag_id, run_id, run)
                if not db_run:
                    continue
                db_run.dag_description = dag["description"]
                db_run.saved_at = runs_save_time
                db_run.airflow_env = self.airflow_api.base_url
                self.db_session.add(db_run)
            # Save to DB for this dag
            if commit_db_changes:
                self.db_session.commit()
                self.log.info("run.db_changes_commited")
            # Don't overload AF API :D
            if sleep_after_dag:
                time.sleep(sleep_after_dag)
