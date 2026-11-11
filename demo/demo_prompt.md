# Demo Prompts

## Pre-Demo: Wake the Database (run 10 min before, NOT on stage)

```
Run a quick sqlcmd query against our Azure SQL database to wake it up: SELECT GETDATE()
```

## Pre-Demo: Verify Setup (run 5 min before, NOT on stage)

```
Verify our setup: 1) Check the arXiv API is reachable (no key needed), 2) Test sqlcmd can connect to Azure SQL, 3) Confirm pyodbc is installed. Just run quick checks for each.
```

## On Stage: /clear first

Run `/clear` to start with a clean conversation.

---

## Prompt 1: The Main Demo (paste this during the presentation)

```xml
<pipeline-request>
  <context>
    I need to build a research-paper intelligence database for AI and data processing —
    covering large language models, time series forecasting, and vector databases.
    Let's use our Azure SQL Database and the arXiv API (no API key needed).
  </context>

  <rules>
    - Announce each step before executing it (e.g., "Step 3: Searching arXiv...")
    - Show every SQL query and its results inline — the audience needs to see what's happening
    - Keep all output concise: tables over paragraphs, top 10 over full dumps
    - One script per task — no unnecessary helper files or abstractions
    - Confirm success at each step with a brief summary before moving to the next
    - Save charts to the output/ directory and confirm file paths
  </rules>

  <steps>
    <step name="create-ticket">
      Create an Azure DevOps work item to track this pipeline build.
      Use az boards to create a Task titled "Build AI & Data arXiv Paper Intelligence Pipeline".
    </step>

    <step name="connect-discover">
      Connect to our Azure SQL Database and show me what tables currently exist
      (should be empty — we're building from scratch). Note: the free tier
      auto-pauses after inactivity — the first query may take ~30 seconds to
      wake the database up. Use a 60-second login timeout (-l 60) and if the
      first attempt fails, wait a moment and retry once.
    </step>

    <step name="create-schema">
      Create a PAPERS table optimized for T-SQL with columns for
      arxiv_id (PK), title, abstract, primary_category, authors (JSON as NVARCHAR(MAX)),
      submitted_date, updated_date, categories (JSON as NVARCHAR(MAX)), search_query, load_source,
      and timestamps. Add indexes on primary_category and submitted_date.
    </step>

    <step name="search-arxiv">
      Use the arXiv search tools in tools/ to search three AI & data topics:
      search_by_title("large language models", limit=17),
      search_by_title("time series forecasting", limit=17),
      search_by_title("vector database", limit=16).
      Merge all results into one list (50 papers total).
    </step>

    <step name="load-data">
      Write a Python script using pyodbc to load those paper results into
      our Azure SQL table. Use parameterized MERGE statements for upsert logic. Execute it.
    </step>

    <step name="backfill">
      Backfill all large language models, time series forecasting, and vector database papers
      submitted since January 1, 2025. Use date-range filtering on the arXiv API
      (submitted_from / submitted_to) to pull papers in batches, loading each batch into the
      PAPERS table with MERGE upserts. arXiv asks for one request every 3 seconds, which
      tools/arxiv_search.py already enforces. Track total papers loaded and date range covered.
    </step>

    <step name="daily-sync">
      Set up a daily sync process that loads only net-new papers since the last run.
      Create a SYNC_LOG table to track the last successful sync date and paper count.
      Write a Python script that queries the arXiv API for papers submitted after the last
      sync date, loads them via MERGE upserts, and updates the sync log.
    </step>

    <step name="deploy-function">
      Create an Azure Function to run the daily sync automatically. Build the
      azure_function/ directory from scratch with function_app.py, host.json,
      and requirements.txt. The function should:
        - Use a timer trigger with schedule "0 0 7 * * *" (daily at 7 AM UTC)
        - Reuse the same arXiv search and MERGE upsert logic from the earlier steps
        - Pick the ODBC driver at runtime: Driver 18 if installed, else Driver 17 (Consumption plan images differ)
        - Copy the arxiv_search.py and azure_sql_queries.py into a shared/ subdirectory
          so the function can import them
      arXiv needs no API key, so the Function App only needs the four Azure SQL settings.
      Then deploy live:
        cd azure_function && func azure functionapp publish patent-sync-func --python
      After deployment, confirm the function is registered using:
        az functionapp function show --name patent-sync-func --resource-group patent-intelligence-rg --function-name daily_paper_sync
      This turns the manual sync into a serverless job that runs every morning at 7 AM UTC.
    </step>

    <step name="analyze">
      Write T-SQL analytical queries and save each one to the sql/ directory
      as a numbered .sql file before executing it. The audience will copy these
      into the Azure Portal Query Editor to validate results visually.

      Queries to write and run:
      1. Summary stats — total papers loaded, earliest/latest submission dates,
         unique primary categories (save as sql/03_paper_count.sql)
      2. Submission trends — paper count by year, ordered chronologically
         (save as sql/04_submission_trends.sql)
      3. Top authors — parse the authors JSON array using CROSS APPLY
         OPENJSON, group by author name, top 10 (save as sql/05_top_authors.sql)
      4. Research categories — parse categories JSON array using CROSS APPLY
         OPENJSON, group by arXiv category (e.g., cs.AI), top 10
         (save as sql/06_category_breakdown.sql)
    </step>

    <step name="visualize">
      Create matplotlib charts from the query results and save as PNG files
      to the output/ directory:
      1. Submission trends by month (bar chart)
      2. Top research categories by arXiv category (horizontal bar chart)
    </step>

    <step name="report">
      Generate a markdown executive summary of the AI & data research landscape on arXiv.
    </step>

    <step name="close-ticket">
      Update the Azure DevOps work item to "Done". Add a discussion comment
      summarizing what was built: table created, papers loaded, analysis complete.
    </step>
  </steps>

  <resources>
    The arXiv search tools are in the tools/ directory. The Azure SQL connection details
    are in the .env file. Let's build this entire pipeline right now.
  </resources>
</pipeline-request>
```

---

## Prompt 2: Audience Participation (optional, use during Q&A if time allows)

```xml
<follow-up>
  The viewer wants to explore [TOPIC]. Search arXiv for papers using
  search_by_title("[TOPIC]", limit=20), load the results into our PAPERS table,
  and give me a quick summary of what researchers are publishing in that area.
</follow-up>
```

---

## Prompt 3: Quick Follow-Up Analysis (optional, if demo finishes early)

```xml
<follow-up>
  Compare paper activity across our three topics: large language models, time series forecasting,
  and vector databases. Run a query showing submission trends by topic side by side,
  and create a comparison chart.
</follow-up>
```
