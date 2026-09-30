import os
import psycopg2


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": 5432,
    "database": "hcpcs_db",
    "user": "hcpcs_user",
    "password": "hcpcs_password",
}


def run_data_quality_checks():

    connection = psycopg2.connect(**DB_CONFIG)

    cursor = connection.cursor()

    print("Starting data quality checks...\n")

    # Check for NULL HCPCS codes
    cursor.execute("""
        SELECT COUNT(*)
        FROM hcpcs_codes
        WHERE hcpcs_code IS NULL
          AND is_current = TRUE;
    """)

    null_codes = cursor.fetchone()[0]

    print(f"NULL HCPCS codes: {null_codes}")


    # Check for NULL descriptions
    cursor.execute("""
        SELECT COUNT(*)
        FROM hcpcs_codes
        WHERE long_description IS NULL
          AND is_current = TRUE;
    """)

    null_descriptions = cursor.fetchone()[0]

    print(f"NULL descriptions: {null_descriptions}")


    # Check for duplicate current HCPCS codes
    cursor.execute("""
        SELECT hcpcs_code, COUNT(*)
        FROM hcpcs_codes
        WHERE is_current = TRUE
        GROUP BY hcpcs_code
        HAVING COUNT(*) > 1;
    """)

    duplicate_codes = cursor.fetchall()

    print(
        f"Duplicate current HCPCS codes: "
        f"{len(duplicate_codes)}"
    )


    # Check current record count
    cursor.execute("""
        SELECT COUNT(*)
        FROM hcpcs_codes
        WHERE is_current = TRUE;
    """)

    current_records = cursor.fetchone()[0]

    print(f"Current records: {current_records}")


    cursor.close()
    connection.close()


    # Fail pipeline if any data quality check fails
    if (
        null_codes > 0
        or null_descriptions > 0
        or len(duplicate_codes) > 0
    ):
        raise ValueError(
            "Data quality checks failed."
        )


    print("\nAll data quality checks passed.")


if __name__ == "__main__":
    run_data_quality_checks()