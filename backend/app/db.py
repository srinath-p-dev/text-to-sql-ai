from sqlalchemy import URL, create_engine, text

from .config import settings

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=settings.db_user,
    password=settings.db_password.get_secret_value(),
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)

engine = create_engine(database_url, pool_pre_ping=True)


def run_readonly_query(sql: str) -> tuple[list[str], list[list]]:
    """Run one already-validated query in a read-only transaction.

    Returns (column names, rows). The transaction is always rolled back.
    """
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        conn.execute(text("SET LOCAL statement_timeout = '5s'"))
        # no_parameters=True: send the SQL as-is, so characters like % or :
        # inside the query are not mistaken for parameter placeholders
        result = conn.exec_driver_sql(
            sql, execution_options={"no_parameters": True}
        )
        columns = list(result.keys())
        rows = [list(row) for row in result]
        conn.rollback()
    return columns, rows
