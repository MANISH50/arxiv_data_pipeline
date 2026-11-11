# AI Agent Instructions: Azure SQL arXiv Paper Intelligence

> IMPORTANT: Everything in this repo is public-facing, so do not place any sensitive info here and make sure to distinguish between what should be internal-facing info (e.g. secrets, PII, recording guides/scripts), and public-facing info (instructions, how-to guides, actual code utilized). If there is information that AI Agent needs across sessions but should not be published, put it in the `.internal/` folder which is ignored by git per the `.gitignore`.

## Project Overview

This is a demo repository for a **KC Labs AI YouTube video** showing how AI Agent integrates with Azure SQL Database to build an AI-powered arXiv research-paper intelligence pipeline.

**Audience**: YouTube viewers — data professionals, AI practitioners, and developers
**Demo Subject**: AI & data processing research-paper analysis using the arXiv API + Azure SQL Database

> **AI Agent**: If `.internal/OWNER_CONFIG.md` exists, read it at the start of each session and use those concrete values (org URLs, resource names, emails) for all commands. This avoids resolving `$ENV_VAR` references or guessing placeholder values.
>
> **Viewers cloning this repo**: Create your own `.internal/OWNER_CONFIG.md` with your personal values (DevOps org, Function App name, resource group, email). See the format in CLAUDE.md's Available Tools section. Then update `.env` with your credentials (see `.env.example`). The pipeline tools, prompts, and SQL patterns all work out of the box.

## Available Tools

### CLI Tools

When calling the cli tools, there may be a pause period of 30 seconds while it wakes back up.

- **sqlcmd**: Connect to Azure SQL Database for DDL and analytical queries
  - Connection: `sqlcmd -S $AZURE_SQL_SERVER -d $AZURE_SQL_DATABASE -U $AZURE_SQL_USER -P $AZURE_SQL_PASSWORD`
  - Login timeout (for free-tier wake-up): add `-l 60` flag
  - CSV output: add `-s "," -W` flags
  - Single query: `-Q "SELECT ..."`
  - Load environment first: `source .env` before running sqlcmd commands
- **Python + pyodbc**: For data loading scripts with parameterized queries
  - Connection string uses `ODBC Driver 18 for SQL Server`
  - Always use parameterized queries (? placeholders) — never string interpolation
  - Load `.env` with `python-dotenv`: `from dotenv import load_dotenv; load_dotenv()`
  - pyodbc connect: `pyodbc.connect(f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={db};UID={user};PWD={pwd}")`
- **az boards** (Azure DevOps): Create and manage work items for ticket-driven workflows
  - Always include `--org "$AZURE_DEVOPS_ORG" --project "$AZURE_DEVOPS_PROJECT"` on every command
  - Create: `az boards work-item create --title "..." --type Task --org "$AZURE_DEVOPS_ORG" --project "$AZURE_DEVOPS_PROJECT"`
  - Transition to Doing (when work starts): `az boards work-item update --id <ID> --state "Doing" --org "$AZURE_DEVOPS_ORG"`
  - Transition to Done (when work completes): `az boards work-item update --id <ID> --state "Done" --org "$AZURE_DEVOPS_ORG"`
  - Add comment: `az boards work-item update --id <ID> --discussion "Summary" --org "$AZURE_DEVOPS_ORG"`
  - Delete: `az boards work-item delete --id <ID> --yes --org "$AZURE_DEVOPS_ORG" --project "$AZURE_DEVOPS_PROJECT"`
  - State lifecycle: `To Do` → `Doing` (start of work) → `Done` (completion)

### Azure Functions (Daily Sync Automation)

