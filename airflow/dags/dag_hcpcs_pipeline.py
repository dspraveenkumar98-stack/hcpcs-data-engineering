from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_PATH = "/opt/hcpcs-data-engineering"


with DAG(
    dag_id="hcpcs_data_pipeline",
    start_date=datetime(2026, 9, 29),
    schedule=None,
    catchup=False,
    tags=["hcpcs", "data-engineering"],
) as dag:

    scrape = BashOperator(
        task_id="scrape_hcpcs",
        bash_command=(
            f"cd {PROJECT_PATH} && "
            "python scraper/scraper.py"
        ),
    )

    transform = BashOperator(
        task_id="transform_hcpcs",
        bash_command=(
            f"cd {PROJECT_PATH} && "
            "python transform/transform.py"
        ),
    )

    load = BashOperator(
        task_id="load_postgres",
        bash_command=(
            f"cd {PROJECT_PATH} && "
            "python database/loader.py"
        ),
    )

    data_quality = BashOperator(
        task_id="data_quality_checks",
        bash_command=(
            f"cd {PROJECT_PATH} && "
            "python tests/data_quality.py"
        ),
    )

    update_metrics = BashOperator(
        task_id="update_metrics",
        bash_command=(
            f"cd {PROJECT_PATH} && "
            "python database/update_metrics.py"
        ),
    )

    scrape >> transform >> load >> data_quality >> update_metrics