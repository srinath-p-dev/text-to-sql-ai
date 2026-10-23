"""Quick manual test for app/safety.py. Run from the backend folder:
    python check_safety.py
It only checks text. It never connects to the database.
"""
from app.safety import UnsafeSQLError, add_row_limit, validate_sql

SAFE = [
    "SELECT COUNT(*) FROM customers;",
    "SELECT SUM(order_items.quantity * order_items.unit_price) FROM order_items "
    "JOIN orders ON order_items.order_id = orders.order_id "
    "WHERE orders.status != 'cancelled';",
    "WITH t AS (SELECT * FROM orders) SELECT COUNT(*) FROM t",
    "SELECT * FROM public.products",
]

BLOCKED = [
    "DELETE FROM customers",
    "UPDATE products SET price = 0",
    "DROP TABLE customers",
    "SELECT 1; DROP TABLE customers",
    "WITH x AS (DELETE FROM orders RETURNING *) SELECT * FROM x",
    "SELECT * INTO copy_of_customers FROM customers",
    "SELECT * FROM pg_catalog.pg_user",
    "SELECT * FROM secret_table",
    "",
    "SELECT 'unclosed quote FROM customers",
]

passed = 0
total = len(SAFE) + len(BLOCKED)

for sql in SAFE:
    try:
        cleaned = validate_sql(sql)
        print(f"PASS  allowed : {sql[:60]}")
        passed += 1
    except UnsafeSQLError as e:
        print(f"FAIL  blocked a safe query: {sql[:60]}  ({e})")

for sql in BLOCKED:
    try:
        validate_sql(sql)
        print(f"FAIL  allowed a dangerous query: {sql[:60]!r}")
    except UnsafeSQLError as e:
        print(f"PASS  blocked : {sql[:60]!r}  ({e})")
        passed += 1

print()
print("Row-limit example:", add_row_limit(validate_sql("SELECT * FROM customers")))
print(f"\n{passed}/{total} checks passed")
