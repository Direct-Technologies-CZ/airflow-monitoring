import datetime

import requests
import structlog


class AirflowApi:
    def __init__(
        self,
        base_url: str,
        http_session: requests.sessions.Session,
        logger: structlog._config.BoundLoggerLazyProxy = None,
    ) -> None:
        self.base_url = base_url
        self.session = http_session
        self.log = logger or structlog.get_logger("af_api")

    def check_access(self) -> bool:
        r = self.session.get(self.base_url + "dags", params={"limit": 1}, verify=False)
        if r.status_code == 200:
            return True
        r.raise_for_status()
        return False

    def get_dags(self) -> list[dict]:
        response = self._get_dags_page()
        total_count = response["total_entries"]
        current_count = len(response["dags"])
        all_dags = response["dags"]
        # More items available than returned
        if total_count > current_count:
            for offset in range(current_count, total_count, current_count):
                new_dags = self._get_dags_page(offset)
                if new_dags["dags"]:
                    all_dags.extend(new_dags["dags"])
                else:
                    break
        # Check
        assert len(all_dags) == total_count
        return all_dags

    def _get_dags_page(self, offset: int = None) -> dict:
        params = None
        if offset:
            params = {"offset": offset}
        r = self.session.get(self.base_url + "dags", params=params, verify=False)
        return r.json()

    def get_runs(
        self,
        dag_id: str,
        end_time_since: datetime.datetime = None,
        max_runs: int = None,
    ) -> list[dict]:
        response = self._get_runs_page(dag_id=dag_id, end_time_since=end_time_since)
        if max_runs:
            total_count = min(max_runs, response["total_entries"])
        else:
            total_count = response["total_entries"]
        self.log.info(
            "get_runs.first_request",
            total_entries=response["total_entries"],
            max_total_count=total_count,
        )
        current_count = len(response["dag_runs"])
        all_runs = response["dag_runs"]
        # More items available than returned
        if total_count > current_count:
            for offset in range(current_count, total_count, current_count):
                new_runs = self._get_runs_page(
                    dag_id=dag_id, offset=offset, end_time_since=end_time_since
                )
                if new_runs["dag_runs"]:
                    all_runs.extend(new_runs["dag_runs"])
                else:
                    break
        # Check
        if max_runs:
            assert len(all_runs) <= max_runs
        else:
            assert len(all_runs) == total_count
        # Sort from earliest
        all_runs.reverse()
        return all_runs

    def _get_runs_page(
        self, dag_id: str, offset: int = None, end_time_since: datetime.datetime = None
    ) -> dict:
        params = {"order_by": "-end_date"}
        if end_time_since:
            params["end_date_gte"] = end_time_since.isoformat()
        if offset:
            params["offset"] = offset
        url = f"{self.base_url}dags/{dag_id}/dagRuns"
        r = self.session.get(url, params=params, verify=False)
        return r.json()

    def get_tasks(self, dag_id: str, dag_run_id: str) -> list[dict]:
        url = f"{self.base_url}dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances"
        r = self.session.get(url, verify=False)
        return r.json()["task_instances"]
