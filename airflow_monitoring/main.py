from .airflow_api import AirflowApi
from .db.connection import get_db_session, create_db
from .http_session import get_session
from .saver import Saver
from .settings import (
    AIRFLOW_PASSWORD,
    AIRFLOW_URL,
    AIRFLOW_USER,
    USER_AGENT,
    PSQL_CONN,
    PSQL_ROLE,
    IS_DEBUG,
    IS_LOCAL,
    SLEEP_AFTER_DAG,
    SAVE_MAX_DAG_RUNS
)
from .logs import get_logger

# Prepare logging
is_debug = IS_LOCAL or IS_DEBUG
logger = get_logger(name="af_main", is_debug=is_debug)

# Prepare DB
create_db(db_conn=PSQL_CONN, db_role=PSQL_ROLE)
db_session = get_db_session(db_conn=PSQL_CONN, echo_sql=False)

# Prepare working objects
http_session = get_session(
    user=AIRFLOW_USER, psw=AIRFLOW_PASSWORD, user_agent=USER_AGENT, logger=logger
)
airflow_api = AirflowApi(base_url=AIRFLOW_URL, http_session=http_session, logger=logger)
saver = Saver(airflow_api=airflow_api, db_session=db_session, logger=logger)
# Example data for manual save
"""
import datetime
save_since_dt = datetime.datetime.fromisoformat("2023-01-01T00:00:00.489281+00:00")
save_only_dag = "sample_dag_id"
"""

# Save new runs
try:
    saver.run(
        save_since_dt_manual=None,
        save_only_dag=None,
        commit_db_changes=True,
        save_max_dag_runs=SAVE_MAX_DAG_RUNS,
        sleep_after_dag=SLEEP_AFTER_DAG,
    )
finally:
    db_session.close()
