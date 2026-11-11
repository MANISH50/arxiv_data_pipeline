
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
