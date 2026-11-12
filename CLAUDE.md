# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

**Start of session:** if `Progress.md` exists, read it first. It records where the last pipeline run stopped and how to resume or roll back. Then read `.internal/OWNER_CONFIG.md` (if present) for this owner's concrete Azure, DevOps and GitHub values.

`AGENTS.md` (imported above) holds the tool list, T-SQL conventions, demo flow and operating principles. This file adds what it does not cover: how the pieces fit, which files must stay in sync, and the gotchas.

## What this repo is

A demo of an AI agent building an Azure pipeline: **arXiv API → Python → Azure SQL (free tier) → T-SQL/OPENJSON analysis → charts, plus a timer-triggered Azure Function for the daily sync**. The data source was originally the USPTO patent API and was migrated to arXiv (no key needed); the repo/GitHub name and Azure resource names still say "patent" on purpose. `.planning/ARXIV_MIGRATION.md` records the decision and field mapping. Older `.planning/*` notes are patent-era history, so don't rewrite them.

## Commands

There is no test suite or linter (only `.markdownlint.json`). Use a venv; on Windows call `.venv\Scripts\python.exe`, elsewhere `python3`.

```bash
pip install -r requirements.txt
python -m compileall -q tools scripts azure_function output          # syntax check
python scripts/category_backfill.py                                   # monthly cs.AI/cs.LG/cs.DB backfill (slow: 3 s per arXiv call + one MERGE round trip per row)
python output/generate_charts.py                                      # writes output/submission_trends.png, category_breakdown.png
python -c "from tools.arxiv_search import search_by_title; print(len(search_by_title('large language models', limit=1)))"   # live smoke test
cd azure_function && func azure functionapp publish <app> --python    # deploy (remote build)
```

- `tools/arxiv_search._parse_feed(xml_bytes)` is pure, so test the parser offline with a saved Atom feed instead of hitting arXiv.
- The Azure CLI has no `az functionapp function invoke`. Trigger the timer function with `POST https://<app>.azurewebsites.net/admin/functions/daily_paper_sync` and header `x-functions-key` (master key from `az functionapp keys list`; never print it). HTTP 202 means accepted.
- Settings come from `.env` (see `.env.example`). arXiv needs no key, so only the four `AZURE_SQL_*` values (plus the DevOps ones for tickets) matter.

## Architecture

- **`tools/arxiv_search.py`** returns plain dicts (`arxiv_id, title, abstract, primary_category, authors, submitted_date, updated_date, categories`). It throttles to one request per 3 s, pages automatically (100 per call), retries 429/503, and turns arXiv's HTTP-200 "Error" entry into a failure. It also owns the shared constants `SEARCH_TOPICS` and `BACKFILL_START`.
- **`tools/azure_sql_queries.py`** builds all T-SQL. `build_upsert_query()` is a MERGE with **10 positional `?` parameters in a fixed order**; every caller (`function_app.py`, `scripts/category_backfill.py`, `demo/backup_commands.md`) must pass the tuple in that order: arxiv_id, title, abstract, primary_category, authors, submitted_date, updated_date, categories, search_query, load_source.
- **Incremental sync:** `SYNC_LOG.submitted_to` of the last completed run becomes the next run's start date. MERGE is idempotent, so overlapping windows are safe. `load_source` is overwritten by the last loader that touches a paper.
- **`azure_function/function_app.py`** (timer `0 0 7 * * *`, function `daily_paper_sync`) imports from `azure_function/shared/`, because the deployed app cannot import from `tools/`. It picks ODBC Driver 18 or 17 at runtime. Local scripts use Driver 18.
- Authors and categories are stored as JSON strings in `NVARCHAR(MAX)` and parsed with `CROSS APPLY OPENJSON`.

## Keep in sync (easy to break)

- `azure_function/shared/arxiv_search.py` and `azure_sql_queries.py` must be **byte-identical** to the `tools/` versions. After editing either, `cp` them and verify with `cmp`.
- `sql/01`–`07` mirror the builders in `tools/azure_sql_queries.py`. The Python builder is the source of truth, so regenerate the `.sql` files from it rather than hand-editing. `sql/08`/`09` are hand-written QC queries.
- The `<pipeline-request>` prompt in `README.md` must stay identical to Prompt 1 in `demo/demo_prompt.md`. `demo/backup_commands.md` mirrors the same steps as manual commands.
- Hardcoded demo numbers live in several docs: 17/17/16 = 50 papers, the three topics, and the 2025-01-01 backfill start. Change them together.

## Gotchas

- **arXiv limits:** about 2000 results per query slice (so backfills use monthly windows), IDs carry a version suffix that must be stripped, and queries use `ti:"phrase"`, `cat:cs.AI` and `submittedDate:[YYYYMMDDHHMM TO YYYYMMDDHHMM]`.
- **Azure Functions:** Python 3.10 is end-of-life and rejected for new apps, so use 3.12. The SQL server needs "Allow Azure services" (or the app's outbound IPs) in its firewall or the Function cannot connect.
- **Free-tier SQL cold start:** the first connection can take ~30–60 s; use a long login timeout and retry once. A new database named in the portal may differ from the name in `.env`, so check `az sql db list` if login fails.
- **Line endings:** git stores LF and the Windows checkout converts to CRLF, so scripted text replacements must normalize `\r\n` before matching.
- **Public repo:** keep secrets and personal or account-specific names (server, resource group, Function App, admin login) out of tracked files. Put them in `.internal/` (gitignored), e.g. `.internal/OWNER_CONFIG.md` and `.internal/SETUP_STATUS.md`. Read those at session start if they exist.
- **Git remotes:** `origin` is the upstream author's repo and rejects pushes from other accounts. Push to your own fork remote, and work on a feature branch.
