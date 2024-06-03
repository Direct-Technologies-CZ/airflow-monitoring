from sqlalchemy import select
from sqlalchemy.orm.session import Session

from .models import AirflowDagRun


def get_newest_dag_run(dag_id: str, session: Session) -> AirflowDagRun:
    stmt = (
        select(AirflowDagRun).filter_by(dag_id=dag_id).order_by(AirflowDagRun.id.desc())
    )
    result = session.scalars(stmt)
    return result.first()
