-- QC Verification Queries for arXiv Paper Intelligence Pipeline
-- Run these in Azure Portal > SQL Query Editor to validate pipeline output

-- QC 1: Total papers, date range, primary category count
SELECT COUNT(*) AS total_papers,
       MIN(submitted_date) AS earliest_submission,
       MAX(submitted_date) AS latest_submission,
       COUNT(DISTINCT primary_category) AS unique_primary_categories
FROM PAPERS;

-- QC 2: Papers by load source (should show title_search, backfill, daily_sync)
SELECT load_source, COUNT(*) AS cnt
FROM PAPERS GROUP BY load_source ORDER BY cnt DESC;

-- QC 3: Papers by search topic
SELECT search_query, COUNT(*) AS cnt
FROM PAPERS GROUP BY search_query ORDER BY cnt DESC;

-- QC 4: Submission trends by month (granular view for backfill verification)
SELECT FORMAT(submitted_date, 'yyyy-MM') AS submission_month, COUNT(*) AS cnt
FROM PAPERS WHERE submitted_date IS NOT NULL
GROUP BY FORMAT(submitted_date, 'yyyy-MM')
ORDER BY submission_month;

-- QC 5: Check for empty/null arxiv_ids (should be 0)
SELECT COUNT(*) AS empty_ids FROM PAPERS
WHERE arxiv_id IS NULL OR arxiv_id = '';

-- QC 6: Check for duplicates (should be 0)
SELECT arxiv_id, COUNT(*) AS cnt
FROM PAPERS GROUP BY arxiv_id HAVING COUNT(*) > 1;

-- QC 7: SYNC_LOG history
SELECT * FROM SYNC_LOG ORDER BY sync_date DESC;

-- QC 8: Sample papers (spot-check titles and data quality)
SELECT TOP 10 arxiv_id, title, primary_category, submitted_date, search_query, load_source
FROM PAPERS ORDER BY submitted_date DESC;
