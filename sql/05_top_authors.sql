
SELECT TOP 10
    author.value AS author_name,
    COUNT(*) AS paper_count
FROM PAPERS
CROSS APPLY OPENJSON(authors) AS author
GROUP BY author.value
ORDER BY paper_count DESC;
