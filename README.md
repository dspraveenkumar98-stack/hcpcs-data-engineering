# HCPCS Data Engineering Pipeline

A production-style data engineering project that extracts HCPCS code data from a public web source, stores raw snapshots, transforms and validates the data, loads it into PostgreSQL with SCD Type 2 support, orchestrates the pipeline using Apache Airflow, and provides monitoring and analytics through Metabase.

---

## 1. Project Overview

This project demonstrates an end-to-end data engineering pipeline for processing HCPCS (Healthcare Common Procedure Coding System) code data.

The pipeline performs the following activities:

1. Scrapes HCPCS code data from `hcpcsdata.com`
2. Stores the extracted data as raw JSON snapshots
3. Transforms and standardizes the raw data
4. Generates description hashes for change detection
5. Loads the data into PostgreSQL
6. Maintains historical changes using SCD Type 2 logic
7. Performs data quality checks
8. Orchestrates the complete workflow using Apache Airflow
9. Stores pipeline execution metrics
10. Visualizes data and pipeline metrics using Metabase

### Current Dataset

The current successful pipeline execution processed:

- **17 HCPCS code groups**
- **8,725 HCPCS records**
- **8,725 current PostgreSQL records**
- **0 duplicate current HCPCS codes**
- **0 data quality failures**

---

## 2. Architecture

```text
                    ┌──────────────────────┐
                    │    HCPCS Website     │
                    │    hcpcsdata.com      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Python Scraper     │
                    │ Requests + BS4       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     Raw JSON         │
                    │    Snapshots         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Transformation    │
                    │ Group + Hash + Clean │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     PostgreSQL       │
                    │   HCPCS Data + SCD2  │
                    └──────────┬───────────┘
                               │
                  ┌────────────┴────────────┐
                  │                         │
                  ▼                         ▼
        ┌──────────────────┐      ┌──────────────────┐
        │ Data Quality     │      │ Pipeline Metrics │
        │ Checks           │      │                  │
        └──────────────────┘      └────────┬─────────┘
                                           │
                                           ▼
                                  ┌──────────────────┐
                                  │    Metabase      │
                                  │    Dashboard     │
                                  └──────────────────┘

                 Apache Airflow orchestrates the pipeline
```

---

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Scraping and data transformation |
| Requests | HTTP requests |
| BeautifulSoup | HTML parsing |
| Pandas | Data processing support |
| PostgreSQL 18 | Data storage |
| psycopg2 | PostgreSQL connectivity |
| Apache Airflow 2.10.5 | Pipeline orchestration |
| Docker | Containerization |
| Docker Compose | Multi-container environment |
| pgAdmin | PostgreSQL administration |
| Metabase | Data visualization and monitoring |
| PowerShell | Local development environment |

---

## 4. Project Structure

```text
hcpcs-data-engineering/
│
├── scraper/
│   └── scraper.py
│
├── transform/
│   ├── transform.py
│   └── output/
│
├── database/
│   ├── schema.sql
│   ├── loader.py
│   └── update_metrics.py
│
├── airflow/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── dags/
│   │   └── hcpcs_pipeline.py
│   └── logs/
│
├── tests/
│   └── data_quality.py
│
├── raw/
│   └── hcpcs_*.json
│
├── logs/
│
├── config/
│
├── docker-compose.yml
├── requirements.txt
├── .gitignore
└── README.md
```

---

# 5. Data Source

The pipeline extracts HCPCS code information from:

**Source:** `https://hcpcsdata.com`

The source contains HCPCS code groups such as:

```text
A
B
C
E
G
H
J
K
L
M
P
Q
R
S
T
U
V
```

The current extraction contains **17 code groups** and **8,725 records**.

---

# 6. Data Extraction

The scraper is implemented in:

```text
scraper/scraper.py
```

The scraper uses:

- `requests`
- `BeautifulSoup`
- browser-style HTTP headers
- timeout handling
- HTML table parsing

The scraper first discovers the HCPCS code-group pages and then extracts:

```text
hcpcs_code
long_description
```

Example raw record:

```json
{
  "hcpcs_code": "A0001",
  "long_description": "Example description"
}
```

Each code group is stored as a timestamped JSON snapshot.

Example:

```text
raw/
├── hcpcs_A_20260929_165101.json
├── hcpcs_B_20260929_165101.json
├── hcpcs_C_20260929_165101.json
└── ...
```

This provides a simple raw-data landing layer and preserves extraction snapshots.

---

# 7. Data Transformation

Transformation logic is implemented in:

```text
transform/transform.py
```

The transformation process:

1. Reads the latest raw snapshot for each HCPCS group
2. Standardizes HCPCS codes to uppercase
3. Removes unnecessary whitespace
4. Derives the HCPCS group from the first character
5. Generates a description hash
6. Produces the transformed JSON dataset

### Transformed Structure

```json
{
  "hcpcs_code": "A0001",
  "group_code": "A",
  "category_name": null,
  "long_description": "Example description",
  "desc_hash": "..."
}
```

