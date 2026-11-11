
SELECT TOP 10
    cat.value AS arxiv_category,
    COUNT(*) AS paper_count
FROM PAPERS
CROSS APPLY OPENJSON(categories) AS cat
GROUP BY cat.value
ORDER BY paper_count DESC;
