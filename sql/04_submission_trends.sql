
SELECT
    YEAR(submitted_date) AS submission_year,
    COUNT(*) AS paper_count
FROM PAPERS
WHERE submitted_date IS NOT NULL
GROUP BY YEAR(submitted_date)
ORDER BY submission_year;
