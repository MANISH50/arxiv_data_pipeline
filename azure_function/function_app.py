"""Azure Function: Daily arXiv Paper Sync

Timer-triggered function that runs daily at 7:00 AM UTC (midnight MST).
Searches the arXiv API for papers submitted since the last sync and loads
them into Azure SQL Database using MERGE upsert. arXiv needs no API key.

Environment variables (configure in Function App > Application Settings):
    AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USER, AZURE_SQL_PASSWORD
"""

import json
import logging
import os
import time
from datetime import date

import azure.functions as func
import pyodbc

from shared.arxiv_search import BACKFILL_START, SEARCH_TOPICS, search_by_title
from shared.azure_sql_queries import (
    build_upsert_query,
    get_last_sync_date_query,
)

app = func.FunctionApp()

SYNC_LIMIT_PER_TOPIC = 500  # search_by_title pages automatically, 100 papers per call


def _odbc_driver() -> str:
    """Newest SQL Server ODBC driver in the Function image (older images ship 17, newer ones 18)."""
    installed = pyodbc.drivers()
    for name in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"):
        if name in installed:
            return name
    raise RuntimeError(f"No SQL Server ODBC driver found; installed: {installed}")


def _get_connection(retries: int = 3, delay: int = 30) -> pyodbc.Connection:
    """Connect to Azure SQL with retry for cold start (free tier wakes up in ~30-60s)."""
    last_error = None
    for attempt in range(retries):
        try:
            return pyodbc.connect(
                f"DRIVER={{{_odbc_driver()}}};"
                f"SERVER={os.environ['AZURE_SQL_SERVER']};"
                f"DATABASE={os.environ['AZURE_SQL_DATABASE']};"
                f"UID={os.environ['AZURE_SQL_USER']};"
                f"PWD={os.environ['AZURE_SQL_PASSWORD']}"
            )
        except pyodbc.Error as e:
            last_error = e
            if attempt < retries - 1:
                logging.warning(f"DB connection attempt {attempt + 1}/{retries} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
    raise last_error


@app.timer_trigger(schedule="0 0 7 * * *", arg_name="timer", run_on_startup=False)
def daily_paper_sync(timer: func.TimerRequest) -> None:
    """Daily paper sync: search arXiv for new papers and load into Azure SQL."""
    logging.info("Starting daily paper sync")

    conn = _get_connection()
    cursor = conn.cursor()

    # Determine date range: last sync date -> today
    cursor.execute(get_last_sync_date_query())
    row = cursor.fetchone()
    if row and row.last_sync_date:
        from_date = str(row.last_sync_date)
    else:
        from_date = BACKFILL_START

    to_date = date.today().isoformat()
    logging.info(f"Sync range: {from_date} to {to_date}")

    merge_sql = build_upsert_query()
    total_loaded = 0

    for topic in SEARCH_TOPICS:
        results = search_by_title(
            topic,
            limit=SYNC_LIMIT_PER_TOPIC,
            submitted_from=from_date,
            submitted_to=to_date,
        )

        count = 0
        for p in results:
            try:
                params = (
                    p.get("arxiv_id", ""),
                    p.get("title", ""),
                    p.get("abstract", ""),
                    p.get("primary_category", ""),
                    json.dumps(p.get("authors", [])),
                    p.get("submitted_date") or None,
                    p.get("updated_date") or None,
                    json.dumps(p.get("categories", [])),
                    topic,
                    "daily_sync",
                )
                cursor.execute(merge_sql, params)
                count += 1
            except Exception as e:
                logging.error(f"Error loading {p.get('arxiv_id', '?')}: {e}")

        logging.info(f"  {topic}: {count} papers")
        total_loaded += count

    conn.commit()

    # Log the sync
    cursor.execute(
        "INSERT INTO SYNC_LOG (submitted_from, submitted_to, papers_loaded, search_topics) "
        "VALUES (?, ?, ?, ?)",
        (from_date, to_date, total_loaded, ", ".join(SEARCH_TOPICS)),
    )
    conn.commit()

    cursor.close()
    conn.close()

    logging.info(f"Daily sync complete: {total_loaded} papers loaded")
