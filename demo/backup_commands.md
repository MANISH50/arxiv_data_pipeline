# Backup Commands

If Claude Code encounters issues during the demo, use these manual commands.

## 0. Create Azure DevOps Work Item

```bash
az boards work-item create \
  --title "Build AI & Data arXiv Paper Intelligence Pipeline" \
  --type Task \
  --description "Build arXiv paper intelligence pipeline: schema creation, arXiv API search, data loading, T-SQL analysis, and visualization." \
  --output table
```

Note the ID from the output for step 8.

## 1. Connect to Azure SQL

```bash
sqlcmd -S $AZURE_SQL_SERVER -d $AZURE_SQL_DATABASE -U $AZURE_SQL_USER -P $AZURE_SQL_PASSWORD -Q "SELECT name FROM sys.tables"
```

## 2. Create PAPERS Table

```bash
sqlcmd -S $AZURE_SQL_SERVER -d $AZURE_SQL_DATABASE -U $AZURE_SQL_USER -P $AZURE_SQL_PASSWORD -Q "
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'PAPERS')
CREATE TABLE PAPERS (
    arxiv_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    title NVARCHAR(1000),
    abstract NVARCHAR(MAX),
    primary_category NVARCHAR(100),
    authors NVARCHAR(MAX),
    submitted_date DATE,
    updated_date DATE,
    categories NVARCHAR(MAX),
    search_query NVARCHAR(200),
    load_source NVARCHAR(100),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
CREATE INDEX IX_PAPERS_PRIMARY_CATEGORY ON PAPERS (primary_category);
CREATE INDEX IX_PAPERS_SUBMITTED_DATE ON PAPERS (submitted_date);
"
```

## 3. Search arXiv API (Python)

```bash
python3 -c "
from tools.arxiv_search import search_by_title
import json

results_llm = search_by_title('large language models', limit=17)
results_ts = search_by_title('time series forecasting', limit=17)
results_vdb = search_by_title('vector database', limit=16)
all_results = results_llm + results_ts + results_vdb

print(f'Found {len(all_results)} papers total')
print(f'  Large language models: {len(results_llm)}')
print(f'  Time series forecasting: {len(results_ts)}')
print(f'  Vector database: {len(results_vdb)}')
for p in all_results[:5]:
    print(f'  - {p[\"arxiv_id\"]}: {p[\"title\"][:60]}...')
"
```

