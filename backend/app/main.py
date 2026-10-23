from typing import Any
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .db import engine, run_readonly_query
from .llm import explain_result, generate_sql
from .safety import UnsafeSQLError, add_row_limit, validate_sql

app = FastAPI(title="Text-to-SQL API")

# Allow only our local website (Next.js dev server) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class QuestionIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():
    with engine.connect() as conn:
        user = conn.execute(text("SELECT current_user")).scalar_one()
        count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar_one()
    return {"database": "connected", "connected_as": user, "customers": count}


@app.post("/generate-sql")
def generate_sql_endpoint(body: QuestionIn):
    # Only generates SQL text. Does NOT run it on the database.
    return {"question": body.question, "sql": generate_sql(body.question)}


@app.post("/ask")
def ask(body: QuestionIn):
    # 1. AI writes the SQL
    try:
        sql = generate_sql(body.question)
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail="Could not reach the AI model (Ollama). Is it running?",
        ) from e

    # 2. Safety checker
    try:
        safe_sql = validate_sql(sql)
    except UnsafeSQLError as e:
        raise HTTPException(
            status_code=400, detail={"error": str(e), "sql": sql}
        ) from e

    # 3. Run it read-only, with a row limit
    try:
        columns, rows = run_readonly_query(add_row_limit(safe_sql))
    except DBAPIError as e:
        reason = str(e.orig).strip().splitlines()[0] if e.orig else "unknown"
        raise HTTPException(
            status_code=400,
            detail={
                "error": "The database could not run this query.",
                "reason": reason,
                "sql": safe_sql,
            },
        ) from e

    return {
        "question": body.question,
        "sql": safe_sql,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
    }


class ExplainIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    columns: list[str] = Field(max_length=50)
    rows: list[list[Any]] = Field(max_length=100)


@app.post("/explain")
def explain(body: ExplainIn):
    # Turns a result table into a short plain-English answer.
    # Does not touch the database.
    try:
        answer = explain_result(body.question, body.columns, body.rows)
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail="Could not reach the AI model (Ollama). Is it running?",
        ) from e
    return {"answer": answer}
