# Progress

**Last updated:** 2026-11-12
**Status:** paused partway through the demo pipeline run, at Step 5 (backfill), on purpose.

Account-specific values (server, database, resource group, Function App, DevOps org, ticket ID) are **not** in this public file. They are in `.internal/OWNER_CONFIG.md`, and credentials are in `.env`. Neither is in git, so copy both to the new machine yourself (see "Move to a new machine").

## Pipeline run status

The run follows `demo/demo_prompt.md` (Prompt 1). The data source is the arXiv API (no key needed); see `.planning/ARXIV_MIGRATION.md`.

| Step | State | Details |
|---|---|---|
| 0. Create ticket | Done | Azure DevOps Task "Build AI & Data arXiv Paper Intelligence Pipeline" created and set to **Doing** (ID in OWNER_CONFIG) |
| 1. Connect and discover | Done | Previous run's tables archived by rename (nothing deleted): `PAPERS_ARCHIVE_20261111` (7,046 rows) and `SYNC_LOG_ARCHIVE_20261111` (4 rows); their indexes renamed to `IX_PAPERS_ARCHIVE_*` |
| 2. Create schema | Done | New `PAPERS` with PK `arxiv_id` and indexes `IX_PAPERS_PRIMARY_CATEGORY` and `IX_PAPERS_SUBMITTED_DATE` (`sql/01_create_papers_table.sql`) |
| 3–4. Search and load | Done | 50 papers (17/17/16) loaded via `scripts/load_papers.py` |
| 5. Backfill | **Paused, partial** | `scripts/backfill_topics.py` was stopped after its first window: 273 "large language models" papers for 2025-01 are loaded. Re-running it from the start is safe (MERGE, no duplicates) |
| 6. Daily sync | Not started | `scripts/daily_sync.py` is written but has not run. **The new `SYNC_LOG` table does not exist yet** |
| 7. Deploy Function | Not started | Timer changed locally to `0 0 7 * * *` but **not deployed**; the live Function still runs at 07:31 UTC |
| 8. Analyze | Not started | `sql/03`–`06` exist and match the prompt |
| 9. Visualize | Not started | `output/generate_charts.py` |
| 10. Report | Not started | Planned file: `output/executive_summary.md` |
| 11. Close ticket | Not started | Move the ticket to Done with a summary comment |

Database snapshot at pause:

| Table | Rows |
|---|---|
| `PAPERS` | 323 (50 `title_search` + 273 `backfill`) |
| `PAPERS_ARCHIVE_20261111` | 7,046 |
| `SYNC_LOG_ARCHIVE_20261111` | 4 |
| `SYNC_LOG` | does not exist |

> **While paused:** the deployed Function's next timer run will fail with "Invalid object name SYNC_LOG", because the table is still archived. This is harmless, and finishing Step 6 fixes it.

## Repo state

- **Branch:** `feat/arxiv-data-source`. The last pushed commit is `e6124a1` on your fork remote (`fork`). `origin` is the upstream author's repo and rejects pushes.
- **Not yet committed:** `scripts/load_papers.py`, `scripts/backfill_topics.py`, `scripts/daily_sync.py`, `Progress.md`, the timer change in `azure_function/function_app.py`, and `CLAUDE.md`.
  **Commit and push them before switching machines**, or the new machine won't have them.

## Move to a new machine

1. **Code:** clone your fork, then `git checkout feat/arxiv-data-source`.
2. **Private files (not in git):** copy `.env` and the whole `.internal/` folder over a secure channel, and never commit them. If `.env` can't be copied, run `cp .env.example .env` and fill in the `AZURE_SQL_*` and `AZURE_DEVOPS_*` values. Use the names in `.internal/OWNER_CONFIG.md`; the password comes from your password manager.
3. **Tools:**
   - Windows: `winget install Python.Python.3.12 Microsoft.msodbcsql.18 Microsoft.Sqlcmd Microsoft.AzureCLI Microsoft.Azure.FunctionsCoreTools`
   - macOS: `brew install python@3.12 sqlcmd azure-cli azure-functions-core-tools@4` plus the Microsoft ODBC Driver 18
   - Then: `az extension add --name azure-devops`