- **Function App**: `patent-sync-func` (Consumption plan, Python 3.12) — replace with your own Function App name
- **Resource Group**: `patent-intelligence-rg` — replace with your own resource group
- **Built during demo**: The `azure_function/` directory is created from scratch by AI Agent during the live demo (not pre-built)
- **What to build**: `function_app.py` (timer-triggered), `host.json`, `requirements.txt` (azure-functions, pyodbc), and a `shared/` subdirectory with copies of `arxiv_search.py` and `azure_sql_queries.py`
- **Schedule**: `0 0 7 * * *` (daily at 7:00 AM UTC / midnight MST)
- **Deploy**: `cd azure_function && func azure functionapp publish <your-function-app> --python`
- **View logs**: `func azure functionapp logstream <your-function-app>`
- **Manual trigger**: the Azure CLI has no `function invoke` command. Fetch the host key without printing it, then POST to the admin endpoint (HTTP 202 = accepted): `KEY=$(az functionapp keys list --name <your-function-app> --resource-group <your-rg> --query masterKey -o tsv)` then `curl -X POST -H "x-functions-key: $KEY" -H "Content-Type: application/json" -d '{}' https://<your-function-app>.azurewebsites.net/admin/functions/daily_paper_sync`
- **Important**: `function_app.py` picks the newest installed SQL ODBC driver at runtime (18, else 17) because Consumption images differ. Python 3.10 reached end-of-life on 2026-10-31 and Azure rejects it for new apps, so use 3.12
- **Setup**: See Prerequisites in README.md for creating the Function App and configuring Application Settings

### Python Tools (in tools/ directory)

- **arxiv_search.py**: arXiv API wrapper (export.arxiv.org) — no API key needed
  - `search_by_title("large language models", limit=17)` — primary function for demo
  - `search_by_title("time series forecasting", limit=17)` — second topic
  - `search_by_title("vector database", limit=16)` — third topic
  - All 50 papers merge into the same PAPERS table for cross-topic analysis
  - `search_by_category("cs.DB", limit=100)` — precise search by arXiv category
  - Supports `submitted_from` / `submitted_to` params for date-range filtering
  - Supports `start` param for pagination; a `limit` above 100 pages automatically
  - Throttled to one request every 3 seconds (arXiv terms of use). One query slice returns at most ~2000 results, so use monthly windows for deep backfills
  - `SEARCH_TOPICS` and `BACKFILL_START` are the single source for the demo topics and the backfill start date
- **azure_sql_queries.py**: T-SQL query builders
  - `build_create_table_sql()` — DDL for PAPERS table with indexes
  - `build_upsert_query()` — Parameterized MERGE statement
  - `get_trends_query()` — Submission trends by year
  - `get_top_authors_query()` — Uses CROSS APPLY OPENJSON
  - `get_category_breakdown_query()` — Uses CROSS APPLY OPENJSON
  - `build_create_sync_log_sql()` — DDL for SYNC_LOG table
  - `get_last_sync_date_query()` — Last successful sync date for daily sync

## T-SQL Conventions for This Project

### JSON Handling

- Store JSON arrays as `NVARCHAR(MAX)` (not Snowflake VARIANT)
- Parse with `CROSS APPLY OPENJSON(column_name)` for arrays
- Use `JSON_VALUE(column, '$.key')` for scalar values

### Key T-SQL Patterns

```sql
-- Parse JSON array (authors, categories)
SELECT author.value FROM PAPERS CROSS APPLY OPENJSON(authors) AS author

-- MERGE upsert (must end with semicolon!)
MERGE INTO PAPERS AS target USING (...) AS source ON ... WHEN MATCHED THEN UPDATE ... WHEN NOT MATCHED THEN INSERT ...;

-- Top N results
SELECT TOP 10 ... FROM ... ORDER BY ...

-- Current timestamp
GETDATE()
```

### Things to Remember

- T-SQL MERGE statements MUST end with a semicolon
- Use `NVARCHAR` not `VARCHAR` for Unicode support
- Azure SQL default collation is case-insensitive (no need for ILIKE)
- Use `DATETIME2` instead of `TIMESTAMP` for date/time columns

## Environment Configuration

Connection details are in `.env` file (gitignored). Template at `.env.example`.

Required variables:

