<div align="center">

# Claude Code + Azure SQL: AI-Powered arXiv Research Intelligence

### From Zero to Full Data Pipeline — Faster Than You Thought Possible

[![Claude Code](https://img.shields.io/badge/Claude_Code-AI_Agent-blueviolet?style=for-the-badge&logo=anthropic)](https://claude.ai/download)
[![Azure SQL](https://img.shields.io/badge/Azure_SQL-Free_Tier-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white)](https://aka.ms/azuresqlhub)
[![Python](https://img.shields.io/badge/Python-pyodbc-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![T-SQL](https://img.shields.io/badge/T--SQL-OPENJSON-CC2927?style=for-the-badge&logo=microsoftsqlserver&logoColor=white)](https://learn.microsoft.com/en-us/sql/t-sql/)
[![arXiv API](https://img.shields.io/badge/arXiv-Paper_API-b31b1b?style=for-the-badge&logo=arxiv&logoColor=white)](https://info.arxiv.org/help/api/index.html)
[![Azure Functions](https://img.shields.io/badge/Azure_Functions-Timer_Trigger-0062AD?style=for-the-badge&logo=azurefunctions&logoColor=white)](https://learn.microsoft.com/en-us/azure/azure-functions/)
[![Azure DevOps](https://img.shields.io/badge/Azure_DevOps-Boards-0078D7?style=for-the-badge&logo=azuredevops&logoColor=white)](https://dev.azure.com)

---

| **Date** | **Venue** | **Presenter** |
| :---: | :---: | :---: |
| Tue, Feb 18, 2026 | Virtual | Kyle Chalmers |
| 5:00 PM MST | [Arizona Data Platform User Group](https://www.meetup.com/arizona-data-platform-user-group/events/312313644/) | KC Labs AI |

---

| **YouTube** | **LinkedIn** | **GitHub Repo** | **KC Labs AI** | **AI Workshop** | **Morning Hike** |
| :---: | :---: | :---: | :---: | :---: | :---: |
| <img src="./qr_codes/youtube_qr.png" width="150" alt="YouTube QR"> | <img src="./qr_codes/linkedin_qr.png" width="150" alt="LinkedIn QR"> | <img src="./qr_codes/repo_qr.png" width="150" alt="GitHub QR"> | <img src="./qr_codes/kclabs_qr.png" width="150" alt="KC Labs QR"> | <img src="./qr_codes/aztechweek_workshop_qr.png" width="150" alt="Workshop QR"> | <img src="./qr_codes/aztechweek_hike_qr.png" width="150" alt="Hike QR"> |
| [Subscribe](https://www.youtube.com/channel/UCkRi29nXFxNBuPhjseoB6AQ) | [Connect](https://www.linkedin.com/in/kylechalmers/) | [Star](https://github.com/kyle-chalmers/azure-sql-patent-intelligence) | [Visit](https://kclabs.ai/) | [RSVP](https://partiful.com/e/VPy2EpNYQFppO6ZQA17n) | [RSVP](https://partiful.com/e/vMiPKyrTML8yf8Gnf618) |

- YouTube (subscribe for more data + AI content): https://www.youtube.com/channel/UCkRi29nXFxNBuPhjseoB6AQ
- LinkedIn: https://www.linkedin.com/in/kylechalmers/
- This repo: https://github.com/kyle-chalmers/azure-sql-patent-intelligence
- KC Labs AI: https://kclabs.ai/

AZ Tech Week 2026:
- The Practical AI Playbook Workshop (Wed, Apr 8 - Scottsdale): https://partiful.com/e/VPy2EpNYQFppO6ZQA17n
- Sat Morning Hike, Connect, & Coffee (Sat, Apr 11 - Phoenix): https://partiful.com/e/vMiPKyrTML8yf8Gnf618

</div>

---

## The Big Idea

> **Today with Claude Code and other AI coding tools, one well-designed prompt with the appropriate context can lead us to building a full data pipeline in one sitting. What used to take days now can happen over hours or even minutes in a single conversation, with ticket tracking, schema design, API ingestion, data loading, analysis, and visualization all handled by an AI agent using the tools available in your Microsoft data stack today.**

In this video I'll build a real research-paper intelligence database analyzing AI and data processing papers from arXiv using:

- **Claude Code** as the AI agent — orchestrating the entire workflow via different CLI/MCP tools
- **Azure SQL Database** (free tier) as the data store, queried through `sqlcmd` and loaded with `pyodbc`
- **Azure DevOps Boards** (free tier) for real-world ticket-driven workflow — the pipeline opens a ticket and closes it when done
- **arXiv API** (free, no key) as the live data source
- **Azure Functions** (free tier) for automated daily paper sync — timer-triggered, serverless
- **One structured prompt** that drives all steps from ticket creation to ticket closure.

---

## Session Flow

```text
┌──────────────────────────────────────────────────────────────────────┐
│                    SESSION OVERVIEW (~30 min)                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐   ┌─────────────┐   ┌──────────────┐   ┌──────────┐  │
│  │  Intro   │──▶│   Context   │──▶│    Demo      │──▶│ Wrap-up  │  │
│  │ (2 min)  │   │  (3 min)    │   │  (15 min)    │   │ (3 min)  │  │
│  └──────────┘   └─────────────┘   └──────────────┘   └──────────┘  │
│                                                              │      │
│                  Show CLAUDE.md     DevOps Ticket ──▶        ▼      │
│                  + tools/           empty DB ──▶ full       Q&A     │
│                                     paper analysis                   │
│                                     ──▶ Azure Function               │
│                                     ──▶ Close Ticket                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Prereqs Prompt for Claude Code

> After cloning this repo, open it in Claude Code and paste this prompt to install all dependencies:

<details>
<summary><b>Prereqs Prompt</b> <sup>(click to expand)</sup></summary>

```xml
<prereqs-request>
  <context>
    I just cloned the azure-sql-patent-intelligence repo and need to install all
    dependencies, configure my environment, and verify everything works before
    running the demo. My Azure SQL Database should already be
    set up — I just need the local tooling wired together.
  </context>

  <rules>
    - Check what's already installed before installing — don't reinstall working tools
    - Never print or log credentials — use environment variables from .env only
    - If a step fails, explain what happened in one sentence and continue with the rest
    - At the end, print a single summary table showing what's ready and what needs attention
  </rules>

  <steps>
    <step name="env-file">
      If .env doesn't already exist, copy .env.example to .env.
      Print a checklist of which variables still need to be filled in (check for
      empty values). Don't print the actual values — just show which are set and
      which are missing.
    </step>

    <step name="python-deps">
      Install Python dependencies from requirements.txt:
      pyodbc, matplotlib, python-dotenv, pandas, qrcode.
      Run: pip install -r requirements.txt
      Verify with: python3 -c "import pyodbc, matplotlib, dotenv, pandas; print('OK')"
    </step>

    <step name="sqlcmd">
      Install sqlcmd for connecting to Azure SQL Database.
      macOS: brew install microsoft/mssql-release/mssql-tools18
      Linux: https://learn.microsoft.com/en-us/sql/linux/sql-server-linux-setup-tools
      Verify with: sqlcmd '-?'
    </step>

    <step name="azure-cli">
      Install Azure CLI if not present, then add the Azure DevOps extension.
      macOS: brew install azure-cli
      Then: az extension add --name azure-devops
      If already installed, skip. Verify with: az boards -h
      Note: User will need to run 'az login' and 'az devops configure --defaults
      organization=ORG project=PROJECT' themselves after this step.
    </step>

    <step name="test-azure-sql">
      If AZURE_SQL_SERVER is set in .env, test the connection:
      source .env && sqlcmd -S "$AZURE_SQL_SERVER" -d "$AZURE_SQL_DATABASE" \
        -U "$AZURE_SQL_USER" -P "$AZURE_SQL_PASSWORD" \
        -Q "SELECT DB_NAME() AS CurrentDB, SUSER_NAME() AS CurrentUser"
      If it fails with a firewall error, tell the user to add their IP in
      Azure Portal > SQL Server > Networking > Firewall rules.
    </step>

    <step name="verify-all">
      Print a summary table:
      - .env variables: which are set, which are empty (DO NOT PRINT ACTUAL VALUES)
      - Python packages: installed or missing
      - sqlcmd: available or not
      - Azure CLI + DevOps extension: available or not
      - Azure SQL connection: connected or failed (with reason)
      - arXiv API: reachable or not (no key needed)
    </step>
  </steps>
</prereqs-request>
```

</details>

---

## Demo: One Prompt, Complete Pipeline

```text
DevOps ──▶ arXiv API ──▶ Python ──▶ Azure SQL ──▶ T-SQL Analysis ──▶ Azure Function ──▶ Visualizations ──▶ DevOps
(ticket)    (search)     (load)      (store)       (OPENJSON)         (daily sync)      (matplotlib)     (close)
```

<details>
<summary><b>Demo Prompt</b> <sup>(click to expand)</sup></summary>

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

</details>

---

## Key Definitions

| Term | Definition |
|:-----|:-----------|
| **CLAUDE.md** | A markdown file that gives Claude Code all the context it needs about your project: available tools, database connections, coding conventions, and workflow steps. Think of it as the instruction manual for your AI agent. |
| **MERGE (T-SQL)** | An upsert statement. If the record exists, update it. If it doesn't, insert it. Makes data loading idempotent, so you can run it multiple times without duplicating data. |
| **OPENJSON (T-SQL)** | A T-SQL function that lets you query inside JSON strings stored in NVARCHAR columns. Azure SQL doesn't have a native JSON type, so this is how you parse JSON arrays for analysis. |
| **arXiv Categories** | Subject tags that authors and moderators assign to every paper. cs.AI is artificial intelligence, cs.LG is machine learning, cs.DB is databases. Think of them as genre tags for research. |

---

## AI & Data arXiv Categories Reference

**arXiv categories** are the subject tags every paper carries: one primary category plus any cross-listed ones. Analyzing them reveals where research activity is concentrated across AI and data processing domains. The pipeline stores them as a JSON array and parses them with `OPENJSON`.

These are the categories you'll see most often in AI & data processing papers:

| Category | Research Area | Description |
|:--------:|:--------------|:------------|
| cs.AI | Artificial Intelligence | Reasoning, agents, knowledge representation, general AI |
| cs.LG | Machine Learning | Learning algorithms, deep learning, training methods |
| cs.DB | Databases | Data management, query processing, vector and relational stores |
| cs.CL | Computation & Language | NLP, language models, text processing |
| cs.IR | Information Retrieval | Search, recommendation, retrieval-augmented generation |
| cs.CV | Computer Vision | Image and video recognition |

---

## Key Tools Demonstrated

<div align="center">

| Tool | Purpose | Command |
|:----:|:--------|:--------|
| ![Claude](https://img.shields.io/badge/-Claude_Code-blueviolet?style=flat-square) | AI agent orchestrating the pipeline | `claude` |
| ![Azure SQL](https://img.shields.io/badge/-Azure_SQL-0078D4?style=flat-square) | Database (free tier) | `sqlcmd -S server -d db -Q "..."` |
| ![Python](https://img.shields.io/badge/-pyodbc-3776AB?style=flat-square) | Data loading with MERGE upserts | `python3 load_papers.py` |
| ![arXiv](https://img.shields.io/badge/-arXiv_API-b31b1b?style=flat-square) | Research paper data source (free, no key) | `export.arxiv.org/api/query` |
| ![T-SQL](https://img.shields.io/badge/-T--SQL-CC2927?style=flat-square) | Analysis with OPENJSON | `CROSS APPLY OPENJSON(...)` |
| ![Azure Functions](https://img.shields.io/badge/-Azure_Functions-0062AD?style=flat-square) | Daily sync automation (free tier) | `func azure functionapp publish` |
| ![Azure DevOps](https://img.shields.io/badge/-Azure_DevOps-0078D7?style=flat-square) | Ticket-driven workflow | `az boards work-item create/update` |

</div>

---

## What Changes When an AI Agent Runs the Pipeline

The value isn't just speed — it's that one person can build something they wouldn't have attempted alone.

Manually, each step requires you to context-switch between docs, languages, and tools. With Claude Code, your job shifts from **writing code** to **reviewing code** — you describe intent and verify results.

| Step | What you do manually | What you do with Claude Code |
|:-----|:---------------------|:-----------------------------|
| Track the work | Open Azure DevOps, create a work item, fill in fields | Described in the prompt — created automatically |
| Design schema | Decide column types, JSON storage strategy, indexing | Review the generated DDL, approve or adjust |
| Search arXiv API | Read API docs, write HTTP requests, parse Atom XML | Describe what you want ("large language models papers") — agent calls the API |
| Load data into SQL | Write pyodbc script, handle connections, build MERGE statements | Review the generated script, watch it execute, verify row counts |
| Analyze with T-SQL | Look up OPENJSON syntax, write CTEs, iterate on queries | Ask questions in plain English, review the SQL and results |
| Visualize results | Write matplotlib boilerplate, format axes, save figures | Describe the charts you want, review the output |
| Deploy automation | Set up Azure Functions, write timer triggers, configure app settings | Review the function code, watch it deploy, verify in portal |
| Summarize findings | Write a report from scratch based on query results | Review the generated summary, edit for tone |

**The honest version:** I could not have built this pipeline without Claude Code — not because I can't write T-SQL or Python, but because I wouldn't have sat down and wired together the arXiv API, pyodbc MERGE statements, OPENJSON analytics, matplotlib charts, and Azure DevOps tickets in one sitting. The breadth of tools and syntax across a pipeline like this is the real barrier, and that's exactly what an AI agent absorbs for you.

---

## Cost Breakdown

| Component | Cost |
|:----------|:----:|
| Azure SQL Database free tier | $0/month (lifetime, 100K vCore-seconds, 32 GB) |
| arXiv API | $0 (no API key needed) |
| Claude Code (Pro plan) | $20/month (or $100/month for Max) |
| Azure Functions (Consumption plan) | $0/month (1M free executions, ~30 runs/month) |
| Azure DevOps Boards free tier | $0 (up to 5 users) |
| sqlcmd + pyodbc | $0 (open source) |
| **Total** | **$20-100/month** |

---

## Takeaways

<table>
<tr>
<td width="33%" align="center">

### 1. AI Works WITH Your Stack

No special plugins. Claude Code uses `sqlcmd` and `pyodbc` — the same tools you already know. It connects TO your Azure SQL, not around it.

</td>
<td width="33%" align="center">

### 2. One Prompt, Complete Pipeline

From empty database to executive report in a single conversation. API ingestion, schema creation, data loading, analysis, and visualization.

</td>
<td width="33%" align="center">

### 3. Context Engineering is the Skill

The CLAUDE.md file teaches the AI your tools, patterns, and standards. That's the real investment — everything else flows from it.

</td>
</tr>
</table>

---

## Prerequisites

### arXiv API (No Key Needed)

arXiv's API is open: no account, key, or sign-up. Please respect its rule of one request every 3 seconds — `tools/arxiv_search.py` already enforces it.

### Azure SQL Database (Free Tier)

> **Detailed walkthrough**: See **[docs/AZURE_SQL_SETUP.md](docs/AZURE_SQL_SETUP.md)** for step-by-step instructions with screenshots.

1. Go to: **<https://aka.ms/azuresqlhub>** and click "Try for free"
2. Create a logical server with SQL authentication
3. Create database: `PatentIntelligence` (any name works — the free tier allows one free database per subscription, so reuse an existing one; select "None" for data source)
4. Add your client IP to the firewall rules

### Local Tools

```bash
# Install sqlcmd (macOS)
brew install sqlcmd

# Install Python dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Azure DevOps Boards (Ticket Workflow)

1. Go to: **<https://dev.azure.com>** and create or use an existing organization
2. Create a project for tracking demo work items
3. Install the CLI:

```bash
# Install Azure CLI (macOS)
brew install azure-cli

# Add Azure DevOps extension
az extension add --name azure-devops

# Login and configure defaults
az login
az devops configure --defaults organization=$AZURE_DEVOPS_ORG project=$AZURE_DEVOPS_PROJECT
```

### Azure Functions (Daily Sync Automation)

> **Optional** — only needed if you want to deploy the automated daily sync.

1. Install Azure Functions Core Tools:

```bash
# macOS
brew install azure-functions-core-tools@4
```

2. Create the Azure resources:

```bash
# Create a resource group
az group create --name patent-intelligence-rg --location westus2

# Create a storage account (required by Azure Functions)
az storage account create --name patentsyncstore --resource-group patent-intelligence-rg --location westus2 --sku Standard_LRS

# Create the Function App (Consumption plan, Python 3.12)
az functionapp create \
  --name <your-function-app-name> \
  --resource-group patent-intelligence-rg \
  --storage-account patentsyncstore \
  --consumption-plan-location westus2 \
  --runtime python --runtime-version 3.12 \
  --functions-version 4 --os-type Linux
```

3. Configure Application Settings (the Azure SQL variables from `.env`; arXiv needs no key):

```bash
source .env
az functionapp config appsettings set \
  --name <your-function-app-name> \
  --resource-group patent-intelligence-rg \
  --settings \
    AZURE_SQL_SERVER="$AZURE_SQL_SERVER" \
    AZURE_SQL_DATABASE="$AZURE_SQL_DATABASE" \
    AZURE_SQL_USER="$AZURE_SQL_USER" \
    AZURE_SQL_PASSWORD="$AZURE_SQL_PASSWORD"
```

4. Allow Azure services through the SQL firewall:

```bash
az sql server firewall-rule create \
  --resource-group patent-intelligence-rg \
  --server <your-sql-server-name> \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
```

5. Deploy:

```bash
cd azure_function && func azure functionapp publish <your-function-app-name> --python
```

### Verify Setup

```bash
# Test arXiv API (no key needed)
python3 -c "from tools.arxiv_search import search_by_title; print('OK' if search_by_title('large language models', limit=1) else 'FAILED')"

# Test Azure SQL
sqlcmd -S yourserver.database.windows.net -d PatentIntelligence -U sqladmin -P 'YourPass' -Q "SELECT 1 AS connected"

# Test pyodbc
python3 -c "import pyodbc; print('OK')"

# Test Azure Functions Core Tools (optional)
func --version
```

---

## Get Started

<div align="center">

| | Resource | Link |
|:--:|:---------|:-----|
| 🤖 | **Claude Code** | [claude.ai/download](https://claude.ai/download) |
| ☁️ | **Azure SQL Free Tier** | [aka.ms/azuresqlhub](https://aka.ms/azuresqlhub) |
| 📊 | **arXiv API** | [info.arxiv.org/help/api](https://info.arxiv.org/help/api/index.html) |
| 💻 | **This Repository** | [github.com/kyle-chalmers/azure-sql-patent-intelligence](https://github.com/kyle-chalmers/azure-sql-patent-intelligence) |

</div>

---

## Video Description Links

| Resource | Link |
|:---------|:-----|
| Meetup presentation | [Arizona Data Platform User Group](https://www.meetup.com/arizona-data-platform-user-group/events/312313644/) |
| Azure Functions docs | [learn.microsoft.com/azure-functions](https://learn.microsoft.com/en-us/azure/azure-functions/) |
| Azure Functions Python guide | [learn.microsoft.com/azure-functions-python](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python) |
| Azure Functions Core Tools | [learn.microsoft.com/functions-run-local](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local) |
| Azure SQL free tier | [aka.ms/azuresqlhub](https://aka.ms/azuresqlhub) |
| Azure SQL free tier docs | [learn.microsoft.com/azure-sql-free-offer](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer) |
| sqlcmd docs | [learn.microsoft.com/sqlcmd-utility](https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility) |
| arXiv API docs | [info.arxiv.org/help/api](https://info.arxiv.org/help/api/index.html) |
| Claude Code | [claude.ai/download](https://claude.ai/download) |
| This repo | [github.com/kyle-chalmers/azure-sql-patent-intelligence](https://github.com/kyle-chalmers/azure-sql-patent-intelligence) |

---

<div align="center">

## More From KC Labs AI

</div>

<details>
<summary><b>Video Tutorials</b> <sup>(click to expand)</sup></summary>

| Video | Description | |
|:------|:------------|:---:|
| **FUTURE PROOF Your Data Career with this Claude Code Deep Dive** | Complete guide to Claude Code for data teams | [Watch](https://www.youtube.com/watch?v=g4g4yBcBNuE) |
| **UPDATE to settings.json Chapter** | Settings.json updates from the Deep Dive | [Watch](https://youtu.be/WKt28ytMl3c) |
| **The AI Integration Every Data Professional Needs** | Using Claude Code with Snowflake | [Watch](https://www.youtube.com/watch?v=q1y7M5mZkkE) |
| **Claude Code Makes Databricks Easy** | Jobs, notebooks, SQL & Unity Catalog | [Watch](https://www.youtube.com/watch?v=5_q7j-k8DbM) |
| **Integrate Claude in Your Jira Workflow** | Jira/Confluence integration guide | [Watch](https://www.youtube.com/watch?v=WRvgMzYaIVo) |
| **Skip S3 and Athena in the AWS Console** | CLI + Claude Code for AWS data lakes | [Watch](https://www.youtube.com/watch?v=kCUTStWwErg) |
| **Use AI to Build Better Data Infrastructure** | Context Engineering with PRP Framework | [Watch](https://youtu.be/DUK39XqEVm0) |

</details>

---

<div align="center">

## Upcoming: AZ Tech Week 2026

| Event | Date | Details |
|:------|:-----|:--------|
| **The Practical AI Playbook Workshop** | Wed, Apr 8 | Hands-on AI tools workshop at 1951@SkySong, Scottsdale |
| **Sat. Morning Hike, Connect, & Coffee** | Sat, Apr 11 | Casual networking hike at Phoenix Mountain Preserve |

</div>

---

<div align="center">

### Scan to Connect

| **YouTube** | **LinkedIn** | **GitHub** | **KC Labs AI** |
| :---: | :---: | :---: | :---: |
| <img src="./qr_codes/youtube_qr.png" width="150" alt="YouTube QR"> | <img src="./qr_codes/linkedin_qr.png" width="150" alt="LinkedIn QR"> | <img src="./qr_codes/repo_qr.png" width="150" alt="GitHub QR"> | <img src="./qr_codes/kclabs_qr.png" width="150" alt="KC Labs QR"> |

YouTube (subscribe for more data + AI content): https://www.youtube.com/channel/UCkRi29nXFxNBuPhjseoB6AQ
LinkedIn: https://www.linkedin.com/in/kylechalmers/
This repo: https://github.com/kyle-chalmers/azure-sql-patent-intelligence
KC Labs AI: https://kclabs.ai/

AZ Tech Week 2026:
The Practical AI Playbook Workshop (Wed, Apr 8 - Scottsdale): https://partiful.com/e/VPy2EpNYQFppO6ZQA17n
Sat Morning Hike, Connect, & Coffee (Sat, Apr 11 - Phoenix): https://partiful.com/e/vMiPKyrTML8yf8Gnf618

---

*Thank you for attending! Questions? Find me after the session or connect on LinkedIn.*

<sub>Made with Claude Code</sub>

</div>
