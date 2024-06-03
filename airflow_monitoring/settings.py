import os

# Airflow
AIRFLOW_URL = os.environ["AIRFLOW_URL"]
AIRFLOW_USER = os.environ["AIRFLOW_USER"]
AIRFLOW_PASSWORD = os.environ["AIRFLOW_PASSWORD"]

# App config
USER_AGENT = os.environ["USER_AGENT"]
IS_LOCAL = os.environ["ENVIRONMENT"] == "local"
IS_DEBUG = bool(os.getenv("IS_DEBUG"))
SAVE_MAX_DAG_RUNS = (
    int(os.getenv("SAVE_MAX_DAG_RUNS")) if os.getenv("SAVE_MAX_DAG_RUNS") else 1000
)
SLEEP_AFTER_DAG = (
    float(os.getenv("SLEEP_AFTER_DAG")) if os.getenv("SLEEP_AFTER_DAG") else 0.5
)

# PostgreSQL
PSQL_CONN = os.environ["PSQL"]
PSQL_SCHEMA = os.getenv("PSQL_SCHEMA", "public")
PSQL_ROLE = os.getenv("PSQL_ROLE")
# Handle templated connection string
if _psql_user := os.getenv("PSQL_USER"):
    PSQL_CONN = PSQL_CONN.replace("<user>", _psql_user)
if _psql_psw := os.getenv("PSQL_PASSWORD"):
    PSQL_CONN = PSQL_CONN.replace("<password>", _psql_psw)