- `AZURE_SQL_SERVER` — yourserver.database.windows.net
- `AZURE_SQL_DATABASE` — PatentIntelligence
- `AZURE_SQL_USER` — sqladmin
- `AZURE_SQL_PASSWORD` — your password
- `AZURE_DEVOPS_ORG` — `https://dev.azure.com/your-org` (placeholder — replace with your org URL)
- `AZURE_DEVOPS_PROJECT` — `your-project` (placeholder — replace with your project name)

> **Note**: The four `AZURE_SQL_*` variables must also be configured as Application Settings in the Azure Function App for the daily sync automation. The arXiv API needs no key. Azure resource names (database, resource group, Function App) are just labels — use your own.

## Demo Flow

The demo follows 9 steps in a single prompt:

0. **Create Ticket** — Azure DevOps work item to track the pipeline build
1. **Connect & Discover** — Show empty database
2. **Create Schema** — DDL with indexes
3. **Search arXiv** — API calls for large language models, time series forecasting, and vector database papers
4. **Load Data** — Python pyodbc with MERGE upserts
5. **Analyze** — T-SQL queries with OPENJSON
5b. **Backfill** — All papers submitted since Jan 1, 2025 via date-range API calls
5c. **Daily Sync** — SYNC_LOG table + script to load net-new papers since last sync
5d. **Deploy Function** — `func azure functionapp publish` to deploy daily sync as Azure Function
6. **Visualize** — matplotlib charts
7. **Report** — Markdown executive summary
8. **Close Ticket** — Update work item to Done with summary

## Operating Principles

How AI Agent should reason through tasks — applicable to any data pipeline project.

### Show Your Reasoning

- Announce intent before action — say what you're about to do and why
- Show the actual commands and queries being run — don't execute silently
- Print every T-SQL query as a formatted code block BEFORE executing it, so the presenter can copy-paste it into the Azure Portal Query Editor for visual validation
- All SQL queries are also saved in the `sql/` directory (numbered by step) for reference and portal use
- Explain design choices briefly (one sentence) so the audience understands *why*, not just *what*
- Calibrate depth to your audience — skip basics they already know, lean into domain-specific details
- Example: "Using NVARCHAR(MAX) for JSON columns because Azure SQL stores JSON as strings, not a native JSON type"

### Verify Your Work

- Validate the result of each step before moving to the next — don't assume success
- After creating a table, confirm it exists. After loading data, check the row count. After running queries, sanity-check the results.
- Design for re-runnability: use `IF NOT EXISTS` for DDL, idempotent operations (like MERGE) for data loading
- If results look wrong or empty, flag it immediately — don't silently continue to the next step

### Keep It Reviewable

- Every artifact (DDL, scripts, queries, charts) should be readable by a colleague in under 30 seconds
- Prefer structured output (tables, bullet points) over prose
- Limit result sets to what's meaningful — top 10-15 rows, not full dumps. Summarize raw data into readable form.
- One script per task — no helper files, utility modules, or abstractions for one-off operations
- KISS and YAGNI: build only what's needed now, don't over-engineer, comment only where the logic isn't obvious

### Handle Failures Gracefully

- When a tool fails, explain what happened in one sentence and try the known fallback
- Don't retry the same failing command endlessly — try once, explain, move on
- Prioritize the core workflow — if a non-critical step fails (e.g., ticket tracking), skip it and continue with the primary work

### Protect Sensitive Data

- Never print credentials, API keys, or passwords in terminal output
- Use environment variables for all secrets — never hardcode in scripts
- Reference `$ENV_VARS` in commands instead of literal values

### Track Work End-to-End

- Open a work item at the start to track what's being built. Capture the ID.
- Immediately transition it to `Doing` once work begins.
- Reference the ticket ID when announcing steps so progress is traceable throughout the pipeline
- Close the ticket (state → `Done`) with a summary comment when work is complete
- If ticket tracking is unavailable, note it and continue — don't block the core work

## AI & Data arXiv Categories Reference

| Category | Research Area |
| -------- | ------------- |
| cs.AI | Artificial intelligence |
| cs.LG | Machine learning |
| cs.DB | Databases and data management |
| cs.CL | Computation and language (NLP) |
| cs.IR | Information retrieval |
| cs.CV | Computer vision |