### Description Hash

An MD5 hash is generated from the normalized description.

The hash is used to identify whether an HCPCS description has changed between pipeline executions.

```text
description
      ↓
strip whitespace
      ↓
convert to lowercase
      ↓
MD5 hash
      ↓
desc_hash
```

`category_name` is currently kept as `NULL` because a separate category mapping was not available from the source data.

---

# 8. PostgreSQL Database

PostgreSQL 18 is used as the primary data store.

Database configuration:

```text
Database: hcpcs_db
User: hcpcs_user
Port: 5432
```

The PostgreSQL container is managed using Docker Compose.

---

# 9. Database Schema

## hcpcs_codes

The main table stores HCPCS code records and historical versions.

Important columns:

| Column | Description |
|---|---|
| id | Surrogate primary key |
| hcpcs_code | HCPCS procedure code |
| group_code | HCPCS code group |
| category_name | Category value when available |
| long_description | HCPCS description |
| desc_hash | Hash used for change detection |
| effective_date | Version effective date |
| end_date | Version end date |
| is_current | Indicates the active record |
| version | Record version |
| inserted_at | Insert timestamp |

Indexes are created for current HCPCS codes and HCPCS code lookups.

---

## pipeline_metrics

The pipeline metrics table stores execution-level monitoring information.

Important columns:

| Column | Description |
|---|---|
| pipeline_name | Pipeline identifier |
| rows_loaded | Number of current rows |
| last_success_ts | Last successful execution timestamp |
| dq_failures | Number of DQ failures |
| created_at | Metrics record creation time |

---

# 10. SCD Type 2 Implementation

The loader implements Slowly Changing Dimension Type 2 behavior for HCPCS descriptions.

The `desc_hash` is used to identify changes.

### Scenario 1 — New HCPCS Code

If a code does not exist:

```text
Insert new record
version = 1
is_current = TRUE
```

### Scenario 2 — Existing Code Without Changes

If the HCPCS code exists and the description hash is unchanged:

```text
No new record
Existing record remains current
```

### Scenario 3 — Existing Code With Description Change

If the description hash changes:

```text
Old record
    ↓
is_current = FALSE
end_date = current date
    ↓
New record
    ↓
version = previous version + 1
is_current = TRUE
```

This allows historical versions of changed HCPCS descriptions to be retained.

The SCD Type 2 logic was tested using an HCPCS record and the test history was subsequently cleaned up.

---

# 11. Data Loading

The loading logic is implemented in:

```text
database/loader.py
```

The loader:

1. Finds the latest transformed JSON file
2. Reads transformed records
3. Connects to PostgreSQL
4. Checks existing current records
5. Inserts new records
6. Skips unchanged records
7. Creates new versions when descriptions change
8. Maintains current/historical status

### Initial Load

The initial pipeline load inserted:

```text
8,725 records
```

### Rerun Validation

A subsequent rerun produced:

```text
New records:        0
Unchanged records:   8,725
Versioned records:   0
```

This confirms that unchanged records are not unnecessarily duplicated.

---

# 12. Data Quality

Data quality checks are implemented in:

```text
tests/data_quality.py
```

Current checks include:

### 1. NULL HCPCS Codes

```text
Expected: 0
Actual:   0
```

### 2. NULL Descriptions

```text
Expected: 0
Actual:   0
```

### 3. Duplicate Current HCPCS Codes

```text
Expected: 0
Actual:   0
```

### 4. Current Record Count

```text
Current records: 8,725
```

### Current Result

```text
All DQ checks passed.
```

---

# 13. Apache Airflow

Apache Airflow is used to orchestrate the complete data pipeline.

The DAG is:

```text
hcpcs_data_pipeline
```

The DAG contains five tasks.

```text
scrape_hcpcs
      ↓
transform_hcpcs
      ↓
load_postgres
      ↓
data_quality_checks
      ↓
update_metrics
```

### Airflow Tasks

| Task | Responsibility |
|---|---|
| scrape_hcpcs | Extract HCPCS data |
| transform_hcpcs | Transform raw data |
| load_postgres | Load data into PostgreSQL |
| data_quality_checks | Validate database data |
| update_metrics | Store pipeline metrics |

The DAG is currently configured for manual execution:

```python
schedule=None
```

with:

```python
catchup=False
```

---

# 14. Pipeline Metrics

After successful pipeline execution, metrics are stored in:

```text
pipeline_metrics
```

The current monitoring values include:

```text
Rows loaded:       8,725
DQ failures:       0
```

The metrics table currently contains multiple successful pipeline execution records.

---

# 15. Docker Environment

Docker Compose is used to run the project services.

Current services include:

```text
postgres
pgadmin
metabase
airflow-init
airflow-webserver
airflow-scheduler
```

### PostgreSQL

```text
localhost:5432
```

### pgAdmin

```text
http://localhost:5050
```

### Airflow

