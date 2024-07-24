# Airflow monitoring

## Purpose

This app reads from [Airflow](https://airflow.apache.org/) [REST API](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html) and saves data about DAG runs and their tasks to database. 

For the DAG run, it calculates duration based on `start_date` and `end_date` values from the API. Please see the [DB models](./airflow_monitoring/db/models.py) for all data it saves. 

The app checks the `end_date` of the newest saved run for each DAG and saves only newer runs. If you run it more times, it saves data only once. This means you can run it periodically with no worries.

## Usage

### Environment variables

#### Mandatory

* `PSQL`: Connection string to PostgreSQL DB instance in format: `postgresql://<user>:<password>@<host>:<port>/<db_name>`
* `AIRFLOW_USER` and `AIRFLOW_PASSWORD`: You can create the user via [API call](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/post_user), role is `Viewer`.
* `AIRFLOW_URL`: Link to API, example: `https://host.domain/api/v1/`
* `USER_AGENT`: Depends on you, suggested format: `team_name app_name`
* `ENVIRONMENT`: `local` or `production`

#### Optional

* You can use variables `PSQL_USER` and `PSQL_PASSWORD` without including the user and password in the `PSQL` connection string. The values get automatically replaced (see [settings.py](./airflow_monitoring/settings.py)).
* `PSQL_ROLE`: If the user needs another role for creating database objects (see [connection.py](./airflow_monitoring/db/connection.py)). 
* `PSQL_SCHEMA`: default is `public` 
* `SAVE_MAX_DAG_RUNS`: default is 1000
* `SLEEP_AFTER_DAG`: how long to wait between DAGs processing. default is 0.5 seconds.
* `IS_DEBUG`: if set to anything, logger prints text instead of JSON

### Production deployment

Use the provided `Dockerfile` to build image and store it to an image registry. Or use the image from [Github Registry](https://github.com/Direct-Technologies-CZ/airflow-monitoring/pkgs/container/airflow-monitoring) - the URL is `ghcr.io/direct-technologies-cz/airflow-monitoring:<version>`. As `version` use either `main` for the latest or `sha-xxx` for a version based on a specific commit. A new version is generated either on a new commit to main branch or once per year in January.

Use the image to run the main script like this: 
```
poetry run python -m airflow_monitoring.main
```

To run periodically (e.g. once per day), use a CRON scheduler. If you have Kubernetes cluster available, use `Cronjob` object to run it. You should use `args` field (not `command`) to not replace entrypoint in Dockerfile. Please see example definition [here](./k8s_cronjob.yaml). If you want to run multiple commands at once (e.g. for monitoring), do it like this:

`args: ["/bin/sh","-c", "poetry run python -m airflow_monitoring.main && curl https://hc-ping.com/xxx"]`

### Local usage
You need to have `.env` file in the root folder, containing environment variables (see `template.env` for example).

To run the code, you can use either Poetry or Docker.

`PSQL` must point to a running PostgreSQL instance: either remote or local. If you don't have any, you can use Docker to run it -- see below.

#### Poetry
* Install [Poetry](https://python-poetry.org/docs/#installation)
* Install [dotenv plugin](https://pypi.org/project/poetry-dotenv-plugin/): `poetry self add poetry-dotenv-plugin`
* Run `poetry install`

Then you can run scripts like this: `poetry run python -m airflow_monitoring.main`

#### Docker
App is installed into venv to not mix system and Poetry dependencies with app dependencies.

1. Build image: `docker-compose build`
2. Run script: `docker-compose run app poetry run python -m airflow_monitoring.main`

If you want to run the PostgreSQL DB from Docker, use this command: `docker-compose up db` (add `-d` to run in background). Then set `PSQL` variable to `postgresql://postgres:sample@db:5432`.

To connect to the DB via command line and inspect data, use this command: `docker-compose run db psql --host=db --username=postgres` (password is `sample`). You can also connect to the DB from your host system: in this case the host is `localhost`.

## More info

### Run configuration
Because there can be many `dagRuns` in the history, we limit the total number of runs saved to DB for each DAG. You can set it via `SAVE_MAX_DAG_RUNS` envvar, the default value is 1000.

So on the first run, the script reads the maximum allowed number of runs from the API, starting from the newest. You can also set a specific date in the [main.py](./airflow_monitoring/main.py) using the `save_since_dt` variable. In this case it gets the data since this date, but again sorted from the newest. The `SAVE_MAX_DAG_RUNS` limit is applied. If you really want to save all runs since the date, set it to a high enough number.

You can also use `save_only_dag` variable to save data only for a specific DAG (you provide its ID).

### Implementation
First, the script uses [dags](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#tag/DAG) endpoint to get all DAGs. Then for each DAG, it gets [dagRuns](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#tag/DAGRun) sorted by `end_date` from the latest, where `end_date` is higher than the newest `dagRun` saved in the DB for given `DAG`. Lastly, it gets [taskInstances](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#tag/TaskInstance) for given `dagRun` and saves them as well.

NOTICE: There is no paging for the `taskInstances` - the API returns 100 items by default, which should be enough for most cases. If needed, you can update [the code here](https://github.com/Direct-Technologies-CZ/airflow-monitoring/blob/33399e983036d3535d9664294e1d2dea4b1c6d05/airflow_monitoring/airflow_api.py#L98).

## Development 

Please use [pre-commit](https://pre-commit.com/) if changing the code:
* Install the command: `pip install pre-commit`
* Install repo hooks: `pre-commit install`

Requirements are managed by [Poetry](https://python-poetry.org/) and defined in [pyproject.toml](./pyproject.toml).

You can run tests via `pytest` command.
