
MERGE INTO PAPERS AS target
USING (SELECT
    ? AS arxiv_id,
    ? AS title,
    ? AS abstract,
    ? AS primary_category,
    ? AS authors,
    ? AS submitted_date,
    ? AS updated_date,
    ? AS categories,
    ? AS search_query,
    ? AS load_source
) AS source
ON target.arxiv_id = source.arxiv_id
WHEN MATCHED THEN UPDATE SET
    title = source.title,
    abstract = source.abstract,
    primary_category = source.primary_category,
    authors = source.authors,
    submitted_date = source.submitted_date,
    updated_date = source.updated_date,
    categories = source.categories,
    search_query = source.search_query,
    load_source = source.load_source,
    updated_at = GETDATE()
WHEN NOT MATCHED THEN INSERT (
    arxiv_id, title, abstract, primary_category, authors,
    submitted_date, updated_date, categories, search_query, load_source,
    created_at, updated_at
) VALUES (
    source.arxiv_id, source.title, source.abstract, source.primary_category,
    source.authors, source.submitted_date, source.updated_date, source.categories,
    source.search_query, source.load_source, GETDATE(), GETDATE()
);
