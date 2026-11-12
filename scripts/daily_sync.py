"""Daily sync: load only papers submitted since the last completed sync, then log the run.

Same logic as azure_function/function_app.py, runnable locally.

Usage:
    python scripts/daily_sync.py

Requires: pyodbc, python-dotenv
"""

import json
import os
import sys
from datetime import date

import pyodbc
from dotenv import load_dotenv

# Add project root to path for tools/ imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from tools.arxiv_search import BACKFILL_START, SEARCH_TOPICS, search_by_title
from tools.azure_sql_queries import build_upsert_query, get_last_sync_date_query

SYNC_LIMIT_PER_TOPIC = 500


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

    cursor.execute(get_last_sync_date_query())
    row = cursor.fetchone()
    from_date = str(row.last_sync_date) if row and row.last_sync_date else BACKFILL_START
    to_date = date.today().isoformat()
    print(f"Sync window: {from_date} -> {to_date}")

    merge_sql = build_upsert_query()
    total = 0
    for topic in SEARCH_TOPICS:
        papers = search_by_title(topic, limit=SYNC_LIMIT_PER_TOPIC, submitted_from=from_date, submitted_to=to_date)
        for p in papers:
            cursor.execute(merge_sql, (
                p["arxiv_id"], p["title"], p["abstract"], p["primary_category"],
                json.dumps(p["authors"]), p["submitted_date"], p["updated_date"],
                json.dumps(p["categories"]), topic, "daily_sync",
            ))
        print(f"  {topic:<25} {len(papers):>4} papers")
        total += len(papers)
    conn.commit()

    cursor.execute(
        "INSERT INTO SYNC_LOG (submitted_from, submitted_to, papers_loaded, search_topics) VALUES (?, ?, ?, ?)",
        (from_date, to_date, total, ", ".join(SEARCH_TOPICS)),
    )
    conn.commit()
    print(f"Daily sync complete: {total} papers merged and logged")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
