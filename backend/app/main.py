from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlalchemy import text

from .db import engine
from .llm import generate_sql

app = FastAPI(title="Text-to-SQL API")


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
