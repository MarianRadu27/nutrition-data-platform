#!/usr/bin/env python3
"""Import external-source foods into source_foods.

This currently imports NEVO food definitions only, not nutrient values.
Use --dry-run first to preview counts without writing to the database.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
import os
from pathlib import Path
import sys

import pymysql
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"

NEVO_MAIN_FILE = (
    PROJECT_ROOT
    / "temp"
    / "EuropeNutrientsDBs"
    / "nevo"
    / "NEVO2025_v9.0.csv"
)

NEVO_DATA_SOURCE_CODE = "NEVO"

NEVO_SOURCE_CODE_COLUMN = "NEVO-code"
NEVO_NAME_ORIGINAL_COLUMN = "Voedingsmiddelnaam/Dutch food name"
NEVO_NAME_EN_COLUMN = "Engelse naam/Food name"
NEVO_CATEGORY_ORIGINAL_COLUMN = "Voedingsmiddelgroep"
NEVO_CATEGORY_EN_COLUMN = "Food group"
NEVO_QUANTITY_COLUMN = "Hoeveelheid/Quantity"
NEVO_NOTE_COLUMN = "Opmerking"
NEVO_TRACES_COLUMN = "Bevat sporen van/Contains traces of"
NEVO_FORTIFIED_COLUMN = "Is verrijkt met/Is fortified with"

REQUIRED_NEVO_COLUMNS = [
    NEVO_SOURCE_CODE_COLUMN,
    NEVO_NAME_ORIGINAL_COLUMN,
    NEVO_NAME_EN_COLUMN,
    NEVO_CATEGORY_ORIGINAL_COLUMN,
    NEVO_CATEGORY_EN_COLUMN,
    NEVO_QUANTITY_COLUMN,
]


@dataclass(frozen=True)
class SourceFood:
    """One food definition from one source."""

    data_source_code: str
    source_food_code: str
    food_name_original: str | None
    food_name_en: str | None
    food_name_ro: str | None
    category_original: str | None
    category_en: str | None
    category_ro: str | None
    basis: str | None
    notes: str | None


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


def build_notes(row: dict[str, str]) -> str | None:
    """Combine optional NEVO note-like fields into one notes value."""
    note_parts = []
    note = clean_text(row.get(NEVO_NOTE_COLUMN))
    traces = clean_text(row.get(NEVO_TRACES_COLUMN))
    fortified = clean_text(row.get(NEVO_FORTIFIED_COLUMN))

    if note:
        note_parts.append(f"note: {note}")

    if traces:
        note_parts.append(f"contains_traces_of: {traces}")

    if fortified:
        note_parts.append(f"is_fortified_with: {fortified}")

    return "\n".join(note_parts) if note_parts else None


def validate_columns(columns: list[str], required_columns: list[str]) -> None:
    missing = [column for column in required_columns if column not in columns]
    if missing:
        raise RuntimeError("Missing required columns: " + ", ".join(missing))


def read_nevo_source_foods() -> list[SourceFood]:
    """Read NEVO foods from the main NEVO CSV file."""
    if not NEVO_MAIN_FILE.exists():
        print(f"File not found: {NEVO_MAIN_FILE}", file=sys.stderr)
        raise SystemExit(1)

    with NEVO_MAIN_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter="|")
        columns = list(reader.fieldnames or [])
        validate_columns(columns, REQUIRED_NEVO_COLUMNS)

        foods: list[SourceFood] = []
        for row in reader:
            source_food_code = clean_text(row[NEVO_SOURCE_CODE_COLUMN])
            if source_food_code is None:
                continue

            foods.append(
                SourceFood(
                    data_source_code=NEVO_DATA_SOURCE_CODE,
                    source_food_code=source_food_code,
                    food_name_original=clean_text(row[NEVO_NAME_ORIGINAL_COLUMN]),
                    food_name_en=clean_text(row[NEVO_NAME_EN_COLUMN]),
                    food_name_ro=None,
                    category_original=clean_text(row[NEVO_CATEGORY_ORIGINAL_COLUMN]),
                    category_en=clean_text(row[NEVO_CATEGORY_EN_COLUMN]),
                    category_ro=None,
                    basis=normalize_basis(row[NEVO_QUANTITY_COLUMN]),
                    notes=build_notes(row),
                )
            )

    return foods


def fetch_data_source_ids(cursor) -> dict[str, int]:
    cursor.execute("SELECT id, code FROM data_sources")
    return {row["code"]: row["id"] for row in cursor.fetchall()}


def validate_required_seed_data(
    foods: list[SourceFood],
    data_source_ids: dict[str, int],
) -> None:
    """Fail early when required data_sources rows do not exist."""
    missing_sources = sorted(
        {food.data_source_code for food in foods}
        - set(data_source_ids)
    )

    if missing_sources:
        raise RuntimeError(
            "Missing data_sources rows: "
            + ", ".join(missing_sources)
            + ". Run migrations through 005 first."
        )


def upsert_source_foods(
    cursor,
    foods: list[SourceFood],
    data_source_ids: dict[str, int],
) -> None:
    """Insert or update source food definitions."""
    sql = """
        INSERT INTO source_foods (
          data_source_id,
          source_food_code,
          food_name_original,
          food_name_en,
          food_name_ro,
          category_original,
          category_en,
          category_ro,
          basis,
          notes
        ) VALUES (
          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) AS new
        ON DUPLICATE KEY UPDATE
          food_name_original = new.food_name_original,
          food_name_en = new.food_name_en,
          food_name_ro = new.food_name_ro,
          category_original = new.category_original,
          category_en = new.category_en,
          category_ro = new.category_ro,
          basis = new.basis,
          notes = new.notes
    """

    rows = [
        (
            data_source_ids[food.data_source_code],
            food.source_food_code,
            food.food_name_original,
            food.food_name_en,
            food.food_name_ro,
            food.category_original,
            food.category_en,
            food.category_ro,
            food.basis,
            food.notes,
        )
        for food in foods
    ]
    cursor.executemany(sql, rows)


def print_summary(foods: list[SourceFood]) -> None:
    """Print import summary for review."""
    by_source = Counter(food.data_source_code for food in foods)
    by_basis = Counter(food.basis or "(missing)" for food in foods)
    by_category = Counter(food.category_en or "(missing)" for food in foods)
    with_notes = sum(1 for food in foods if food.notes)

    print("Source food import summary")
    print("=" * 32)
    for source_code, count in sorted(by_source.items()):
        print(f"{source_code}: {count} foods")

    print()
    print("Basis counts")
    print("=" * 32)
    for basis, count in sorted(by_basis.items()):
        print(f"{basis}: {count}")

    print()
    print(f"Foods with notes: {with_notes}")

    print()
    print("First 10 English categories")
    print("=" * 32)
    for category, count in by_category.most_common(10):
        print(f"{category}: {count}")

    print()
    print("First 5 foods")
    print("=" * 32)
    for food in foods[:5]:
        print(
            f"- {food.source_food_code} | "
            f"{food.food_name_original or '-'} | "
            f"{food.food_name_en or '-'} | "
            f"{food.category_en or '-'} | "
            f"{food.basis or '-'}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import NEVO food definitions into source_foods."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read files and validate seed data without writing to the database.",
    )
    args = parser.parse_args()

    foods = read_nevo_source_foods()
    print_summary(foods)

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            data_source_ids = fetch_data_source_ids(cursor)
            validate_required_seed_data(foods, data_source_ids)

            if args.dry_run:
                print()
                print("Dry run only. No database changes were written.")
                return 0

            upsert_source_foods(cursor, foods, data_source_ids)
            connection.commit()
            print()
            print(f"Imported {len(foods)} source food definitions.")
            return 0
    except Exception as exc:
        connection.rollback()
        print(f"ERROR: source food import failed: {exc}", file=sys.stderr)
        return 1
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
