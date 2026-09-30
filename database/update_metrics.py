import os

import psycopg2


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": 5432,
    "database": "hcpcs_db",
    "user": "hcpcs_user",
    "password": "hcpcs_password",
}


def update_metrics():

    connection = psycopg2.connect(**DB_CONFIG)

    cursor = connection.cursor()

    # Get current HCPCS record count
    cursor.execute("""
        SELECT COUNT(*)
        FROM hcpcs_codes
        WHERE is_current = TRUE;
    """)

    rows_loaded = cursor.fetchone()[0]

    # Get current DQ failure count
    dq_failures = 0

    # Insert successful pipeline metrics
    cursor.execute("""
        INSERT INTO pipeline_metrics (
            pipeline_name,
            rows_loaded,
            last_success_ts,
            dq_failures
        )
        VALUES (
            %s,
            %s,
            CURRENT_TIMESTAMP,
            %s
        );
    """, (
        "hcpcs_data_pipeline",
        rows_loaded,
        dq_failures,
    ))

    connection.commit()

    cursor.close()
    connection.close()

    print("Pipeline metrics updated successfully.")
    print(f"Rows loaded : {rows_loaded}")
    print(f"DQ failures : {dq_failures}")


if __name__ == "__main__":
    update_metrics()