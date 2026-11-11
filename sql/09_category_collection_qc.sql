-- QC Queries for arXiv Category Collection
-- Run these in Azure Portal > SQL Query Editor to verify the category backfill

-- QC 1: Count by arXiv category searched
SELECT search_query, COUNT(*) AS cnt
FROM PAPERS
WHERE load_source = 'category_collection'
GROUP BY search_query
ORDER BY cnt DESC;

-- QC 2: Total by load source (keyword vs category)
SELECT load_source, COUNT(*) AS cnt
FROM PAPERS
GROUP BY load_source
ORDER BY cnt DESC;

-- QC 3: Category distribution within collected papers
SELECT TOP 15
    cat.value AS arxiv_category,
    COUNT(*) AS paper_count
FROM PAPERS
CROSS APPLY OPENJSON(categories) AS cat
WHERE load_source = 'category_collection'
GROUP BY cat.value
ORDER BY paper_count DESC;

-- QC 4: Monthly submission trends for category-collected papers
SELECT FORMAT(submitted_date, 'yyyy-MM') AS submission_month, COUNT(*) AS cnt
FROM PAPERS
WHERE load_source = 'category_collection' AND submitted_date IS NOT NULL
GROUP BY FORMAT(submitted_date, 'yyyy-MM')
ORDER BY submission_month;

-- QC 5: Sample category-collected papers
SELECT TOP 10 arxiv_id, title, primary_category, submitted_date, search_query
FROM PAPERS
WHERE load_source = 'category_collection'
ORDER BY submitted_date DESC;
