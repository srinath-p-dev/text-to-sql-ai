# Text-to-SQL AI

Ask questions about a store database in plain English. A **local AI model** writes the SQL, a **safety checker** approves it, it runs **read-only** on PostgreSQL, and you get the answer as a table plus a short plain-English summary.

Everything runs on your own computer. No paid APIs.

## How it works

```
Your question
   → Ollama (qwen2.5-coder:7b) writes SQL
   → Safety checker (sqlglot) approves or blocks it
   → PostgreSQL runs it as a read-only user (max 100 rows, 5-second limit)
   → Answer table + AI summary in the browser
```

## Safety layers

The AI is told to write only `SELECT` queries, but instructions alone aren't trusted. In testing, the model happily wrote `DELETE FROM customers;` when asked to. These layers stop it:

1. **Safety checker** (`backend/app/safety.py`): parses the SQL and allows only a single `SELECT` on the 4 known tables. It blocks multiple statements, hidden writes inside `WITH`, `SELECT ... INTO`, row locks, system tables (with the database permissions as the final guard) and unparseable SQL.
2. **Row limit**: every query is wrapped with `LIMIT 100`.
3. **Read-only transaction**: each query runs in `SET TRANSACTION READ ONLY` with a 5-second timeout, then is rolled back.
4. **Read-only database user** (`app_readonly`): has `SELECT` permission only, so PostgreSQL itself refuses any change.

The browser never talks to the database or the AI directly. Only the backend does, and only the backend knows the database password (from `backend/.env`, which is never committed).

## Tech stack

| Part | Tools |
|---|---|
| Database | PostgreSQL 17 |
| Backend | Python, FastAPI, SQLAlchemy, psycopg, httpx, sqlglot, pydantic-settings |
| AI | Ollama with `qwen2.5-coder:7b` |
| Frontend | Next.js, React, TypeScript, Tailwind CSS |

## Project structure

```
database/
  01_schema.sql         tables and constraints
  02_seed.sql           sample store data
  03_test_queries.sql   read-only checks of the sample data
  04_readonly_role.sql  the app_readonly database user
backend/
  app/config.py         reads settings from .env
  app/db.py             database connection and read-only query runner
  app/llm.py            prompts and calls to Ollama
  app/safety.py         the SQL safety checker
  app/main.py           API endpoints (/ask, /explain, ...)
  check_safety.py       tests for the safety checker
  eval_questions.py     scores the AI on 10 known questions
frontend/
  app/page.tsx          the question page
```

## Setup

You need: **PostgreSQL**, **Python 3.11+**, **Node.js 20+** and **Ollama**. Commands below are for Windows PowerShell, run from the project folder.

### 1. Database

```powershell
psql -U postgres -c "CREATE DATABASE store_db;"
psql -U postgres -d store_db -v ON_ERROR_STOP=1 -f database/01_schema.sql
psql -U postgres -d store_db -v ON_ERROR_STOP=1 -f database/02_seed.sql
psql -U postgres -d store_db -v ON_ERROR_STOP=1 -f database/04_readonly_role.sql
```

Then give the app user a password (it is never stored in a file in this repo):

```powershell
psql -U postgres -d store_db
```
```
\password app_readonly
\q
```

Optional check that the data loaded correctly:

```powershell
psql -U postgres -d store_db -v ON_ERROR_STOP=1 -f database/03_test_queries.sql
```

### 2. AI model

Install Ollama from https://ollama.com, then:

```powershell
ollama pull qwen2.5-coder:7b
```

### 3. Backend

If activating the virtual environment fails with "running scripts is disabled", first run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

In `.env`, set `DB_PASSWORD` to the `app_readonly` password. Then start the API:

```powershell
uvicorn app.main:app --reload
```

The API runs at http://127.0.0.1:8000 (interactive docs at `/docs`).

### 4. Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** (use `localhost`, not `127.0.0.1`).

## Tests

From the `backend` folder, with `.venv` active:

```powershell
python check_safety.py     # safety checker: 14 cases, no database or AI needed
python eval_questions.py   # AI accuracy: 10 known questions (needs Ollama and PostgreSQL)
```

Latest result: safety checker 14/14, AI evaluation 10/10.

## Limitations

- The sample database is small (4 tables, about 80 rows). Accuracy on larger or messier schemas will be lower.
- A small local model can still write wrong SQL for questions outside the tested set. The page always shows the SQL that ran and the exact result table, so answers can be checked.
- The AI summary is generated text. The table is the source of truth.
- On a laptop without a dedicated GPU, answers take roughly 5–30 seconds.
- Built for local development only. It is not configured for deployment.
