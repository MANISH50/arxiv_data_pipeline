
SELECT
    COUNT(*) AS total_papers,
    MIN(submitted_date) AS earliest_submission,
    MAX(submitted_date) AS latest_submission,
    COUNT(DISTINCT primary_category) AS unique_primary_categories
FROM PAPERS;
