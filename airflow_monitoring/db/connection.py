import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .models import Base


def create_db(db_conn: str, db_role: str = None, echo_sql=False):
    engine = create_engine(db_conn, echo=echo_sql)
    with engine.connect() as conn:
        if db_role:
            conn.execute(sqlalchemy.text(f"SET ROLE {db_role}"))
        Base.metadata.create_all(conn, checkfirst=True)
        conn.commit()


def get_db_session(db_conn: str, echo_sql=False) -> Session:
    engine = create_engine(db_conn, echo=echo_sql)
    return Session(engine)
