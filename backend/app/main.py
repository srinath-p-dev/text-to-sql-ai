from fastapi import FastAPI
from sqlalchemy import text

from .db import engine

app = FastAPI(title="Text-to-SQL API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():
    with engine.connect() as conn:
        user = conn.execute(text("SELECT current_user")).scalar_one()
        count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar_one()
    return {"database": "connected", "connected_as": user, "customers": count}
