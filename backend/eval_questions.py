"""Ask the AI our known test questions and score the answers.

Run from the backend folder (with .venv active and Ollama running):
    python eval_questions.py

It uses the same safe path as /ask: AI -> safety checker -> read-only query.
"""
import time
from decimal import Decimal

import httpx
from sqlalchemy.exc import DBAPIError

from app.db import run_readonly_query
from app.llm import generate_sql
from app.safety import UnsafeSQLError, add_row_limit, validate_sql

# Expected answers come from database/03_test_queries.sql.
# All text is compared in lowercase; numbers ignore trailing zeros.
TESTS = [
    {"question": "How many customers are there?", "rows": 1, "contains": ["12"]},
    {"question": "How many orders are there in total?", "rows": 1, "contains": ["20"]},
    {"question": "What is the total revenue?", "rows": 1, "contains": ["1795"]},
    {
        "question": "Who are the top 5 customers by revenue?",
        "rows": 5,
        "order": ["ben clark", "asha rao", "carmen diaz", "emma wilson", "farah khan"],
        "pairs": [
            ("ben clark", "443"),
            ("asha rao", "318"),
            ("carmen diaz", "284"),
            ("emma wilson", "199"),
            ("farah khan", "173"),
        ],
    },
    {
        "question": "What is the revenue for each month?",
        "rows": 4,
        "contains": ["361", "503", "474", "457"],
    },
    {
        "question": "Which customers have never placed an order?",
        "rows": 1,
        "contains": ["kofi mensah"],
    },
    {
        "question": "Which products have never been sold?",
        "rows": 1,
        "contains": ["phone stand"],
    },
    {
        "question": "What is the revenue for each product category?",
        "rows": 4,
        "pairs": [
            ("electronics", "1140"),
            ("home", "274"),
            ("accessories", "228"),
            ("stationery", "153"),
        ],
    },
    {
        "question": "Which customers have zero revenue?",
        "rows": 2,
        "contains": ["kofi mensah", "lina haddad"],
    },
    {
        "question": "How many orders are there in each status?",
        "rows": 4,
        "pairs": [
            ("delivered", "13"),
            ("shipped", "3"),
            ("pending", "2"),
            ("cancelled", "2"),
        ],
    },
]


def norm(value) -> str:
    """Make values comparable: lowercase text, numbers without trailing zeros."""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float, Decimal)):
        return f"{Decimal(str(value)).normalize():f}"
    return str(value).strip().lower()


def check(test: dict, rows: list[list]) -> list[str]:
    """Return a list of problems. An empty list means the test passed."""
    problems = []
    cells = [[norm(v) for v in row] for row in rows]
    flat = {c for row in cells for c in row}

    if "rows" in test and len(rows) != test["rows"]:
        problems.append(f"expected {test['rows']} rows, got {len(rows)}")

    for value in test.get("contains", []):
        if value not in flat:
            problems.append(f"missing {value!r}")

    for pair in test.get("pairs", []):
        if not any(all(p in row for p in pair) for row in cells):
            problems.append(f"no row containing {pair}")

    order = test.get("order")
    if order:
        positions = [
            next((i for i, row in enumerate(cells) if name in row), None)
            for name in order
        ]
        if None in positions or positions != sorted(positions):
            problems.append("names missing or in the wrong order")

    return problems


def main() -> None:
    passed = 0
    start_all = time.perf_counter()

    for n, test in enumerate(TESTS, 1):
        question = test["question"]
        start = time.perf_counter()
        sql = ""
        try:
            sql = generate_sql(question)
            safe_sql = validate_sql(sql)
            _, rows = run_readonly_query(add_row_limit(safe_sql))
            problems = check(test, rows)
        except httpx.HTTPError as e:
            problems = [f"could not reach Ollama: {e}"]
        except UnsafeSQLError as e:
            problems = [f"blocked by safety checker: {e}"]
        except DBAPIError as e:
            reason = str(e.orig).strip().splitlines()[0] if e.orig else "unknown"
            problems = [f"database error: {reason}"]
        seconds = time.perf_counter() - start

        if problems:
            print(f"FAIL {n:2}. {question}  ({seconds:.0f}s)")
            for p in problems:
                print(f"         - {p}")
            print(f"         SQL: {sql}")
        else:
            passed += 1
            print(f"PASS {n:2}. {question}  ({seconds:.0f}s)")

    total = time.perf_counter() - start_all
    print(f"\nScore: {passed}/{len(TESTS)}  (took {total:.0f}s)")


if __name__ == "__main__":
    main()
