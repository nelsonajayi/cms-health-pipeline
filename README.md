# CMS Healthcare Analytics Pipeline

An end-to-end ELT data pipeline analyzing 28 million rows of public CMS Medicare data to surface population health insights on hospital readmissions and drug prescribing patterns across the United States.

Built on the modern data stack: **Snowflake · dbt · Apache Airflow · Python · Streamlit · GitHub Actions**

---

## The Business Problem

Hospital readmissions are one of the most expensive and preventable problems in US healthcare. CMS tracks which hospitals send patients home who return too soon, and penalizes those hospitals financially. Understanding which states, conditions, and hospitals drive the highest readmission rates is a genuine population health analytics problem with direct policy implications.

At the same time, Medicare drug spending is a national economic issue. Understanding which drugs cost the most, which providers prescribe the most, and where costs concentrate geographically gives policymakers, payers, and healthcare organizations the information they need to make smarter decisions.

This pipeline answers both questions using real, publicly available government data.

---

## Architecture

CMS.gov (Raw CSVs)
│
▼ Great Expectations validation
│
▼ Python ingestion (pandas + snowflake-connector)
│
Snowflake RAW Schema
├── RAW_HOSPITAL_READMISSIONS (18,330 rows)
├── RAW_DRUG_PRESCRIBING (25,869,521 rows)
└── RAW_PROVIDER_ENROLLMENT (2,981,799 rows)
│
▼ dbt staging models (views)
│
Snowflake STAGING Schema
├── STG_HOSPITAL_READMISSIONS (cleaned, typed)
├── STG_DRUG_PRESCRIBING (cleaned, typed)
└── STG_PROVIDER_ENROLLMENT (cleaned, typed)
│
▼ dbt mart models (tables)
│
Snowflake MARTS Schema
├── MART_HOSPITAL_READMISSIONS (306 rows — state/condition aggregates)
└── MART_DRUG_ANALYSIS (2,539 rows — national drug summary)
│
▼ Streamlit dashboard
│
Interactive Population Health Dashboard

Orchestrated by **Apache Airflow** (weekly schedule) | Tested automatically by **GitHub Actions** CI/CD

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Cloud Data Warehouse | Snowflake |
| Data Transformation | dbt 1.12 |
| Pipeline Orchestration | Apache Airflow 2.8 (Docker Compose) |
| Data Quality | Great Expectations |
| Visualization | Streamlit + Plotly |
| CI/CD | GitHub Actions |
| Language | Python 3.11 |
| Infrastructure | Docker + WSL 2 (Windows 11) |

---

## Datasets

All datasets are free and publicly available from **data.cms.gov**:

**Hospital Readmissions Reduction Program**
Hospital-level excess readmission ratios for major conditions (heart failure, pneumonia, hip/knee replacement, COPD). Hospitals above ratio 1.0 face CMS payment penalties.

**Medicare Part D Prescribers by Provider and Drug (2022)**
25.8 million records showing every Medicare provider's drug prescribing patterns — drug names, claim counts, and total Medicare cost. One of the largest publicly available healthcare datasets.

**Medicare Fee-for-Service Public Provider Enrollment (2026)**
2.98 million enrolled Medicare providers with specialty, location, and enrollment details. The reference table linking prescribers to their demographics.

---

## Key Findings

- States in the Southeast consistently show higher excess readmission ratios for heart failure than the national average
- The top 20 drugs by Medicare cost account for a disproportionate share of total Part D spending
- Significant variation exists in cost per claim across drug categories — some high-volume drugs are low cost while some low-volume drugs are extremely expensive per claim
- Geographic prescribing patterns vary significantly by specialty and drug class

---

## Pipeline Flow

Every Sunday at midnight, Airflow triggers the pipeline:

1. **Validate** — Great Expectations checks data quality before loading
2. **Ingest** — Python reads CSVs and bulk-loads to Snowflake RAW schema
3. **Stage** — dbt staging models clean and type-cast raw data into views
4. **Mart** — dbt mart models aggregate into business-ready tables
5. **Test** — 15 dbt data quality tests assert no nulls and valid values
6. **Serve** — Streamlit dashboard reads live from MARTS on user request

