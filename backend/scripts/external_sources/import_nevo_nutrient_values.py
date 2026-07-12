#!/usr/bin/env python3
"""Import NEVO nutrient values into source_food_nutrient_values.

This imports NEVO Details rows. It also imports NEVO source references because
the value rows point to reference_id.

Use --dry-run first to preview counts without writing to the database.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import os
from pathlib import Path
import sys

import pymysql
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"

NEVO_DETAILS_FILE = (
    PROJECT_ROOT
    / "temp"
    / "EuropeNutrientsDBs"
    / "nevo"
    / "NEVO2025_v9.0_Details.csv"
)

NEVO_DATA_SOURCE_CODE = "NEVO"

NEVO_FOOD_CODE_COLUMN = "NEVO-code"
NEVO_QUANTITY_COLUMN = "Hoeveelheid/Quantity"
NEVO_NUTRIENT_CODE_COLUMN = "Nutrient-code"
NEVO_VALUE_COLUMN = "Gehalte/Value"
NEVO_UNIT_COLUMN = "Eenheid/Unit"
NEVO_TRACE_FORTIFIED_COLUMN = "Spoor / Verrijkt/Trace / Fortified"
NEVO_SOURCE_CODE_COLUMN = "Broncode/Source code"
NEVO_REFERENCE_COLUMN = "Referentie/Reference"

REQUIRED_NEVO_DETAILS_COLUMNS = [
    NEVO_FOOD_CODE_COLUMN,
    NEVO_QUANTITY_COLUMN,
    NEVO_NUTRIENT_CODE_COLUMN,
    NEVO_VALUE_COLUMN,
    NEVO_UNIT_COLUMN,
    NEVO_TRACE_FORTIFIED_COLUMN,
    NEVO_SOURCE_CODE_COLUMN,
    NEVO_REFERENCE_COLUMN,
]

INSERT_CHUNK_SIZE = 5000


@dataclass(frozen=True)
class SourceReference:
    """One source reference row to import."""

    source_code: str
    reference_text: str


@dataclass(frozen=True)
class NevoNutrientValue:
    """One NEVO nutrient value row after source-code mapping."""

    source_food_code: str
    source_nutrient_code: str
    raw_value: str
    value: Decimal | None
    value_qualifier: str | None
    unit: str | None
    basis: str | None
    reference_source_code: str


def env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped if stripped else default


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def get_connection() -> pymysql.connections.Connection:
    """Open a MySQL connection using the backend .env settings."""
    load_dotenv(BACKEND_DIR / ".env")
    return pymysql.connect(
        host=env_str("DB_HOST", "127.0.0.1"),
        port=env_int("DB_PORT", 3307),
        user=env_str("DB_USER", "nutrition"),
        password=env_str("DB_PASSWORD", "nutritionpass"),
        database=env_str("DB_NAME", "nutrition"),
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )


def clean_text(value: str | None) -> str | None:
    """Return stripped text, treating empty strings as missing."""
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned if cleaned else None


def normalize_reference_text(value: str | None) -> str:
    """Collapse whitespace in reference text for stable comparison."""
    return " ".join((value or "").split())


def normalize_unit(value: str | None) -> str | None:
    """Normalize unit spelling while keeping storage simple."""
    cleaned = clean_text(value)
    if cleaned is None:
        return None

    cleaned = cleaned.replace("\u00c2\u00b5", "u")
    cleaned = cleaned.replace("\u00b5", "u")
    cleaned = cleaned.replace("\u03bc", "u")
    cleaned = cleaned.replace("�", "u")
    return cleaned.lower()


def normalize_basis(value: str | None) -> str | None:
    """Normalize NEVO quantity strings such as 'per 100g'."""
    cleaned = clean_text(value)
    if cleaned is None:
        return None

    compact = cleaned.lower().replace(" ", "")
    if compact in {"per100g", "per100gram", "per100grams"}:
        return "per_100g"

    if compact in {"per100ml", "per100milliliter", "per100milliliters"}:
        return "per_100ml"

    return cleaned.lower().replace(" ", "_")


def parse_decimal(value: str) -> Decimal | None:
    """Convert NEVO numeric text into Decimal."""
    cleaned = value.strip().replace(",", ".")
    if not cleaned:
        return None

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_value_qualifier(value: str | None) -> str | None:
    """Map NEVO trace/fortified markers into a compact qualifier."""
    cleaned = clean_text(value)
    if cleaned is None:
        return None

    normalized = cleaned.upper()
    if normalized == "TR":
        return "trace"

    if normalized == "+":
        return "fortified"

    return cleaned


def validate_columns(columns: list[str], required_columns: list[str]) -> None:
    missing = [column for column in required_columns if column not in columns]
    if missing:
        raise RuntimeError("Missing required columns: " + ", ".join(missing))


def make_conflict_reference_code(source_code: str, reference_text: str) -> str:
    """Create a stable code when one source code has multiple reference texts."""
    digest = hashlib.sha1(reference_text.encode("utf-8")).hexdigest()[:10]
    prefix = source_code[:89]
    return f"{prefix}#{digest}"


def build_reference_key_map(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str], str]:
    """Return the source_references.source_code to use for each raw reference."""
    texts_by_code: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        source_code = clean_text(row[NEVO_SOURCE_CODE_COLUMN])
        reference_text = normalize_reference_text(row[NEVO_REFERENCE_COLUMN])
        if source_code is None:
            continue
        texts_by_code[source_code].add(reference_text)

    reference_key_by_raw_pair: dict[tuple[str, str], str] = {}
    for source_code, reference_texts in texts_by_code.items():
        has_conflict = len(reference_texts) > 1

        for reference_text in reference_texts:
            key = (
                make_conflict_reference_code(source_code, reference_text)
                if has_conflict
                else source_code
            )
            reference_key_by_raw_pair[(source_code, reference_text)] = key

    return reference_key_by_raw_pair


def read_nevo_details() -> tuple[list[SourceReference], list[NevoNutrientValue]]:
    """Read NEVO Details rows and transform them into import objects."""
    if not NEVO_DETAILS_FILE.exists():
        print(f"File not found: {NEVO_DETAILS_FILE}", file=sys.stderr)
        raise SystemExit(1)

    with NEVO_DETAILS_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter="|")
        columns = list(reader.fieldnames or [])
        validate_columns(columns, REQUIRED_NEVO_DETAILS_COLUMNS)
        raw_rows = list(reader)

    reference_key_by_raw_pair = build_reference_key_map(raw_rows)

    references_by_key: dict[str, SourceReference] = {}
    value_signatures: set[tuple[str, str, str, str | None, str | None, str]] = set()
    values: list[NevoNutrientValue] = []

    for row in raw_rows:
        food_code = clean_text(row[NEVO_FOOD_CODE_COLUMN])
        nutrient_code = clean_text(row[NEVO_NUTRIENT_CODE_COLUMN])
        source_code = clean_text(row[NEVO_SOURCE_CODE_COLUMN])
        reference_text = normalize_reference_text(row[NEVO_REFERENCE_COLUMN])

        if food_code is None or nutrient_code is None or source_code is None:
            continue

        reference_key = reference_key_by_raw_pair[(source_code, reference_text)]
        references_by_key[reference_key] = SourceReference(
            source_code=reference_key,
            reference_text=reference_text,
        )

        raw_value = row[NEVO_VALUE_COLUMN].strip()
        unit = normalize_unit(row[NEVO_UNIT_COLUMN])
        basis = normalize_basis(row[NEVO_QUANTITY_COLUMN])
        value_qualifier = parse_value_qualifier(row[NEVO_TRACE_FORTIFIED_COLUMN])

        signature = (
            food_code,
            nutrient_code,
            raw_value,
            unit,
            basis,
            reference_key,
        )
        if signature in value_signatures:
            continue

        value_signatures.add(signature)
        values.append(
            NevoNutrientValue(
                source_food_code=food_code,
                source_nutrient_code=nutrient_code,
                raw_value=raw_value,
                value=parse_decimal(raw_value),
                value_qualifier=value_qualifier,
                unit=unit,
                basis=basis,
                reference_source_code=reference_key,
            )
        )

    references = sorted(references_by_key.values(), key=lambda item: item.source_code)
    return references, values


def fetch_nevo_data_source_id(cursor) -> int:
    cursor.execute("SELECT id FROM data_sources WHERE code = %s", (NEVO_DATA_SOURCE_CODE,))
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Missing NEVO row in data_sources. Run migrations through 005 first.")
    return int(row["id"])


def fetch_source_food_ids(cursor, data_source_id: int) -> dict[str, int]:
    cursor.execute(
        """
        SELECT id, source_food_code
        FROM source_foods
        WHERE data_source_id = %s
        """,
        (data_source_id,),
    )
    return {row["source_food_code"]: row["id"] for row in cursor.fetchall()}


def fetch_source_nutrient_ids(cursor, data_source_id: int) -> dict[str, int]:
    cursor.execute(
        """
        SELECT id, source_nutrient_code
        FROM source_nutrients
        WHERE data_source_id = %s
        """,
        (data_source_id,),
    )
    return {row["source_nutrient_code"]: row["id"] for row in cursor.fetchall()}


def fetch_reference_ids(cursor, data_source_id: int) -> dict[str, int]:
    cursor.execute(
        """
        SELECT id, source_code
        FROM source_references
        WHERE data_source_id = %s
        """,
        (data_source_id,),
    )
    return {row["source_code"]: row["id"] for row in cursor.fetchall()}


def validate_import_dependencies(
    values: list[NevoNutrientValue],
    food_ids: dict[str, int],
    nutrient_ids: dict[str, int],
) -> None:
    """Fail before writing when foods or nutrients are missing."""
    missing_food_codes = sorted(
        {value.source_food_code for value in values}
        - set(food_ids)
    )
    missing_nutrient_codes = sorted(
        {value.source_nutrient_code for value in values}
        - set(nutrient_ids)
    )

    if missing_food_codes:
        raise RuntimeError(
            "Missing NEVO source_foods rows. First missing codes: "
            + ", ".join(missing_food_codes[:20])
        )

    if missing_nutrient_codes:
        raise RuntimeError(
            "Missing NEVO source_nutrients rows. First missing codes: "
            + ", ".join(missing_nutrient_codes[:20])
        )


def iter_chunks(items: list, size: int):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def upsert_references(
    cursor,
    data_source_id: int,
    references: list[SourceReference],
) -> None:
    """Insert or update source references."""
    sql = """
        INSERT INTO source_references (
          data_source_id,
          source_code,
          reference_text
        ) VALUES (
          %s, %s, %s
        ) AS new
        ON DUPLICATE KEY UPDATE
          reference_text = new.reference_text
    """
    rows = [
        (data_source_id, reference.source_code, reference.reference_text)
        for reference in references
    ]

    for chunk in iter_chunks(rows, INSERT_CHUNK_SIZE):
        cursor.executemany(sql, chunk)


def delete_existing_nevo_values(cursor, data_source_id: int) -> None:
    """Remove existing NEVO value rows so the import is repeatable."""
    cursor.execute(
        """
        DELETE v
        FROM source_food_nutrient_values v
        JOIN source_foods f ON f.id = v.source_food_id
        WHERE f.data_source_id = %s
        """,
        (data_source_id,),
    )


def insert_values(
    cursor,
    values: list[NevoNutrientValue],
    food_ids: dict[str, int],
    nutrient_ids: dict[str, int],
    reference_ids: dict[str, int],
) -> None:
    """Insert NEVO nutrient value rows."""
    sql = """
        INSERT INTO source_food_nutrient_values (
          source_food_id,
          source_nutrient_id,
          raw_value,
          value,
          value_qualifier,
          unit,
          basis,
          reference_id
        ) VALUES (
          %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    rows = [
        (
            food_ids[value.source_food_code],
            nutrient_ids[value.source_nutrient_code],
            value.raw_value,
            value.value,
            value.value_qualifier,
            value.unit,
            value.basis,
            reference_ids[value.reference_source_code],
        )
        for value in values
    ]

    for chunk in iter_chunks(rows, INSERT_CHUNK_SIZE):
        cursor.executemany(sql, chunk)


def print_summary(
    references: list[SourceReference],
    values: list[NevoNutrientValue],
) -> None:
    """Print import summary for review."""
    basis_counts = Counter(value.basis or "(missing)" for value in values)
    unit_counts = Counter(value.unit or "(missing)" for value in values)
    qualifier_counts = Counter(value.value_qualifier or "(blank)" for value in values)

    print("NEVO nutrient value import summary")
    print("=" * 40)
    print(f"References to import: {len(references)}")
    print(f"Deduplicated value rows to import: {len(values)}")
    print(f"Unique foods: {len({value.source_food_code for value in values})}")
    print(f"Unique nutrients: {len({value.source_nutrient_code for value in values})}")

    print()
    print("Basis counts")
    print("=" * 40)
    for basis, count in sorted(basis_counts.items()):
        print(f"{basis}: {count}")

    print()
    print("Top units")
    print("=" * 40)
    for unit, count in unit_counts.most_common(10):
        print(f"{unit}: {count}")

    print()
    print("Value qualifier counts")
    print("=" * 40)
    for qualifier, count in qualifier_counts.most_common():
        print(f"{qualifier}: {count}")

    print()
    print("First 5 values")
    print("=" * 40)
    for value in values[:5]:
        print(
            f"- food={value.source_food_code}, "
            f"nutrient={value.source_nutrient_code}, "
            f"raw={value.raw_value}, "
            f"value={value.value}, "
            f"unit={value.unit}, "
            f"reference={value.reference_source_code}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import NEVO nutrient values into source_food_nutrient_values."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read files and validate database dependencies without writing.",
    )
    args = parser.parse_args()

    references, values = read_nevo_details()
    print_summary(references, values)

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            data_source_id = fetch_nevo_data_source_id(cursor)
            food_ids = fetch_source_food_ids(cursor, data_source_id)
            nutrient_ids = fetch_source_nutrient_ids(cursor, data_source_id)
            validate_import_dependencies(values, food_ids, nutrient_ids)

            if args.dry_run:
                print()
                print("Dry run only. No database changes were written.")
                return 0

            upsert_references(cursor, data_source_id, references)
            reference_ids = fetch_reference_ids(cursor, data_source_id)
            delete_existing_nevo_values(cursor, data_source_id)
            insert_values(cursor, values, food_ids, nutrient_ids, reference_ids)
            connection.commit()

            print()
            print(f"Imported {len(references)} references.")
            print(f"Imported {len(values)} NEVO nutrient value rows.")
            return 0
    except Exception as exc:
        connection.rollback()
        print(f"ERROR: NEVO nutrient value import failed: {exc}", file=sys.stderr)
        return 1
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