4. **Python:** `python -m venv .venv`, then `.venv/Scripts/python -m pip install -r requirements.txt` (on macOS/Linux, `.venv/bin/python`).
5. **Azure sign-in:** `az login`. If the browser pop-up fails, use `az login --use-device-code`.
6. **Firewall:** a new machine has a new public IP. Add it in Azure Portal > SQL server > Networking > "Add your client IPv4 address". The "Allow Azure services" rule is already enabled for the Function.
7. **Verify:** paste the "Prereqs Prompt" from `README.md`. All rows should come back ready.

## Resume from here

Run these from the repo root. The SQL connection uses the `.env` values. Pass the password through the `SQLCMDPASSWORD` environment variable, not `-P`.

1. **Step 5, backfill:** `python scripts/backfill_topics.py`. This takes about 5–10 minutes because arXiv allows one request every 3 seconds. It re-merges January safely.
2. **Step 6, daily sync:**
   - `sqlcmd ... -l 60 -i sql/07_create_sync_log.sql`
   - Seed one row recording the backfill, so the first sync doesn't redo it:

     ```sql
     INSERT INTO SYNC_LOG (submitted_from, submitted_to, papers_loaded, search_topics)
     SELECT '2025-01-01', CAST(GETDATE() AS DATE), COUNT(*),
            'large language models, time series forecasting, vector database'
     FROM PAPERS WHERE load_source = 'backfill';
     ```

   - `python scripts/daily_sync.py`, then check `SELECT * FROM SYNC_LOG`.
3. **Step 7, deploy:**
   - `cmp tools/arxiv_search.py azure_function/shared/arxiv_search.py` and the same for `azure_sql_queries.py`. Both must be identical.
   - `cd azure_function && func azure functionapp publish <function-app> --python`
   - `az functionapp function show -g <rg> -n <function-app> --function-name daily_paper_sync`
   - Trigger it once through the admin endpoint (see `AGENTS.md` "Manual trigger"); HTTP 202 means accepted. Then check that a new `SYNC_LOG` row appeared.
4. **Step 8, analyze:** print and run `sql/03_paper_count.sql`, `04_submission_trends.sql`, `05_top_authors.sql`, and `06_category_breakdown.sql`.
5. **Step 9, visualize:** `python output/generate_charts.py` writes `output/submission_trends.png` and `output/category_breakdown.png`.
6. **Step 10, report:** write `output/executive_summary.md` from the Step 8 results.
7. **Step 11, close the ticket:** `az boards work-item update --id <ticket-id> --state Done --discussion "<summary>" --org "$AZURE_DEVOPS_ORG"`

## Roll back instead (abandon this run)

This restores the previous run's data and loses the 323 rows of the new run, which can be re-fetched from arXiv.

```sql
DROP TABLE IF EXISTS PAPERS;
DROP TABLE IF EXISTS SYNC_LOG;
EXEC sp_rename 'PAPERS_ARCHIVE_20261111', 'PAPERS';
EXEC sp_rename 'SYNC_LOG_ARCHIVE_20261111', 'SYNC_LOG';
EXEC sp_rename 'PAPERS.IX_PAPERS_ARCHIVE_PRIMARY_CATEGORY', 'IX_PAPERS_PRIMARY_CATEGORY', 'INDEX';
EXEC sp_rename 'PAPERS.IX_PAPERS_ARCHIVE_SUBMITTED_DATE', 'IX_PAPERS_SUBMITTED_DATE', 'INDEX';
```

Then revert the local timer change with `git checkout -- azure_function/function_app.py`.

## Later cleanup

Once the new run is complete and checked, drop the archives with `DROP TABLE PAPERS_ARCHIVE_20261111; DROP TABLE SYNC_LOG_ARCHIVE_20261111;`.

## Gotchas from this setup

- **Free-tier auto-pause:** the first connection after idle fails with "database not available" for up to about a minute, so use `-l 60` and retry.
- **arXiv rate limits:** after heavy runs arXiv may return HTTP 429 for a few minutes; wait and retry.
- **Windows `az.cmd` quoting:** the wrapper breaks on `&` or `(` in arguments. Call `"<CLI2>/python.exe" -IBm azure.cli ...` directly instead.
- **CRLF in `.env`:** when sourcing it in bash, strip carriage returns first: `set -a; source <(tr -d '\r' < .env); set +a`.
- **Python 3.10 is end-of-life on Azure Functions**, so new apps must use 3.12.
