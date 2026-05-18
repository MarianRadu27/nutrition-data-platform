#!/usr/bin/env python3
"""Profile the NEVO dataset before importing it into the database.

This script does not modify the database. It only reads the source CSV files
and prints useful information about their structure and data quality.
"""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

NEVO_DIR = PROJECT_ROOT / "temp" / "EuropeNutrientsDBs" / "nevo"
MAIN_FILE = NEVO_DIR / "NEVO2025_v9.0.csv"
NUTRIENTS_FILE = NEVO_DIR / "NEVO2025_v9.0_Nutrienten_Nutrients.csv"
DETAILS_FILE = NEVO_DIR / "NEVO2025_v9.0_Details.csv"

CATEGORY_COLUMN = "Food group"
CODE_COLUMN = "NEVO-code"
ENGLISH_NAME_COLUMN = "Engelse naam/Food name"
QUANTITY_COLUMN = "Hoeveelheid/Quantity"
FIRST_NUTRIENT_COLUMN = "ENERCJ (kJ)"
FIBER_COLUMN = "FIBT (g)"

MAIN_NUTRIENTS = [
    "ENERCC (kcal)",
    "PROT (g)",
    "CHO (g)",
    "FAT (g)",
    "FIBT (g)",
]

REQUIRED_MAIN_COLUMNS = [
    CATEGORY_COLUMN,
    CODE_COLUMN,
    ENGLISH_NAME_COLUMN,
    QUANTITY_COLUMN,
    FIRST_NUTRIENT_COLUMN,
    *MAIN_NUTRIENTS,
]


