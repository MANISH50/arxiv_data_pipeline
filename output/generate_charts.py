"""Generate arXiv paper analysis charts from Azure SQL data.

Connects to Azure SQL Database, runs analytical queries, and produces
matplotlib charts saved to the output/ directory.

Usage:
    python output/generate_charts.py

Requires: matplotlib, pyodbc, python-dotenv
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pyodbc
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def get_connection() -> pyodbc.Connection:
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.environ['AZURE_SQL_SERVER']};"
        f"DATABASE={os.environ['AZURE_SQL_DATABASE']};"
        f"UID={os.environ['AZURE_SQL_USER']};"
        f"PWD={os.environ['AZURE_SQL_PASSWORD']};"
        "Connection Timeout=120;"
    )


def generate_submission_trends(cursor):
    """Bar chart of paper submission counts by month."""
    cursor.execute("""
        SELECT FORMAT(submitted_date, 'yyyy-MM') AS submission_month, COUNT(*) AS cnt
        FROM PAPERS WHERE submitted_date IS NOT NULL
        GROUP BY FORMAT(submitted_date, 'yyyy-MM')
        ORDER BY submission_month
    """)
    rows = cursor.fetchall()
    months = [r[0] for r in rows]
    counts = [r[1] for r in rows]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(months, counts, color="#2563eb", edgecolor="white")
    ax.set_xlabel("Submission Month", fontsize=12)
    ax.set_ylabel("Paper Count", fontsize=12)
    title = "AI & Data arXiv Paper Submission Trends"
    if months:
        title += f" ({months[0][:4]}-{months[-1][:4]})" if months[0][:4] != months[-1][:4] else f" ({months[0][:4]})"
    ax.set_title(title, fontsize=14, fontweight="bold")
    plt.xticks(rotation=45, ha="right")
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + 1,
            str(count),
            ha="center",
            va="bottom",
            fontsize=9,
        )
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "submission_trends.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


def generate_category_breakdown(cursor):
    """Horizontal bar chart of top 10 arXiv categories."""
    cursor.execute("""
        SELECT TOP 10 cat.value AS arxiv_category, COUNT(*) AS paper_count
        FROM PAPERS CROSS APPLY OPENJSON(categories) AS cat
        GROUP BY cat.value
        ORDER BY paper_count DESC
    """)
    rows = cursor.fetchall()
    category_labels = [r[0] for r in rows]
    category_counts = [r[1] for r in rows]

    # Category descriptions for readability
    category_desc = {
        "cs.AI": "Artificial Intelligence",
        "cs.LG": "Machine Learning",
        "cs.DB": "Databases",
        "cs.CL": "Computation & Language",
        "cs.CV": "Computer Vision",
        "cs.IR": "Information Retrieval",
        "cs.DC": "Distributed Computing",
        "cs.SE": "Software Engineering",
        "cs.CR": "Cryptography & Security",
        "stat.ML": "Machine Learning (Statistics)",
    }
    labels = [f"{c}\n{category_desc.get(c, '')}" for c in category_labels]

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.Set3(range(len(category_labels)))
    bars = ax.barh(labels[::-1], category_counts[::-1], color=colors[::-1], edgecolor="white")
    ax.set_xlabel("Paper Count", fontsize=12)
    ax.set_title("Top 10 Research Categories (arXiv)", fontsize=14, fontweight="bold")
    for bar, count in zip(bars, category_counts[::-1]):
        ax.text(
            bar.get_width() + 5,
            bar.get_y() + bar.get_height() / 2.0,
            str(count),
            ha="left",
            va="center",
            fontsize=9,
        )
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "category_breakdown.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


if __name__ == "__main__":
    conn = get_connection()
    cursor = conn.cursor()

    generate_submission_trends(cursor)
    generate_category_breakdown(cursor)

    cursor.close()
    conn.close()
    print("Done.")
