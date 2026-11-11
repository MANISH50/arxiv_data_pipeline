"""Exhaustive paper collection by arXiv category (cs.AI, cs.DB, cs.LG, ...).

Collects AI & data papers by author-assigned arXiv categories using the arXiv
API. Uses monthly windows so each query stays far below arXiv's ~2000-result
limit per query slice. The search module throttles to one request per 3 seconds.

Usage:
    python scripts/category_backfill.py

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

from tools.arxiv_search import BACKFILL_START, search_by_category
from tools.azure_sql_queries import build_upsert_query

# --- Configuration ---
DATE_FROM = BACKFILL_START
DATE_TO = date.today().isoformat()
MAX_PER_WINDOW = 100  # papers per category per month; 100 = one API call (~3 s). Raise for deeper coverage.
LOAD_SOURCE = "category_collection"

# Categories ordered by AI-specificity (highest priority first).
CATEGORIES = {
    "cs.AI": "Artificial intelligence",
    "cs.LG": "Machine learning",
    "cs.DB": "Databases and data management",
}


def generate_monthly_windows(start_date: str, end_date: str) -> list[tuple[str, str]]:
    """Generate (month_start, month_end) tuples covering the date range."""
    windows = []
    d = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    while d <= end:
        month_start = d.replace(day=1)
        if d.month == 12:
            month_end = date(d.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(d.year, d.month + 1, 1) - timedelta(days=1)
        if month_end > end:
            month_end = end
        windows.append((month_start.isoformat(), month_end.isoformat()))
        # Advance to next month
        if d.month == 12:
            d = date(d.year + 1, 1, 1)
        else:
            d = date(d.year, d.month + 1, 1)

    return windows


def get_connection() -> pyodbc.Connection:
    """Connect to Azure SQL Database."""
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
    merge_sql = build_upsert_query()
    windows = generate_monthly_windows(DATE_FROM, DATE_TO)

    print(f"Category Backfill: {len(windows)} monthly windows x {len(CATEGORIES)} categories")
    print(f"Date range: {DATE_FROM} to {DATE_TO}\n")

    grand_total = 0
    global_seen = set()  # Dedup across categories (papers are often cross-listed)
    category_counts = {}

    for category, description in CATEGORIES.items():
        category_total = 0
        print(f"{'='*60}")
        print(f"arXiv {category}: {description}")
        print(f"{'='*60}")

        for month_start, month_end in windows:
            papers = search_by_category(
                category,
                limit=MAX_PER_WINDOW,
                submitted_from=month_start,
                submitted_to=month_end,
            )

            loaded = 0
            for p in papers:
                pid = p.get("arxiv_id", "")
                if not pid:
                    continue

                global_seen.add(pid)

                params = (
                    pid,
                    p.get("title", ""),
                    p.get("abstract", ""),
                    p.get("primary_category", ""),
                    json.dumps(p.get("authors", [])),
                    p.get("submitted_date") or None,
                    p.get("updated_date") or None,
                    json.dumps(p.get("categories", [])),
                    f"cat:{category}",
                    LOAD_SOURCE,
                )
                try:
                    cursor.execute(merge_sql, params)
                    loaded += 1
                except Exception as e:
                    print(f"    MERGE error {pid}: {e}")

            conn.commit()
            category_total += loaded
            if loaded > 0:
                print(f"  {month_start[:7]}: {loaded} papers")

        grand_total += category_total
        category_counts[category] = category_total
        print(f"  Subtotal: {category_total}\n")

    # Log to SYNC_LOG
    cursor.execute(
        "INSERT INTO SYNC_LOG (submitted_from, submitted_to, "
        "papers_loaded, search_topics, sync_status) "
        "VALUES (?, ?, ?, ?, ?)",
        (DATE_FROM, DATE_TO, grand_total,
         ", ".join(f"cat:{c}" for c in CATEGORIES), "completed"),
    )
    conn.commit()

    # Final summary
    cursor.execute("SELECT COUNT(*) FROM PAPERS")
    total_in_db = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    print(f"{'='*60}")
    print("Category Collection Complete")
    print(f"{'='*60}")
    print(f"  Unique papers seen: {len(global_seen)}")
    print(f"  Total MERGE operations: {grand_total}")
    for code, count in category_counts.items():
        print(f"    cat:{code}: {count}")
    print(f"  Total papers in DB: {total_in_db}")


if __name__ == "__main__":
    main()
