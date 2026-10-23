import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

ALLOWED_TABLES = {"customers", "products", "orders", "order_items"}
ALLOWED_SCHEMAS = {"", "public"}
MAX_ROWS = 100


class UnsafeSQLError(ValueError):
    """Raised when SQL is not a single, safe, read-only query."""


def validate_sql(sql: str) -> str:
    """Return a cleaned version of the SQL, or raise UnsafeSQLError."""
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except SqlglotError as e:
        raise UnsafeSQLError("The SQL could not be understood.") from e

    # 1. Exactly one statement
    if len(statements) != 1:
        raise UnsafeSQLError("Exactly one SQL statement is allowed.")
    tree = statements[0]

    # 2. Must be a query (SELECT, or SELECT ... UNION SELECT ...)
    if not isinstance(tree, exp.Query):
        raise UnsafeSQLError("Only SELECT queries are allowed.")

    # 3. No hidden writes, SELECT ... INTO, or row locking anywhere inside
    if tree.find(exp.Insert, exp.Update, exp.Delete, exp.Into, exp.Lock):
        raise UnsafeSQLError("Queries that change data are not allowed.")

    # 4. Only our 4 tables (plus names defined in WITH ... AS)
    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        schema = table.db.lower()
        if not schema and name in cte_names:
            continue
        if name not in ALLOWED_TABLES or schema not in ALLOWED_SCHEMAS:
            raise UnsafeSQLError(
                f"Table not allowed: {table.sql(dialect='postgres')}"
            )

    # Rebuild the SQL cleanly (this also drops any trailing semicolon)
    return tree.sql(dialect="postgres")


def add_row_limit(sql: str, max_rows: int = MAX_ROWS) -> str:
    """Wrap a validated query so it can never return more than max_rows."""
    return f"SELECT * FROM ({sql}) AS q LIMIT {max_rows}"
