import json
import os
from pathlib import Path
from datetime import date

import psycopg2


TRANSFORMED_FOLDER = Path("transform/output")


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": 5432,
    "database": "hcpcs_db",
    "user": "hcpcs_user",
    "password": "hcpcs_password",
}


def get_latest_transformed_file():
    files = sorted(
        TRANSFORMED_FOLDER.glob("hcpcs_transformed_*.json")
    )

    if not files:
        raise FileNotFoundError(
            "No transformed JSON file found."
        )

    return files[-1]


def load_data():
    input_file = get_latest_transformed_file()

    print(f"Loading file: {input_file}")

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as file:
        records = json.load(file)

    print(f"Records found: {len(records)}")

    connection = psycopg2.connect(**DB_CONFIG)

    cursor = connection.cursor()

    inserted_count = 0
    skipped_count = 0
    updated_count = 0

    for record in records:

        hcpcs_code = record["hcpcs_code"]
        group_code = record["group_code"]
        category_name = record["category_name"]
        description = record["long_description"]
        desc_hash = record["desc_hash"]

        cursor.execute(
            """
            SELECT id, desc_hash, version
            FROM hcpcs_codes
            WHERE hcpcs_code = %s
              AND is_current = TRUE
            """,
            (hcpcs_code,)
        )

        existing_record = cursor.fetchone()

        # New HCPCS code
        if existing_record is None:

            cursor.execute(
                """
                INSERT INTO hcpcs_codes (
                    hcpcs_code,
                    group_code,
                    category_name,
                    long_description,
                    desc_hash,
                    effective_date,
                    is_current,
                    version
                )
                VALUES (%s, %s, %s, %s, %s, %s, TRUE, 1)
                """,
                (
                    hcpcs_code,
                    group_code,
                    category_name,
                    description,
                    desc_hash,
                    date.today(),
                )
            )

            inserted_count += 1

        else:

            existing_id, existing_hash, existing_version = existing_record

            # Description has not changed
            if existing_hash == desc_hash:

                skipped_count += 1

            # Description has changed
            else:

                cursor.execute(
                    """
                    UPDATE hcpcs_codes
                    SET
                        is_current = FALSE,
                        end_date = %s
                    WHERE id = %s
                    """,
                    (
                        date.today(),
                        existing_id,
                    )
                )

                cursor.execute(
                    """
                    INSERT INTO hcpcs_codes (
                        hcpcs_code,
                        group_code,
                        category_name,
                        long_description,
                        desc_hash,
                        effective_date,
                        is_current,
                        version
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s)
                    """,
                    (
                        hcpcs_code,
                        group_code,
                        category_name,
                        description,
                        desc_hash,
                        date.today(),
                        existing_version + 1,
                    )
                )

                updated_count += 1

    connection.commit()

    cursor.close()
    connection