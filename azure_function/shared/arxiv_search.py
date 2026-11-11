"""arXiv paper search wrapper (export.arxiv.org Atom API).

No API key is needed. arXiv's terms of use ask for at most one request every
3 seconds, so every call here is throttled. Metadata is CC0.

Query syntax used (see https://info.arxiv.org/help/api/user-manual.html):
  - ti:"large language models"      exact phrase in the title
  - cat:cs.AI                       arXiv category (cs.AI, cs.DB, cs.LG, ...)
  - submittedDate:[YYYYMMDDHHMM TO YYYYMMDDHHMM]   submission date range
One query slice returns at most ~2000 results, so use date windows to go deeper.

Every function returns plain dicts with these keys (the PAPERS table columns):
  arxiv_id, title, abstract, primary_category, authors, submitted_date,
  updated_date, categories
"""
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Optional

ARXIV_API = "https://export.arxiv.org/api/query"

# Generic client name: no personal contact details are sent.
USER_AGENT = "azure-sql-arxiv-intelligence-demo/1.0"

# AI & data categories searched by default.
DEFAULT_CATEGORIES = ("cs.AI", "cs.DB", "cs.LG")

# Demo topics (title phrases) and the one place the backfill start date lives.
# The daily-sync function and scripts/category_backfill.py both import these.
SEARCH_TOPICS = ("large language models", "time series forecasting", "vector database")
BACKFILL_START = "2025-01-01"

PAGE_SIZE = 100          # results requested per HTTP call
REQUEST_INTERVAL = 3.0   # seconds between calls (arXiv terms of use)
MAX_ATTEMPTS = 3
RETRY_CODES = (429, 503)

_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "os": "http://a9.com/-/spec/opensearch/1.1/",
}

_last_request = 0.0


def search_by_title(
    keywords: str,
    limit: int = 50,
    submitted_from: Optional[str] = None,
    submitted_to: Optional[str] = None,
    start: int = 0,
    categories: tuple = DEFAULT_CATEGORIES,
) -> list[dict]:
    """Search papers whose title contains the phrase `keywords`.

    Args:
        keywords: Phrase to match in the title (e.g., "large language models")
        limit: Maximum number of results to return (paginates automatically)
        submitted_from: Earliest submission date (YYYY-MM-DD), inclusive
        submitted_to: Latest submission date (YYYY-MM-DD), inclusive
        start: Offset for pagination (skip first N results)
        categories: arXiv categories to restrict to; empty tuple means no restriction

    Returns:
        List of paper dictionaries, newest submissions first
    """
    query = f'ti:"{keywords}"'
    query += _category_clause(categories)
    query += _date_clause(submitted_from, submitted_to)
    return _search(query, limit, start)


def search_by_category(
    category: str,
    limit: int = 50,
    submitted_from: Optional[str] = None,
    submitted_to: Optional[str] = None,
    start: int = 0,
) -> list[dict]:
    """Search papers by arXiv category (e.g., "cs.AI", "cs.DB").

    Categories are assigned by the authors and moderators, so this is the
    most precise filter: no keyword ambiguity.

    Args:
        category: arXiv category code
        limit: Maximum number of results to return (paginates automatically)
        submitted_from: Earliest submission date (YYYY-MM-DD), inclusive
        submitted_to: Latest submission date (YYYY-MM-DD), inclusive
        start: Offset for pagination (skip first N results)

    Returns:
        List of paper dictionaries, newest submissions first
    """
    query = f"cat:{category}" + _date_clause(submitted_from, submitted_to)
    return _search(query, limit, start)


def get_paper(arxiv_id: str) -> Optional[dict]:
    """Get a single paper by arXiv ID (e.g., "2311.12345", version optional)."""
    try:
        _, entries = _fetch({"id_list": arxiv_id, "max_results": 1})
    except Exception as e:
        print(f"[arXiv API error: {e}]")
        return None
    return entries[0] if entries else None


def _category_clause(categories: tuple) -> str:
    if not categories:
        return ""
    return " AND (" + " OR ".join(f"cat:{c}" for c in categories) + ")"