---

## Project Structure

cms-health-pipeline/
├── .github/workflows/
│ └── dbt_test.yml # GitHub Actions CI/CD
├── dags/
│ └── cms_pipeline_dag.py # Airflow DAG
├── dbt_project/
│ ├── macros/
│ │ └── generate_schema_name.sql
│ ├── models/
│ │ ├── staging/ # Cleaning and type casting
│ │ └── marts/ # Business aggregations
│ └── dbt_project.yml
├── ingestion/
│ └── cms_ingest.py # Python ingestion script
├── dashboard/
│ └── app.py # Streamlit dashboard
├── validation/
│ └── cms_expectations.py # Data quality checks
├── docker-compose.yml # Airflow + PostgreSQL
├── requirements.txt
└── .env.example

---

## How to Run

### Prerequisites
- Python 3.11+ with Anaconda
- Docker Desktop with WSL 2 (Windows) or Docker (Mac/Linux)
- Snowflake free trial account
- Git and GitHub account

### Setup

**1. Clone the repository:**
```bash
git clone git@github.com:nelsonajayi/cms-health-pipeline.git
cd cms-health-pipeline
```

**2. Install dependencies:**
```bash
python -m pip install -r requirements.txt
```

**3. Configure credentials:**
```bash
cp .env.example .env
# Edit .env with your Snowflake credentials
```

**4. Set up Snowflake:**

Run the SQL in `docs/snowflake_setup.sql` in your Snowflake worksheet to create the database, schemas, warehouse, role, and tables.

**5. Download CMS data:**

- Hospital Readmissions: https://data.cms.gov/provider-data/dataset/9n3s-kdb3
- Drug Prescribing (2022): https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/medicare-part-d-prescribers-by-provider-and-drug
- Provider Enrollment: https://data.cms.gov/provider-characteristics/medicare-provider-supplier-enrollment/medicare-fee-for-service-public-provider-enrollment

Place CSV files in `ingestion/data/` named:
- `hospital_readmissions.csv`
- `drug_prescribing.csv`
- `provider_enrollment.csv`

**6. Run ingestion:**
```bash
python ingestion/cms_ingest.py
```

**7. Run dbt:**
```bash
cd dbt_project
dbt run
dbt test
dbt docs generate && dbt docs serve
```

**8. Start dashboard:**
```bash
streamlit run dashboard/app.py
```

**9. Start Airflow (for scheduled runs):**
```bash
docker-compose up airflow-init
docker-compose up -d
# Open http://localhost:8080 (airflow/airflow)
```

---

## dbt Model Lineage

cms_raw (sources)
├── raw_hospital_readmissions
├── raw_drug_prescribing
└── raw_provider_enrollment
│
▼ staging models
├── stg_hospital_readmissions ──► mart_hospital_readmissions
├── stg_drug_prescribing ──► mart_drug_analysis
└── stg_provider_enrollment

Run `dbt docs serve` to view the interactive lineage graph in your browser.

---

## Data Quality

15 automated dbt tests run on every pipeline execution and every GitHub push:

- `not_null` tests on all primary keys and critical columns
- Source freshness checks ensuring raw data is current
- Value range validation on readmission ratios

GitHub Actions runs the full test suite on every commit to main. A red X on any commit means a data quality test failed.

---

## Author

**Oluwagbemiga Nelson Ajayi, PhD**
Information Systems | Data Science Specialization

[LinkedIn](https://www.linkedin.com/in/oluwagbemiga-ajayi-phd-28565b90) | [GitHub](https://github.com/nelsonajayi)

*PhD-trained data engineer with 8+ years across enterprise cloud (AWS), healthcare (VA Medical Center), and defense research (Army Research Lab). Published peer-reviewed research in Diabetes Care and IEEE on healthcare analytics and cybersecurity.*

---

## License

Data sourced from CMS.gov is in the public domain. Code in this repository is available under the MIT License.