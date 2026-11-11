"""Azure SQL (T-SQL) query builders for arXiv paper data.

This module provides functions to generate T-SQL queries for:
- Creating the PAPERS table with proper indexes
- Upserting paper records using MERGE
- Analyzing submission trends, authors, and arXiv categories
- JSON handling via OPENJSON and CROSS APPLY

Key T-SQL adaptations from Snowflake:
    Snowflake VARIANT     -> NVARCHAR(MAX) (JSON as string)
    PARSE_JSON()          -> N/A (store as string, query with OPENJSON())
    ILIKE                 -> LIKE (Azure SQL default collation is case-insensitive)
    CURRENT_TIMESTAMP()   -> GETDATE()
    LIMIT N               -> TOP N
    TIMESTAMP             -> DATETIME2
"""


def build_create_table_sql() -> str:
    """Generate T-SQL CREATE TABLE statement for PAPERS table.

    Returns:
        T-SQL DDL string with table creation and index statements
    """
    return """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'PAPERS')
CREATE TABLE PAPERS (
    arxiv_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    title NVARCHAR(1000),
    abstract NVARCHAR(MAX),
    primary_category NVARCHAR(100),
    authors NVARCHAR(MAX),         -- JSON array stored as string
    submitted_date DATE,           -- first version submitted to arXiv
    updated_date DATE,             -- latest arXiv revision (not the row timestamp)
    categories NVARCHAR(MAX),      -- JSON array stored as string
    search_query NVARCHAR(200),
    load_source NVARCHAR(100),     -- how the row was loaded: title_search / backfill / daily_sync / category_collection
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);

-- Indexes for common query patterns
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_PAPERS_PRIMARY_CATEGORY')
    CREATE INDEX IX_PAPERS_PRIMARY_CATEGORY ON PAPERS (primary_category);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_PAPERS_SUBMITTED_DATE')
    CREATE INDEX IX_PAPERS_SUBMITTED_DATE ON PAPERS (submitted_date);
"""


def build_upsert_query() -> str:
    """Generate T-SQL MERGE template for upserting paper records.

    This returns a parameterized MERGE statement for use with pyodbc.
    Parameters are passed via ? placeholders, in this order:
    arxiv_id, title, abstract, primary_category, authors, submitted_date,
    updated_date, categories, search_query, load_source.

    Returns:
        T-SQL MERGE statement with parameter placeholders
    """
    return """
MERGE INTO PAPERS AS target
USING (SELECT
    ? AS arxiv_id,
    ? AS title,
    ? AS abstract,
    ? AS primary_category,
    ? AS authors,
    ? AS submitted_date,
    ? AS updated_date,
    ? AS categories,
    ? AS search_query,
    ? AS load_source
) AS source
ON target.arxiv_id = source.arxiv_id
WHEN MATCHED THEN UPDATE SET
    title = source.title,
    abstract = source.abstract,
    primary_category = source.primary_category,
    authors = source.authors,
    submitted_date = source.submitted_date,
    updated_date = source.updated_date,
    categories = source.categories,
    search_query = source.search_query,
    load_source = source.load_source,
    updated_at = GETDATE()
WHEN NOT MATCHED THEN INSERT (
    arxiv_id, title, abstract, primary_category, authors,
    submitted_date, updated_date, categories, search_query, load_source,
    created_at, updated_at
) VALUES (
    source.arxiv_id, source.title, source.abstract, source.primary_category,
    source.authors, source.submitted_date, source.updated_date, source.categories,
    source.search_query, source.load_source, GETDATE(), GETDATE()
);
"""


def get_paper_count_query() -> str:
    """Query to get total paper count and date range.

    Returns:
        T-SQL query string
    """
    return """
SELECT
    COUNT(*) AS total_papers,
    MIN(submitted_date) AS earliest_submission,
    MAX(submitted_date) AS latest_submission,
    COUNT(DISTINCT primary_category) AS unique_primary_categories
FROM PAPERS;
"""


def get_trends_query() -> str:
    """Query for paper submission trends by year.

    Returns:
        T-SQL query string
    """
    return """
SELECT
    YEAR(submitted_date) AS submission_year,
    COUNT(*) AS paper_count
FROM PAPERS
WHERE submitted_date IS NOT NULL
GROUP BY YEAR(submitted_date)
ORDER BY submission_year;
"""


def get_top_authors_query(top_n: int = 10) -> str:
    """Query for most prolific authors using OPENJSON to parse JSON array.

    Args:
        top_n: Number of top authors to return

    Returns:
        T-SQL query string using CROSS APPLY OPENJSON
    """
    return f"""
SELECT TOP {top_n}
    author.value AS author_name,
    COUNT(*) AS paper_count
FROM PAPERS
CROSS APPLY OPENJSON(authors) AS author
GROUP BY author.value
ORDER BY paper_count DESC;
"""


def get_category_breakdown_query(top_n: int = 10) -> str:
    """Query for arXiv category breakdown using OPENJSON.

    Args:
        top_n: Number of top categories to return

    Returns:
        T-SQL query string using CROSS APPLY OPENJSON
    """
    return f"""
SELECT TOP {top_n}
    cat.value AS arxiv_category,
    COUNT(*) AS paper_count
FROM PAPERS
CROSS APPLY OPENJSON(categories) AS cat
GROUP BY cat.value
ORDER BY paper_count DESC;
"""


def get_primary_category_comparison_query() -> str:
    """Query to compare paper activity across primary categories.

    Returns:
        T-SQL query string
    """
    return """
SELECT
    primary_category,
    COUNT(*) AS total_papers,
    MIN(submitted_date) AS earliest_submission,
    MAX(submitted_date) AS latest_submission,
    COUNT(DISTINCT YEAR(submitted_date)) AS active_years
FROM PAPERS
GROUP BY primary_category
ORDER BY total_papers DESC;
"""


def build_create_sync_log_sql() -> str:
    """Generate T-SQL CREATE TABLE statement for SYNC_LOG table.

    Tracks daily sync runs: when they happened, what submission-date range was
    covered, how many papers were loaded, and which topics were searched.

    Returns:
        T-SQL DDL string with table creation
    """
    return """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SYNC_LOG')
CREATE TABLE SYNC_LOG (
    sync_id INT IDENTITY(1,1) PRIMARY KEY,
    sync_date DATETIME2 DEFAULT GETDATE(),
    submitted_from DATE,
    submitted_to DATE,
    papers_loaded INT,
    search_topics NVARCHAR(500),
    sync_status NVARCHAR(50) DEFAULT 'completed'
);
"""


def get_last_sync_date_query() -> str:
    """Query to get the last successful sync date.

    Returns the most recent submitted_to from a completed sync,
    used as the starting point for the next daily sync run.

    Returns:
        T-SQL query string
    """
    return """
SELECT TOP 1
    submitted_to AS last_sync_date,
    sync_date,
    papers_loaded
FROM SYNC_LOG
WHERE sync_status = 'completed'
ORDER BY sync_date DESC;
"""
