"""Azure SQL arXiv Intelligence tools.

This module exports the public API for arXiv paper search, Azure SQL query
builders, and analysis workflow functions.
"""

from tools.arxiv_search import (
    search_by_title,
    search_by_category,
    get_paper,
)

from tools.azure_sql_queries import (
    build_create_table_sql,
    build_upsert_query,
    get_trends_query,
    get_top_authors_query,
    get_category_breakdown_query,
    build_create_sync_log_sql,
    get_last_sync_date_query,
)

# AI & Data arXiv categories (most relevant research areas)
AI_DATA_ARXIV_CATEGORIES = {
    "cs.AI": "Artificial intelligence",
    "cs.LG": "Machine learning",
    "cs.DB": "Databases and data management",
    "cs.CL": "Computation and language (NLP)",
    "cs.IR": "Information retrieval",
}

__all__ = [
    # arXiv search functions
    "search_by_title",
    "search_by_category",
    "get_paper",
    # Azure SQL query builders
    "build_create_table_sql",
    "build_upsert_query",
    "get_trends_query",
    "get_top_authors_query",
    "get_category_breakdown_query",
    "build_create_sync_log_sql",
    "get_last_sync_date_query",
    # Constants
    "AI_DATA_ARXIV_CATEGORIES",
]