def read_pipe_csv(path: Path) -> list[dict[str, str]]:
    """Read a pipe-delimited NEVO CSV file into dictionaries."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter="|")
        return list(reader)


def get_columns(rows: list[dict[str, str]]) -> list[str]:
    """Return the CSV column names from the first row."""
    return list(rows[0].keys())


def find_missing_columns(columns: list[str], required_columns: list[str]) -> list[str]:
    """Find expected columns that are not present in the parsed CSV header."""
    return [column for column in required_columns if column not in columns]


def split_metadata_and_nutrient_columns(
    columns: list[str],
) -> tuple[list[str], list[str]]:
    """Split the NEVO main columns into food metadata and nutrient columns."""
    first_nutrient_index = columns.index(FIRST_NUTRIENT_COLUMN)
    metadata_columns = columns[:first_nutrient_index]
    nutrient_columns = columns[first_nutrient_index:]
    return metadata_columns, nutrient_columns


def print_main_file_profile(
    path: Path,
    rows: list[dict[str, str]],
    columns: list[str],
) -> None:
    """Print basic row and column information for the main NEVO file."""
    print("NEVO main file profile")
    print("======================")
    print(f"File: {path}")
    print(f"Rows: {len(rows)}")
    print(f"Columns: {len(columns)}")
    print()
    print("First 15 columns:")
    for column in columns[:15]:
        print(f"- {column}")


def print_categories(rows: list[dict[str, str]]) -> None:
    """Print distinct English food groups."""
    categories = sorted(
        {row[CATEGORY_COLUMN] for row in rows if row[CATEGORY_COLUMN]}
    )

    print()
    print(f"Categories: {len(categories)}")
    print("First 20 categories:")
    for category in categories[:20]:
        print(f"- {category}")


def print_first_foods(rows: list[dict[str, str]]) -> None:
    """Print a small sample of foods to verify identity columns."""
    print()
    print("First 10 foods:")
    for row in rows[:10]:
        print(
            f"- {row[CODE_COLUMN]} | "
            f"{row[CATEGORY_COLUMN]} | "
            f"{row[ENGLISH_NAME_COLUMN]} | "
            f"{row[QUANTITY_COLUMN]}"
        )


def count_values(rows: list[dict[str, str]], column: str) -> dict[str, int]:
    """Count how many times each value appears in one column."""
    counts: dict[str, int] = {}
    for row in rows:
        value = row[column] or "(blank)"
        counts[value] = counts.get(value, 0) + 1
    return counts


def print_quantity_profile(rows: list[dict[str, str]]) -> None:
    """Print distinct quantity bases and their row counts."""
    quantities = sorted({row[QUANTITY_COLUMN] for row in rows if row[QUANTITY_COLUMN]})
    quantity_counts = count_values(rows, QUANTITY_COLUMN)

    print()
    print(f"Quantity values: {len(quantities)}")
    for quantity in quantities:
        print(f"- {quantity}")

    print()
    print("Quantity counts:")
    for quantity, count in sorted(quantity_counts.items()):
        print(f"- {quantity}: {count}")


def print_main_nutrient_missing_values(rows: list[dict[str, str]]) -> None:
    """Print present/missing counts for the main calculator-style nutrients."""
    print()
    print("Main nutrient missing values:")
    for nutrient in MAIN_NUTRIENTS:
        missing_count = sum(1 for row in rows if not row[nutrient])
        present_count = len(rows) - missing_count
        print(f"- {nutrient}: present={present_count}, missing={missing_count}")


def print_foods_missing_fiber(rows: list[dict[str, str]]) -> None:
    """Print foods where dietary fibre is missing."""
    print()
    print("Foods missing fiber:")
    for row in rows:
        if not row[FIBER_COLUMN]:
            print(
                f"- {row[CODE_COLUMN]} | "
                f"{row[CATEGORY_COLUMN]} | "
                f"{row[ENGLISH_NAME_COLUMN]} | "
                f"{row[QUANTITY_COLUMN]}"
            )


def find_duplicate_codes(rows: list[dict[str, str]]) -> tuple[set[str], list[str]]:
    """Return unique NEVO codes and any repeated codes."""
    seen_codes: set[str] = set()
    duplicate_codes: list[str] = []

    for row in rows:
        code = row[CODE_COLUMN]
        if code in seen_codes:
            duplicate_codes.append(code)
        else:
            seen_codes.add(code)

    return seen_codes, duplicate_codes


def print_code_uniqueness(rows: list[dict[str, str]]) -> None:
    """Print whether NEVO-code is unique in the main file."""
    seen_codes, duplicate_codes = find_duplicate_codes(rows)

    print()
    print(f"Unique NEVO codes: {len(seen_codes)}")
    print(f"Duplicate NEVO codes: {len(duplicate_codes)}")

    if duplicate_codes:
        print("First duplicate codes:")
        for code in duplicate_codes[:20]:
            print(f"- {code}")


def print_nutrient_column_profile(
    metadata_columns: list[str],
    nutrient_columns: list[str],
) -> None:
    """Print how the main file columns split into metadata and nutrients."""
    print()
    print(f"Metadata columns: {len(metadata_columns)}")
    print(f"Nutrient columns: {len(nutrient_columns)}")
    print(f"Total {len(metadata_columns + nutrient_columns)}")
    print("First 20 nutrient columns:")
    for column in nutrient_columns[:20]:
        print(f"- {column}")


def print_nutrient_dictionary_profile(
    path: Path,
    nutrient_dictionary: list[dict[str, str]],
) -> None:
    """Print basic information from the NEVO nutrient dictionary."""
    dictionary_codes = get_dictionary_codes(nutrient_dictionary)
    duplicate_code_counts = find_duplicate_nutrient_code_counts(nutrient_dictionary)

    print()
    print("Nutrient dictionary profile")
    print("===========================")
    print(f"File: {path}")
    print(f"Rows: {len(nutrient_dictionary)}")
    print(f"Unique nutrient codes: {len(dictionary_codes)}")
    print(f"Duplicate nutrient code names: {len(duplicate_code_counts)}")

    if duplicate_code_counts:
        print("Duplicate nutrient codes:")
        for code, count in sorted(duplicate_code_counts.items()):
            print(f"- {code}: {count}")

    print("First 10 nutrient definitions:")
    for row in nutrient_dictionary[:10]:
        print(
            f"- {row['Nutrient-code']} | "
            f"{row['Component']} | "
            f"{row['Eenheid/Unit']}"
        )


def nutrient_code_from_column(column: str) -> str:
    """Convert a main-file column like 'ENERCC (kcal)' to 'ENERCC'."""
    return column.split(" (", 1)[0].strip()


def get_dictionary_codes(nutrient_dictionary: list[dict[str, str]]) -> set[str]:
    """Return unique nutrient codes from the nutrient dictionary."""
    return {
        row["Nutrient-code"].strip()
        for row in nutrient_dictionary
        if row["Nutrient-code"].strip()
    }


def find_duplicate_nutrient_code_counts(
    nutrient_dictionary: list[dict[str, str]],
) -> dict[str, int]:
    """Return nutrient dictionary codes that appear more than once."""
    code_counts: dict[str, int] = {}
    for row in nutrient_dictionary:
        code = row["Nutrient-code"].strip()
        code_counts[code] = code_counts.get(code, 0) + 1

    return {code: count for code, count in code_counts.items() if count > 1}


def get_main_nutrient_codes(nutrient_columns: list[str]) -> set[str]:
    """Return unique nutrient codes from the main-file nutrient columns."""
    return {nutrient_code_from_column(column) for column in nutrient_columns}


def print_nutrient_code_comparison(
    nutrient_columns: list[str],
    nutrient_dictionary: list[dict[str, str]],
) -> None:
    """Compare main-file nutrient codes with dictionary nutrient codes."""
    dictionary_codes = get_dictionary_codes(nutrient_dictionary)
    main_nutrient_codes = get_main_nutrient_codes(nutrient_columns)
    missing_from_dictionary = sorted(main_nutrient_codes - dictionary_codes)
    dictionary_not_in_main = sorted(dictionary_codes - main_nutrient_codes)

    print()
    print("Nutrient code comparison")
    print("========================")
    print(f"Codes in main file: {len(main_nutrient_codes)}")
    print(f"Codes in dictionary: {len(dictionary_codes)}")
    print(f"Main codes missing from dictionary: {len(missing_from_dictionary)}")
    for code in missing_from_dictionary[:20]:
        print(f"- {code}")

    print(f"Dictionary codes not in main file: {len(dictionary_not_in_main)}")
    for code in dictionary_not_in_main[:20]:
        print(f"- {code}")

def print_details_file_profile(
    path: Path,
    details_rows: list[dict[str, str]],
) -> None:
    """Print basic row and column information for the NEVO details file."""
    details_columns = get_columns(details_rows)

    print()
    print("NEVO details file profile")
    print("=========================")
    print(f"File: {path}")
    print(f"Rows: {len(details_rows)}")
    print(f"Columns: {len(details_columns)}")
    print("First 15 columns:")
    for column in details_columns[:15]:
        print(f"- {column}")


def get_main_food_codes(rows: list[dict[str, str]]) -> set[str]:
    """Return unique food codes from the NEVO main file."""
    return {row[CODE_COLUMN].strip() for row in rows if row[CODE_COLUMN].strip()}


def print_details_food_code_comparison(
    details_rows: list[dict[str, str]],
    main_food_codes: set[str],
) -> None:
    """Check whether every food code in Details also exists in the main file."""
    details_food_codes = {
        row[CODE_COLUMN].strip()
        for row in details_rows
        if row[CODE_COLUMN].strip()
    }

    missing_from_main = sorted(details_food_codes - main_food_codes)

    print()
    print("Details food code comparison")
    print("============================")
    print(f"Food codes in Details: {len(details_food_codes)}")
    print(f"Food codes in Main: {len(main_food_codes)}")
    print(f"Details food codes missing from Main: {len(missing_from_main)}")

    for code in missing_from_main[:20]:
        print(f"- {code}")


def print_details_nutrient_code_comparison(
    details_rows: list[dict[str, str]],
    dictionary_codes: set[str],
) -> None:
    """Check whether every nutrient code in Details exists in the dictionary."""
    details_nutrient_codes = {
        row["Nutrient-code"].strip()
        for row in details_rows
        if row["Nutrient-code"].strip()
    }

    missing_from_dictionary = sorted(details_nutrient_codes - dictionary_codes)

    print()
    print("Details nutrient code comparison")
    print("================================")
    print(f"Nutrient codes in Details: {len(details_nutrient_codes)}")
    print(f"Nutrient codes in dictionary: {len(dictionary_codes)}")
    print(f"Details nutrient codes missing from dictionary: {len(missing_from_dictionary)}")

    for code in missing_from_dictionary[:20]:
        print(f"- {code}")


def print_details_duplicate_food_nutrients(
    details_rows: list[dict[str, str]],
) -> None:
    """Check whether Details has duplicate food + nutrient rows."""
    pair_counts: dict[tuple[str, str], int] = {}

    for row in details_rows:
        food_code = row[CODE_COLUMN].strip()
        nutrient_code = row["Nutrient-code"].strip()
        pair = (food_code, nutrient_code)
        pair_counts[pair] = pair_counts.get(pair, 0) + 1

    duplicate_pairs = {
        pair: count
        for pair, count in pair_counts.items()
        if count > 1
    }

    print()
    print("Details duplicate food/nutrient pairs")
    print("=====================================")
    print(f"Duplicate food/nutrient pairs: {len(duplicate_pairs)}")

    for (food_code, nutrient_code), count in list(duplicate_pairs.items())[:20]:
        print(f"- food={food_code}, nutrient={nutrient_code}, count={count}")

def print_details_value_conflicts(
    details_rows: list[dict[str, str]],
) -> None:
    """Check whether the same food + nutrient has conflicting values or units."""
    values_by_pair: dict[tuple[str, str], set[tuple[str, str]]] = {}

    for row in details_rows:
        food_code = row[CODE_COLUMN].strip()
        nutrient_code = row["Nutrient-code"].strip()
        value = row["Gehalte/Value"].strip()
        unit = row["Eenheid/Unit"].strip()

        pair = (food_code, nutrient_code)
        value_signature = (value, unit)

        if food_code and nutrient_code:
            values_by_pair.setdefault(pair, set()).add(value_signature)

    conflict_pairs = {
        pair: value_signatures
        for pair, value_signatures in values_by_pair.items()
        if len(value_signatures) > 1
    }

    print()
    print("Details value conflicts")
    print("=======================")
    print(f"Food/nutrient pairs with different value or unit: {len(conflict_pairs)}")

    for (food_code, nutrient_code), value_signatures in list(conflict_pairs.items())[:20]:
        print(f"- food={food_code}, nutrient={nutrient_code}, values={value_signatures}")


def parse_decimal(value: str) -> Decimal | None:
    """Convert a CSV text value into a Decimal number, or None if it is blank."""
    cleaned_value = value.strip().replace(",", ".")

    if not cleaned_value:
        return None

    try:
        return Decimal(cleaned_value)
    except InvalidOperation:
        return None


def print_main_details_value_comparison(
    main_rows: list[dict[str, str]],
    details_rows: list[dict[str, str]],
) -> None:
    """Compare selected nutrient values between the main file and details file."""
    detail_values_by_pair: dict[tuple[str, str], set[Decimal | None]] = {}

    for row in details_rows:
        food_code = row[CODE_COLUMN].strip()
        nutrient_code = row["Nutrient-code"].strip()
        value = parse_decimal(row["Gehalte/Value"])

        if food_code and nutrient_code:
            pair = (food_code, nutrient_code)
            detail_values_by_pair.setdefault(pair, set()).add(value)

    mismatch_count = 0

    print()
    print("Main vs Details value comparison")
    print("================================")

    for row in main_rows:
        food_code = row[CODE_COLUMN].strip()

        for nutrient_column in MAIN_NUTRIENTS:
            nutrient_code = nutrient_code_from_column(nutrient_column)
            main_value = parse_decimal(row[nutrient_column])
            detail_values = detail_values_by_pair.get((food_code, nutrient_code), set())

            value_missing_in_both_files = main_value is None and not detail_values

            if value_missing_in_both_files:
                continue

            if main_value not in detail_values:
                mismatch_count += 1

                if mismatch_count <= 20:
                    print(
                        f"- food={food_code}, nutrient={nutrient_code}, "
                        f"main={main_value}, details={detail_values}"
                    )

    print(f"Main/details mismatches: {mismatch_count}")


def main() -> int:
    """Run the NEVO profiling checks."""
    if not MAIN_FILE.exists():
        print(f"File not found: {MAIN_FILE}")
        return 1

    if not NUTRIENTS_FILE.exists():
        print(f"File not found: {NUTRIENTS_FILE}")
        return 1

    if not DETAILS_FILE.exists():
        print(f"File not found: {DETAILS_FILE}")
        return 1

    rows = read_pipe_csv(MAIN_FILE)
    if not rows:
        print("No rows found.")
        return 0

    columns = get_columns(rows)
    missing_columns = find_missing_columns(columns, REQUIRED_MAIN_COLUMNS)
    if missing_columns:
        print("The main NEVO file is missing expected columns.")
        print("This can happen if the CSV was resaved with the wrong delimiter.")
        for column in missing_columns:
            print(f"- {column}")
        return 1

    metadata_columns, nutrient_columns = split_metadata_and_nutrient_columns(columns)
    nutrient_dictionary = read_pipe_csv(NUTRIENTS_FILE)
    details_rows = read_pipe_csv(DETAILS_FILE)
    main_food_codes = get_main_food_codes(rows)
    dictionary_codes = get_dictionary_codes(nutrient_dictionary)

    print_main_file_profile(MAIN_FILE, rows, columns)
    print_categories(rows)
    print_first_foods(rows)
    print_quantity_profile(rows)
    print_main_nutrient_missing_values(rows)
    print_foods_missing_fiber(rows)
    print_code_uniqueness(rows)
    print_nutrient_column_profile(metadata_columns, nutrient_columns)
    print_nutrient_dictionary_profile(NUTRIENTS_FILE, nutrient_dictionary)
    print_nutrient_code_comparison(nutrient_columns, nutrient_dictionary)
    print_details_file_profile(DETAILS_FILE, details_rows)
    print_details_food_code_comparison(details_rows, main_food_codes)
    print_details_nutrient_code_comparison(details_rows, dictionary_codes)
    print_details_duplicate_food_nutrients(details_rows)
    print_details_value_conflicts(details_rows)
    print_main_details_value_comparison(rows, details_rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
