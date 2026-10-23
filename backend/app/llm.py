import json
import re

import httpx

from .config import settings

SCHEMA = """
customers(customer_id, full_name, email, city, country, signup_date)
products(product_id, product_name, category, price, stock_qty)
    -- price is the CURRENT list price
orders(order_id, customer_id -> customers.customer_id, order_date, status)
    -- status is one of: pending, shipped, delivered, cancelled
order_items(order_item_id, order_id -> orders.order_id,
            product_id -> products.product_id, quantity, unit_price)
    -- unit_price is the price actually paid at the time of purchase
"""

SYSTEM_PROMPT = (
    "You are an expert PostgreSQL assistant.\n"
    "Write ONE PostgreSQL SELECT query that answers the user's question, "
    "using only these tables:\n"
    + SCHEMA
    + "\nRules:\n"
    "- Return only the SQL query, with no explanation.\n"
    "- Use only SELECT. Never write INSERT, UPDATE, DELETE, DROP, ALTER, "
    "or any other command that changes data.\n"
    "- Revenue = SUM(order_items.quantity * order_items.unit_price), "
    "excluding orders where orders.status = 'cancelled'.\n"
    "- For revenue, use order_items.unit_price, not products.price.\n"
    "- Exclude cancelled orders ONLY for revenue or money questions. Questions about whether a customer placed an order, or how many orders exist, must include ALL orders, including cancelled ones.\n"
)

# Matches ```sql ... ``` or ``` ... ``` around the answer
FENCE = re.compile(r"```(?:sql)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def clean_sql(text: str) -> str:
    match = FENCE.search(text)
    if match:
        text = match.group(1)
    return text.strip()


def generate_sql(question: str) -> str:
    response = httpx.post(
        f"{settings.ollama_url}/api/chat",
        json={
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=120,
    )
    response.raise_for_status()
    return clean_sql(response.json()["message"]["content"])


EXPLAIN_PROMPT = (
    "You explain database query results to a non-technical person.\n"
    "Answer the user's question in one or two short sentences, "
    "using ONLY the data provided.\n"
    "- Never invent or estimate numbers that are not in the data.\n"
    "- If the data has no rows, say that nothing matched.\n"
    "- Do not mention SQL, queries, tables, or column names.\n"
    "- Do not add currency symbols or units that are not in the data.\n"
)

MAX_EXPLAIN_ROWS = 20


def explain_result(question: str, columns: list[str], rows: list[list]) -> str:
    data = {"columns": columns, "rows": rows[:MAX_EXPLAIN_ROWS]}
    note = ""
    if len(rows) > MAX_EXPLAIN_ROWS:
        note = f"\n(Only the first {MAX_EXPLAIN_ROWS} of {len(rows)} rows are shown.)"
    user_message = (
        f"Question: {question}\n"
        f"Data: {json.dumps(data, default=str)}{note}"
    )
    response = httpx.post(
        f"{settings.ollama_url}/api/chat",
        json={
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": EXPLAIN_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()
