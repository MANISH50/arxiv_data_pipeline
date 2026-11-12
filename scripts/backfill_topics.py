"""Backfill every paper for the demo topics submitted since BACKFILL_START.

Walks month-by-month windows per topic (arXiv returns at most ~2000 results per
query slice) and MERGEs each window in one batched round trip.

Usage:
    python scripts/backfill_topics.py

Requires: pyodbc, python-dotenv
"""

import json
import os
import sys
from datetime import date, timedelta

import pyodbc
from dotenv import load_dotenv

# Add project root to path for tools/ imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from tools.arxiv_search import BACKFILL_START, SEARCH_TOPICS, search_by_title
from tools.azure_sql_queries import build_upsert_query

DATE_TO = date.today().isoformat()
WINDOW_LIMIT = 2000  # arXiv's per-query-slice ceiling
LOAD_SOURCE = "backfill"


def month_windows(start: str, end: str) -> list[tuple[str, str]]:
    """(first_day, last_day) for each month from start to end, clipped to end."""
    windows, d, stop = [], date.fromisoformat(start).replace(day=1), date.fromisoformat(end)
    while d <= stop:
        nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        windows.append((max(d, date.fromisoformat(start)).isoformat(), min(nxt - timedelta(days=1), stop).isoformat()))
        d = nxt
    return windows


def get_connection() -> pyodbc.Connection:
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.environ['AZURE_SQL_SERVER']};"
        f"DATABASE={os.environ['AZURE_SQL_DATABASE']};"
        f"UID={os.environ['AZURE_SQL_USER']};"
        f"PWD={os.environ['AZURE_SQL_PASSWORD']};"
        "Connection Timeout=120;"
    )


def main():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.fast_executemany = True  # one round trip per window instead of one per paper
    merge_sql = build_upsert_query()
    windows = month_windows(BACKFILL_START, DATE_TO)
    print(f"Backfill {BACKFILL_START} -> {DATE_TO}: {len(windows)} monthly windows x {len(SEARCH_TOPICS)} topics\n")

    totals, capped = {}, []
    for topic in SEARCH_TOPICS:
        merged = 0
        for start, end in windows:
            papers = search_by_title(topic, limit=WINDOW_LIMIT, submitted_from=start, submitted_to=end)
            if len(papers) >= WINDOW_LIMIT:
                capped.append(f"{topic} {start[:7]}")
            if papers:
                cursor.executemany(merge_sql, [
                    (
                        p["arxiv_id"], p["title"], p["abstract"], p["primary_category"],
                        json.dumps(p["authors"]), p["submitted_date"], p["updated_date"],
                        json.dumps(p["categories"]), topic, LOAD_SOURCE,
                    )
                    for p in papers
                ])
                conn.commit()
                merged += len(papers)
        totals[topic] = merged
        print(f"  {topic:<25} {merged:>5} papers merged")

    cursor.execute("SELECT COUNT(*), MIN(submitted_date), MAX(submitted_date) FROM PAPERS")
    total, lo, hi = cursor.fetchone()
    print(f"\nMERGE operations: {sum(totals.values())} | PAPERS rows: {total} | submitted {lo} -> {hi}")
    print("Windows that hit the 2000 cap (incomplete):", capped or "none")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