def _date_clause(submitted_from: Optional[str], submitted_to: Optional[str]) -> str:
    """Build the submittedDate range; arXiv needs both bounds as YYYYMMDDHHMM."""
    if not submitted_from and not submitted_to:
        return ""
    low = (submitted_from or "1991-01-01").replace("-", "") + "0000"
    high = (submitted_to or "2099-12-31").replace("-", "") + "2359"
    return f" AND submittedDate:[{low} TO {high}]"


def _search(search_query: str, limit: int, start: int = 0) -> list[dict]:
    """Run a query and page through results until `limit` papers are collected.

    Returns an empty list (after printing why) on any failure.
    """
    try:
        results: list[dict] = []
        offset = start
        total = 0
        while len(results) < limit:
            page = min(PAGE_SIZE, limit - len(results))
            total, entries = _fetch({
                "search_query": search_query,
                "start": offset,
                "max_results": page,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            })
            results.extend(entries)
            offset += len(entries)
            if len(entries) < page or offset >= total:
                break
        if results:
            print(f"[arXiv: {total} total matches, returning {len(results)}]")
        return results
    except urllib.error.HTTPError as e:
        print(f"[arXiv API error: HTTP {e.code}]")
        return []
    except Exception as e:
        print(f"[arXiv API error: {e}]")
        return []


def _fetch(params: dict) -> tuple[int, list[dict]]:
    """GET one page from the arXiv API with throttling and retry.

    Returns:
        (total matching results, formatted entries on this page)
    """
    global _last_request
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        wait = REQUEST_INTERVAL - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()

        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as response:
                return _parse_feed(response.read())
        except urllib.error.HTTPError as e:
            if e.code not in RETRY_CODES or attempt == MAX_ATTEMPTS:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == MAX_ATTEMPTS:
                raise
        time.sleep(5 * attempt)  # back off before retrying

    return 0, []  # unreachable; keeps type checkers happy


def _parse_feed(xml_bytes: bytes) -> tuple[int, list[dict]]:
    """Parse an arXiv Atom feed into (total_results, papers).

    arXiv reports bad queries as HTTP 200 with a single entry titled "Error",
    so that case is raised as a ValueError instead of returning junk.
    """
    root = ET.fromstring(xml_bytes)
    total_text = root.findtext("os:totalResults", default="0", namespaces=_NS)
    total = int(total_text) if total_text.strip().isdigit() else 0

    papers = []
    for entry in root.findall("atom:entry", _NS):
        entry_id = entry.findtext("atom:id", default="", namespaces=_NS)
        if "/api/errors" in entry_id:
            message = entry.findtext("atom:summary", default="unknown error", namespaces=_NS)
            raise ValueError(f"arXiv rejected the query: {message.strip()}")
        paper = _format_entry(entry)
        if paper:
            papers.append(paper)
    return total, papers


def _clean(text: Optional[str]) -> str:
    """Collapse the line breaks and runs of spaces arXiv leaves in titles/abstracts."""
    return " ".join((text or "").split())


def _format_entry(entry: ET.Element) -> Optional[dict]:
    """Convert one Atom <entry> to the standardized dict used for storage.

    Returns:
        Paper dictionary, or None if the entry has no usable ID
    """
    raw_id = entry.findtext("atom:id", default="", namespaces=_NS)
    # http://arxiv.org/abs/2611.14519v1 -> 2611.14519 (also works for hep-th/9901001v2)
    arxiv_id = re.sub(r"v\d+$", "", raw_id.split("/abs/")[-1].strip())
    if not arxiv_id:
        return None

    categories = [c.get("term") for c in entry.findall("atom:category", _NS) if c.get("term")]
    primary = entry.find("arxiv:primary_category", _NS)
    primary_category = primary.get("term") if primary is not None else ""
    if not primary_category and categories:
        primary_category = categories[0]

    authors = [
        _clean(a.findtext("atom:name", default="", namespaces=_NS))
        for a in entry.findall("atom:author", _NS)
    ]

    return {
        "arxiv_id": arxiv_id,
        "title": _clean(entry.findtext("atom:title", default="", namespaces=_NS)),
        "abstract": _clean(entry.findtext("atom:summary", default="", namespaces=_NS)),
        "primary_category": primary_category,
        "authors": [a for a in authors if a],
        "submitted_date": entry.findtext("atom:published", default="", namespaces=_NS)[:10] or None,
        "updated_date": entry.findtext("atom:updated", default="", namespaces=_NS)[:10] or None,
        "categories": categories,
    }