```text
http://localhost:8080
```

### Metabase

```text
http://localhost:3000
```

---

# 16. pgAdmin

pgAdmin is included for PostgreSQL administration and database inspection.

Connection details inside the Docker network:

```text
Host: postgres
Port: 5432
Database: hcpcs_db
Username: hcpcs_user
```

pgAdmin is available at:

```text
http://localhost:5050
```

---

# 17. Metabase Dashboard

Metabase is used to visualize HCPCS data and pipeline monitoring metrics.

The dashboard:

```text
HCPCS Data Engineering Dashboard
```

contains the following cards:

### Total HCPCS Codes

```text
8,725
```

### HCPCS Codes by Group

A bar chart showing the distribution of HCPCS records across the available code groups.

### Pipeline Runs

Current recorded pipeline executions:

```text
3
```

### Data Quality Failures

Current recorded DQ failures:

```text
0
```

Recommended dashboard layout:

```text
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ Total HCPCS Codes   │ Pipeline Runs       │ DQ Failures         │
│      8,725          │        3            │         0           │
└─────────────────────┴─────────────────────┴─────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│                    HCPCS Codes by Group                           │
└───────────────────────────────────────────────────────────────────┘
```

---

# 18. Local Setup

## Prerequisites

Install:

- Python 3.12
- Docker Desktop
- Git

Verify Python:

```powershell
python --version
```

Verify Docker:

```powershell
docker --version
```

Verify Docker Compose:

```powershell
docker compose version
```

---

# 19. Python Environment Setup

Create the virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell execution policy blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

# 20. Start Docker Services

From the project root:

```powershell
docker compose up -d
```

Check running containers:

```powershell
docker ps
```

Expected services include:

```text
hcpcs-postgres
hcpcs-pgadmin
hcpcs-metabase
hcpcs-airflow-webserver
hcpcs-airflow-scheduler
```

---

# 21. Run the Pipeline Manually

## Step 1 — Scrape

```powershell
python scraper/scraper.py
```

This creates timestamped JSON files under:

```text
raw/
```

---

## Step 2 — Transform

```powershell
python transform/transform.py
```

The transformed dataset is generated under:

```text
transform/output/
```

---

## Step 3 — Load PostgreSQL

```powershell
python database/loader.py
```

This performs inserts and SCD Type 2 processing.

---

## Step 4 — Run Data Quality Checks

```powershell
python tests/data_quality.py
```

Expected result:

```text
All DQ checks passed.
```

---

## Step 5 — Update Metrics

```powershell
python database/update_metrics.py
```

This records pipeline execution metrics in PostgreSQL.

---

# 22. Running Through Airflow

Open:

```text
http://localhost:8080
```

Login:

```text
Username: admin
Password: admin
```

Open:

```text
hcpcs_data_pipeline
```

Trigger the DAG manually.

The expected task sequence is:

```text
scrape_hcpcs
      ↓
transform_hcpcs
      ↓
load_postgres
      ↓
data_quality_checks
      ↓
update_metrics
```

---

# 23. Useful Database Queries

Connect to the `hcpcs_db` PostgreSQL database and run:

### Total Current HCPCS Records

```sql
SELECT COUNT(*)
FROM hcpcs_codes
WHERE is_current = TRUE;
```

Expected:

```text
8725
```

### Group Distribution

```sql
SELECT
    group_code,
    COUNT(*) AS record_count
FROM hcpcs_codes
WHERE is_current = TRUE
GROUP BY group_code
ORDER BY group_code;
```

### Check Duplicate Current Codes

```sql
SELECT
    hcpcs_code,
    COUNT(*) AS record_count
FROM hcpcs_codes
WHERE is_current = TRUE
GROUP BY hcpcs_code
HAVING COUNT(*) > 1;
```

Expected:

```text
0 rows
```

### Pipeline Metrics

```sql
SELECT
    pipeline_name,
    rows_loaded,
    last_success_ts,
    dq_failures,
    created_at
FROM pipeline_metrics
ORDER BY created_at DESC;
```

---

# 24. Validation Results

The current implementation has been validated with the following results:

```text
HCPCS Groups                  17
Total Raw Records          8,725
Total Transformed Records  8,725
Current DB Records         8,725
NULL HCPCS Codes               0
NULL Descriptions              0
Duplicate Current Codes        0
DQ Failures                    0
```

The pipeline has also been successfully executed through Airflow.

---

# 25. Error Handling and Troubleshooting

## Check Docker Containers

```powershell
docker ps
```

For stopped containers:

```powershell
docker ps -a
```

View PostgreSQL logs:

```powershell
docker logs hcpcs-postgres
```

View Airflow webserver logs:

```powershell
docker logs hcpcs-airflow-webserver
```

View Airflow scheduler logs:

```powershell
docker logs hcpcs-airflow-scheduler
```

View Metabase logs:

```powershell
docker logs hcpcs-metabase
```

---

## Restart Services

Restart Metabase: