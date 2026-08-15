"""
CMS Healthcare Pipeline DAG
Orchestrates: validate → ingest → dbt run → dbt test
Schedule: Weekly (every Sunday at midnight)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'nelson',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def run_data_ingestion():
    import sys
    sys.path.insert(0, '/opt/airflow')
    from ingestion.cms_ingest import run_ingestion
    run_ingestion()


def log_start():
    print(f"CMS Pipeline starting at {datetime.now()}")


def log_end():
    print(f"CMS Pipeline completed at {datetime.now()}")


with DAG(
    dag_id='cms_health_pipeline',
    default_args=default_args,
    description='Weekly CMS healthcare data pipeline',
    schedule_interval='@weekly',
    start_date=days_ago(1),
    catchup=False,
    tags=['healthcare', 'cms', 'snowflake', 'dbt'],
) as dag:

    log_start_task = PythonOperator(
        task_id='log_start',
        python_callable=log_start,
    )

    ingest_task = PythonOperator(
        task_id='ingest_cms_data',
        python_callable=run_data_ingestion,
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd /opt/airflow/dbt_project && dbt run',
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='cd /opt/airflow/dbt_project && dbt test',
    )

    log_end_task = PythonOperator(
        task_id='log_end',
        python_callable=log_end,
    )

    log_start_task >> ingest_task >> dbt_run >> dbt_test >> log_end_task