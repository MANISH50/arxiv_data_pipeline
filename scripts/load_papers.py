"""Search three AI & data topics on arXiv (17 + 17 + 16 = 50 papers) and MERGE them into PAPERS.

Usage:
    python scripts/load_papers.py

Requires: pyodbc, python-dotenv
"""

import json
import os
import sys

import pyodbc
from dotenv import load_dotenv

# Add project root to path for tools/ imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from tools.arxiv_search import search_by_title
from tools.azure_sql_queries import build_upsert_query

TOPICS = [("large language models", 17), ("time series forecasting", 17), ("vector database", 16)]
LOAD_SOURCE = "title_search"


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
    # Step 3: search arXiv and merge into one list
    papers = []
    for topic, limit in TOPICS:
        results = search_by_title(topic, limit=limit)
        print(f"  {topic:<25} {len(results):>3} papers")
        papers.extend((topic, p) for p in results)
    print(f"Search total: {len(papers)} papers\n")

    # Step 4: parameterized MERGE upsert (order matches build_upsert_query)
    rows = [
        (
            p["arxiv_id"], p["title"], p["abstract"], p["primary_category"],
            json.dumps(p["authors"]), p["submitted_date"], p["updated_date"],
            json.dumps(p["categories"]), topic, LOAD_SOURCE,
        )
        for topic, p in papers
    ]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(build_upsert_query(), rows)
    conn.commit()

    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT arxiv_id) FROM PAPERS")
    total, distinct = cursor.fetchone()
    print(f"Loaded {len(rows)} rows via MERGE -> PAPERS now has {total} rows ({distinct} distinct ids)\n")

    cursor.execute(
        "SELECT TOP 5 arxiv_id, LEFT(title, 60) AS title, primary_category, submitted_date "
        "FROM PAPERS ORDER BY submitted_date DESC, arxiv_id"
    )
    print("Sample (newest 5):")
    for r in cursor.fetchall():
        print(f"  {r.arxiv_id:<12} {r.primary_category:<8} {r.submitted_date}  {r.title}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
