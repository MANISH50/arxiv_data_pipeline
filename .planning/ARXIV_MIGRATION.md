# Data Source Migration: USPTO to arXiv

**Status**: code and docs migrated; database steps pending a configured `.env`.

## Why

The USPTO Open Data Portal API needs a key that is not available on demand. The pipeline goal does not depend on
patents, so the data source was swapped. Other options considered: Google Patents on BigQuery (needs a Google login,
awkward for an Azure-only demo), EPO OPS (registration, quotas), OpenAlex (key now needed), Crossref (sparse abstracts),
Semantic Scholar (rate-limited without a key).

## Why arXiv

Run by Cornell University, CC0 metadata, no key or account, `submittedDate` range filter (tested), Atom XML parsed with
the Python standard library (no new dependency for the Azure Function).

## Field mapping

| Patents | arXiv papers |
|---|---|
| `PATENTS` | `PAPERS` |
| `patent_number` | `arxiv_id` (version suffix stripped) |
| `assignee` | `primary_category` |
| `inventors` (JSON) | `authors` (JSON) |
| `cpc_codes` (JSON) | `categories` (JSON) |
| `filing_date` / `grant_date` | `submitted_date` / `updated_date` |
| `category` (load tag) | `load_source` |
| SYNC_LOG `filing_date_from/to`, `patents_loaded` | `submitted_from/to`, `papers_loaded` |

## Unchanged on purpose

- Pipeline steps, ticket flow, MERGE pattern, SYNC_LOG, timer schedule, ODBC Driver 17 in the Function.
- Azure resource names (database, resource group, Function App): they are labels, and the free tier allows one free
  database per subscription, so existing ones are reused. Only the function name changed (`daily_paper_sync`).
- The patent-era notes in this folder are history and were not rewritten.

## Operational notes

- arXiv asks for one request every 3 seconds; `tools/arxiv_search.py` enforces it.
- One query slice returns at most ~2000 results, so backfills use monthly windows.
- If a previous version already created `SYNC_LOG` with the old column names, drop and recreate it (it only holds sync
  history) before running the new sync, or `IF NOT EXISTS` will skip creation and the INSERT will fail.
- Redeploy the Function (`func azure functionapp publish ...`) to replace the old `daily_patent_sync` function.
