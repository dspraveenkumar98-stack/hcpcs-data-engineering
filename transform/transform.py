import json
import hashlib

from pathlib import Path
from datetime import datetime


RAW_FOLDER = Path("raw")
TRANSFORMED_FOLDER = Path("transform/output")


def calculate_desc_hash(description):
    """
    Create MD5 hash for HCPCS description.
    """

    normalized_description = description.strip().lower()

    return hashlib.md5(
        normalized_description.encode("utf-8")
    ).hexdigest()


def transform_record(record):
    """
    Normalize one HCPCS record.
    """

    hcpcs_code = record["hcpcs_code"].strip().upper()

    description = record["long_description"].strip()

    group_code = hcpcs_code[0]

    transformed_record = {
        "hcpcs_code": hcpcs_code,
        "group_code": group_code,
        "category_name": None,
        "long_description": description,
        "desc_hash": calculate_desc_hash(description)
    }

    return transformed_record


def main():

    print("Starting transformation...")

    raw_files = sorted(
        RAW_FOLDER.glob("hcpcs_*.json")
    )

    print(f"Raw files found: {len(raw_files)}")

    # Select latest snapshot for each HCPCS group
    latest_files = {}

    for file_path in raw_files:

        filename = file_path.stem

        # Example:
        # hcpcs_A_20260929_165200
        parts = filename.split("_")

        if len(parts) < 3:
            continue

        group_code = parts[1]

        latest_files[group_code] = file_path

    print(
        f"Latest snapshots selected: "
        f"{len(latest_files)}"
    )

    all_records = []

    for group_code, file_path in sorted(
        latest_files.items()
    ):

        print(
            f"Reading latest {group_code}: "
            f"{file_path}"
        )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            records = json.load(file)

            all_records.extend(records)

    print(
        f"\nTotal raw records: "
        f"{len(all_records)}"
    )

    transformed_records = []

    for record in all_records:

        transformed_record = transform_record(
            record
        )

        transformed_records.append(
            transformed_record
        )

    print(
        f"Total transformed records: "
        f"{len(transformed_records)}"
    )

    TRANSFORMED_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_file = (
        TRANSFORMED_FOLDER
        / f"hcpcs_transformed_{timestamp}.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            transformed_records,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"\nTransformed file created: "
        f"{output_file}"
    )

    print("\nFirst 5 records:")

    for record in transformed_records[:5]:
        print(record)


if __name__ == "__main__":
    main()