arXiv needs no API key. The search module waits 3 seconds between calls (arXiv's rate rule), so this takes about 10 seconds.

## 4. Load Data (Python with pyodbc)

```bash
python3 -c "
import os, json, pyodbc
from dotenv import load_dotenv
from tools.arxiv_search import search_by_title

load_dotenv()
conn_str = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={os.getenv(\"AZURE_SQL_SERVER\")};'
    f'DATABASE={os.getenv(\"AZURE_SQL_DATABASE\")};'
    f'UID={os.getenv(\"AZURE_SQL_USER\")};'
    f'PWD={os.getenv(\"AZURE_SQL_PASSWORD\")};'
    f'Encrypt=yes;TrustServerCertificate=no;'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Search three AI & data topics
topics = [
    ('large language models', 17),
    ('time series forecasting', 17),
    ('vector database', 16),
]
all_papers = []
for topic, limit in topics:
    results = search_by_title(topic, limit=limit)
    for p in results:
        p['search_query'] = topic
        p['load_source'] = 'title_search'
    all_papers.extend(results)

merge_sql = '''
MERGE INTO PAPERS AS target
USING (SELECT ? AS arxiv_id, ? AS title, ? AS abstract, ? AS primary_category,
       ? AS authors, ? AS submitted_date, ? AS updated_date, ? AS categories,
       ? AS search_query, ? AS load_source) AS source
ON target.arxiv_id = source.arxiv_id
WHEN MATCHED THEN UPDATE SET title=source.title, abstract=source.abstract,
    primary_category=source.primary_category, authors=source.authors,
    submitted_date=source.submitted_date, updated_date=source.updated_date,
    categories=source.categories, search_query=source.search_query,
    load_source=source.load_source, updated_at=GETDATE()
WHEN NOT MATCHED THEN INSERT (arxiv_id, title, abstract, primary_category, authors,
    submitted_date, updated_date, categories, search_query, load_source, created_at, updated_at)
VALUES (source.arxiv_id, source.title, source.abstract, source.primary_category,
    source.authors, source.submitted_date, source.updated_date, source.categories,
    source.search_query, source.load_source, GETDATE(), GETDATE());
'''

for p in all_papers:
    cursor.execute(merge_sql, (
        p['arxiv_id'], p['title'], p.get('abstract', ''), p['primary_category'],
        json.dumps(p.get('authors', [])), p.get('submitted_date'),
        p.get('updated_date'), json.dumps(p.get('categories', [])),
        p.get('search_query', ''), p.get('load_source', 'title_search')
    ))

conn.commit()
print(f'Loaded {len(all_papers)} papers')
conn.close()
"
```

## 5. Analytical Queries

### Paper Count and Date Range
```bash
sqlcmd -S $AZURE_SQL_SERVER -d $AZURE_SQL_DATABASE -U $AZURE_SQL_USER -P $AZURE_SQL_PASSWORD -Q "
SELECT COUNT(*) AS total_papers, MIN(submitted_date) AS earliest, MAX(submitted_date) AS latest
FROM PAPERS;
"
```

### Submission Trends by Year
```bash
sqlcmd -S $AZURE_SQL_SERVER -d $AZURE_SQL_DATABASE -U $AZURE_SQL_USER -P $AZURE_SQL_PASSWORD -Q "
SELECT YEAR(submitted_date) AS year, COUNT(*) AS papers
FROM PAPERS WHERE submitted_date IS NOT NULL
GROUP BY YEAR(submitted_date) ORDER BY year;
"
```

### Top Authors (OPENJSON)
```bash
sqlcmd -S $AZURE_SQL_SERVER -d $AZURE_SQL_DATABASE -U $AZURE_SQL_USER -P $AZURE_SQL_PASSWORD -Q "
SELECT TOP 10 author.value AS author, COUNT(*) AS papers
FROM PAPERS CROSS APPLY OPENJSON(authors) AS author
GROUP BY author.value ORDER BY papers DESC;
"
```

### arXiv Category Breakdown (OPENJSON)
```bash
sqlcmd -S $AZURE_SQL_SERVER -d $AZURE_SQL_DATABASE -U $AZURE_SQL_USER -P $AZURE_SQL_PASSWORD -Q "
SELECT TOP 10 cat.value AS arxiv_category, COUNT(*) AS papers
FROM PAPERS CROSS APPLY OPENJSON(categories) AS cat
GROUP BY cat.value ORDER BY papers DESC;
"
```

## 5b. Backfill Papers Since January 1, 2025

```bash
python3 -c "
import os, json, pyodbc
from dotenv import load_dotenv
from tools.arxiv_search import search_by_title, SEARCH_TOPICS, BACKFILL_START

load_dotenv()
conn_str = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={os.getenv(\"AZURE_SQL_SERVER\")};'
    f'DATABASE={os.getenv(\"AZURE_SQL_DATABASE\")};'
    f'UID={os.getenv(\"AZURE_SQL_USER\")};'
    f'PWD={os.getenv(\"AZURE_SQL_PASSWORD\")};'
    f'Encrypt=yes;TrustServerCertificate=no;'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

merge_sql = '''
MERGE INTO PAPERS AS target
USING (SELECT ? AS arxiv_id, ? AS title, ? AS abstract, ? AS primary_category,
       ? AS authors, ? AS submitted_date, ? AS updated_date, ? AS categories,
       ? AS search_query, ? AS load_source) AS source
ON target.arxiv_id = source.arxiv_id
WHEN MATCHED THEN UPDATE SET title=source.title, abstract=source.abstract,
    primary_category=source.primary_category, authors=source.authors,
    submitted_date=source.submitted_date, updated_date=source.updated_date,
    categories=source.categories, updated_at=GETDATE()
WHEN NOT MATCHED THEN INSERT (arxiv_id, title, abstract, primary_category, authors,
    submitted_date, updated_date, categories, search_query, load_source, created_at, updated_at)
VALUES (source.arxiv_id, source.title, source.abstract, source.primary_category,
    source.authors, source.submitted_date, source.updated_date, source.categories,
    source.search_query, source.load_source, GETDATE(), GETDATE());
'''

total = 0
for topic in SEARCH_TOPICS:
    # search_by_title pages automatically (100 papers per call, 3 s apart)
    batch = search_by_title(topic, limit=500, submitted_from=BACKFILL_START)
    for p in batch:
        cursor.execute(merge_sql, (
            p['arxiv_id'], p['title'], p.get('abstract', ''), p['primary_category'],
            json.dumps(p.get('authors', [])), p.get('submitted_date'),
            p.get('updated_date'), json.dumps(p.get('categories', [])),
            topic, 'backfill'
        ))
    conn.commit()
    total += len(batch)

print(f'Backfill complete: {total} papers loaded since {BACKFILL_START}')
conn.close()
"
```

For a deeper, category-based collection (cs.AI, cs.LG, cs.DB by month), run `python3 scripts/category_backfill.py`.

## 5c. Daily Sync — Create SYNC_LOG Table and Run Sync

```bash
# Create SYNC_LOG table
sqlcmd -S $AZURE_SQL_SERVER -d $AZURE_SQL_DATABASE -U $AZURE_SQL_USER -P $AZURE_SQL_PASSWORD -Q "
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
"
```

```bash
# Run daily sync
python3 -c "
import os, json, pyodbc
from datetime import date
from dotenv import load_dotenv
from tools.arxiv_search import search_by_title, SEARCH_TOPICS, BACKFILL_START

load_dotenv()
conn_str = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={os.getenv(\"AZURE_SQL_SERVER\")};'
    f'DATABASE={os.getenv(\"AZURE_SQL_DATABASE\")};'
    f'UID={os.getenv(\"AZURE_SQL_USER\")};'
    f'PWD={os.getenv(\"AZURE_SQL_PASSWORD\")};'
    f'Encrypt=yes;TrustServerCertificate=no;'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Get last sync date
cursor.execute('''
    SELECT TOP 1 submitted_to FROM SYNC_LOG
    WHERE sync_status = \'completed\' ORDER BY sync_date DESC
''')
row = cursor.fetchone()
last_date = str(row[0]) if row else BACKFILL_START
today = str(date.today())

merge_sql = '''
MERGE INTO PAPERS AS target
USING (SELECT ? AS arxiv_id, ? AS title, ? AS abstract, ? AS primary_category,
       ? AS authors, ? AS submitted_date, ? AS updated_date, ? AS categories,
       ? AS search_query, ? AS load_source) AS source
ON target.arxiv_id = source.arxiv_id
WHEN MATCHED THEN UPDATE SET title=source.title, abstract=source.abstract,
    primary_category=source.primary_category, authors=source.authors,
    submitted_date=source.submitted_date, updated_date=source.updated_date,
    categories=source.categories, updated_at=GETDATE()
WHEN NOT MATCHED THEN INSERT (arxiv_id, title, abstract, primary_category, authors,
    submitted_date, updated_date, categories, search_query, load_source, created_at, updated_at)
VALUES (source.arxiv_id, source.title, source.abstract, source.primary_category,
    source.authors, source.submitted_date, source.updated_date, source.categories,
    source.search_query, source.load_source, GETDATE(), GETDATE());
'''

total = 0
for topic in SEARCH_TOPICS:
    results = search_by_title(topic, limit=500, submitted_from=last_date, submitted_to=today)
    for p in results:
        cursor.execute(merge_sql, (
            p['arxiv_id'], p['title'], p.get('abstract', ''), p['primary_category'],
            json.dumps(p.get('authors', [])), p.get('submitted_date'),
            p.get('updated_date'), json.dumps(p.get('categories', [])),
            topic, 'daily_sync'
        ))
    total += len(results)

conn.commit()
cursor.execute('''
    INSERT INTO SYNC_LOG (submitted_from, submitted_to, papers_loaded, search_topics)
    VALUES (?, ?, ?, ?)
''', (last_date, today, total, ', '.join(SEARCH_TOPICS)))
conn.commit()
print(f'Daily sync complete: {total} papers loaded ({last_date} to {today})')
conn.close()
"
```

## 5d. Create & Deploy Azure Function

> The `azure_function/` directory is built from scratch by Claude Code during the live demo.
> If you need to create it manually, it should contain: `function_app.py` (timer trigger),
> `host.json`, `requirements.txt`, and `shared/` (with `arxiv_search.py` and `azure_sql_queries.py`).
> arXiv needs no API key, so the Function App only needs the four Azure SQL settings.

```bash
# Deploy the daily sync function to Azure
cd azure_function && func azure functionapp publish patent-sync-func --python
```

```bash
# Verify the function is registered
az functionapp function show \
  --name patent-sync-func \
  --resource-group patent-intelligence-rg \
  --function-name daily_paper_sync \
  --output table
```

```bash
# (Optional) Manually trigger the function to test (HTTP 202 = accepted; do not print the key)
KEY=$(az functionapp keys list --name patent-sync-func --resource-group patent-intelligence-rg --query masterKey -o tsv)
curl -X POST -H "x-functions-key: $KEY" -H "Content-Type: application/json" -d '{}' \
  https://patent-sync-func.azurewebsites.net/admin/functions/daily_paper_sync
```

```bash
# (Optional) Stream live logs
func azure functionapp logstream patent-sync-func
```

## 8. Close Azure DevOps Work Item

```bash
# Replace <ID> with the work item ID from step 0
az boards work-item update \
  --id <ID> \
  --state Done \
  --discussion "Pipeline complete: PAPERS table created with indexes, AI & data papers loaded via MERGE upserts across 3 topics, analysis run with OPENJSON, matplotlib visualizations generated, executive summary produced." \
  --output table
```

## 9. Cleanup (after demo)

```bash
sqlcmd -S $AZURE_SQL_SERVER -d $AZURE_SQL_DATABASE -U $AZURE_SQL_USER -P $AZURE_SQL_PASSWORD -Q "DROP TABLE IF EXISTS PAPERS;"
```
