"use client";

import { useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type AskResult = {
  question: string;
  sql: string;
  columns: string[];
  rows: unknown[][];
  row_count: number;
};

type ApiError = {
  message: string;
  reason?: string;
  sql?: string;
};

const EXAMPLES = [
  "What is the total revenue?",
  "Who are the top 5 customers by revenue?",
  "What is the revenue for each month?",
  "Which product has never been sold?",
];

function readError(detail: unknown): ApiError {
  if (typeof detail === "string") return { message: detail };
  if (Array.isArray(detail)) {
    return { message: "Please enter a question between 3 and 500 characters." };
  }
  if (detail && typeof detail === "object") {
    const d = detail as { error?: string; reason?: string; sql?: string };
    return {
      message: d.error ?? "Something went wrong.",
      reason: d.reason,
      sql: d.sql,
    };
  }
  return { message: "Something went wrong." };
}

const MONEY_WORDS = ["revenue", "price", "amount", "sales", "spent", "cost"];
const PLAIN_WORDS = ["year", "month"];

function formatCell(value: unknown, column: string): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    const col = column.toLowerCase();
    if (col === "id" || col.endsWith("_id")) {
      return String(value);
    }
    if (MONEY_WORDS.some((w) => col.includes(w))) {
      return value.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    }
    if (PLAIN_WORDS.some((w) => col.includes(w))) {
      return String(value);
    }
    return value.toLocaleString();
  }
  return String(value);
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResult | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [summarizing, setSummarizing] = useState(false);
  const requestId = useRef(0);

  async function explain(id: number, q: string, data: AskResult) {
    setSummarizing(true);
    try {
      const res = await fetch(`${API_URL}/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: q,
          columns: data.columns,
          rows: data.rows,
        }),
      });
      if (!res.ok) return;
      const body = await res.json();
      if (id === requestId.current) setSummary(body.answer);
    } catch {
      // The summary is optional; the table is still shown.
    } finally {
      if (id === requestId.current) setSummarizing(false);
    }
  }

  async function ask(q: string) {
    const trimmed = q.trim();
    if (trimmed.length < 3 || loading) return;

    const id = ++requestId.current;
    setLoading(true);
    setResult(null);
    setError(null);
    setSummary(null);
    setSummarizing(false);

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(readError(data.detail));
      } else {
        setResult(data as AskResult);
        explain(id, trimmed, data as AskResult);
      }
    } catch {
      setError({
        message:
          "Could not get a response from the backend. Is it running on port 8000?",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-3xl font-bold">Ask your store database</h1>
      <p className="mt-2 opacity-70">
        Type a question in plain English. A local AI writes the SQL, a safety
        checker approves it, and it runs read-only.
      </p>

      <form
        className="mt-6 flex flex-col gap-3 sm:flex-row"
        onSubmit={(e) => {
          e.preventDefault();
          ask(question);
        }}
      >
        <input
          className="flex-1 rounded-lg border border-black/20 bg-transparent px-4 py-2 dark:border-white/20"
          placeholder="e.g. Who are the top 5 customers by revenue?"
          value={question}
          maxLength={500}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading || question.trim().length < 3}
          className="rounded-lg bg-blue-600 px-5 py-2 font-medium text-white disabled:opacity-50"
        >
          {loading ? "Thinking…" : "Ask"}
        </button>
      </form>

      <div className="mt-3 flex flex-wrap gap-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            type="button"
            disabled={loading}
            onClick={() => {
              setQuestion(ex);
              ask(ex);
            }}
            className="rounded-full border border-black/15 px-3 py-1 text-sm hover:bg-black/5 disabled:opacity-50 dark:border-white/20 dark:hover:bg-white/10"
          >
            {ex}
          </button>
        ))}
      </div>

      {loading && (
        <p className="mt-6 opacity-70">
          The AI is writing SQL… this can take up to a minute on this laptop.
        </p>
      )}

      {error && (
        <div className="mt-6 rounded-lg border border-red-500/40 bg-red-500/10 p-4">
          <p className="font-medium text-red-600 dark:text-red-400">
            {error.message}
          </p>
          {error.reason && <p className="mt-1 text-sm">{error.reason}</p>}
          {error.sql && (
            <pre className="mt-3 overflow-x-auto rounded bg-black/5 p-3 text-sm dark:bg-white/10">
              {error.sql}
            </pre>
          )}
        </div>
      )}

      {result && (
        <section className="mt-6">
          {(summarizing || summary) && (
            <div className="mb-6 rounded-lg border border-blue-500/30 bg-blue-500/10 p-4">
              <h2 className="text-sm font-semibold uppercase opacity-60">
                AI summary
              </h2>
              <p className="mt-1">
                {summarizing ? "Writing a short summary…" : summary}
              </p>
              {!summarizing && (
                <p className="mt-2 text-xs opacity-60">
                  Written by AI. The table below is the exact answer from the
                  database.
                </p>
              )}
            </div>
          )}
          <h2 className="text-sm font-semibold uppercase opacity-60">
            SQL that ran
          </h2>
          <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-lg bg-black/5 p-3 text-sm dark:bg-white/10">
            {result.sql}
          </pre>

          <h2 className="mt-6 text-sm font-semibold uppercase opacity-60">
            Answer ({result.row_count} {result.row_count === 1 ? "row" : "rows"}
            {result.row_count === 100 ? ", limit reached" : ""})
          </h2>

          {result.row_count === 0 ? (
            <p className="mt-2 opacity-70">No rows matched.</p>
          ) : (
            <div className="mt-2 overflow-x-auto rounded-lg border border-black/10 dark:border-white/15">
              <table className="w-full text-left text-sm">
                <thead className="bg-black/5 dark:bg-white/10">
                  <tr>
                    {result.columns.map((col) => (
                      <th key={col} className="px-3 py-2 font-semibold">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.rows.map((row, i) => (
                    <tr
                      key={i}
                      className="border-t border-black/10 dark:border-white/10"
                    >
                      {row.map((cell, j) => (
                        <td key={j} className="px-3 py-2">
                          {formatCell(cell, result.columns[j])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
