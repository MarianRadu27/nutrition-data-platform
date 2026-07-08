#!/usr/bin/env python3
"""Import the main FoodsFinal Excel workbook into MySQL.

The workbook uses visual hierarchy rows:
- uppercase DA Code cells represent Category rows;
- Food Description-only rows represent Food group rows;
- rows with DA Code values represent Food Description rows.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from pprint import pformat
from typing import Any

import pandas as pd
import pymysql

BELOW_LIMIT_CALC_VALUE = 0.0
# Empty markers mean "unknown"; trace and below-limit markers are stored as zero for calculations.
NULL_NUMERIC_TOKENS = {"", "-", "\u2013", "\u2014"}
TRACE_NUMERIC_TOKENS = {"t", "tr", "trace"}
UNICODE_FRACTIONS = {
    "¼": "1/4",
    "½": "1/2",
    "¾": "3/4",
    "⅐": "1/7",
    "⅑": "1/9",
    "⅒": "1/10",
    "⅓": "1/3",
    "⅔": "2/3",
    "⅕": "1/5",
    "⅖": "2/5",
    "⅗": "3/5",
    "⅘": "4/5",
    "⅙": "1/6",
    "⅚": "5/6",
    "⅛": "1/8",
    "⅜": "3/8",
    "⅝": "5/8",
    "⅞": "7/8",
}

NUMERIC_COLUMNS = [
    # Column names here match the DB schema, not the Excel display labels.
    "wt_g",
    "h2o_g",
    "ener_kcal",
    "prot_g",
    "carbo_g",
    "fiber_g",
    "fat_g",
    "sat_g",
    "mono_g",
    "poly_g",
    "trans_g",
    "chol_mg",
    "calc_mg",
    "iron_mg",
    "magn_mg",
    "pota_mg",
    "sodi_mg",
    "zinc_mg",
    "vit_a_ug",
    "vit_e_mg",
    "thia_mg",
    "ribo_mg",
    "niac_mg",
    "vit_b6_mg",
    "fola_ug",
    "vit_c_mg",
    "vit_b12_ug",
    "sele_ug",
]

FOOD_COLUMNS = [
    "da_code",
    "subcategory_id",
    "food_description",
    "quantity",
    "measure",
    *NUMERIC_COLUMNS,
    "nutrient_value_notes",
]

HEADER_ALIAS_TO_DB = {
    # Excel headers are normalized before lookup, so "DA + Code" becomes "dacode".
    "dacode": "da_code",
    "fooddescription": "food_description",
    "ownsubcategory": "own_subcategory",
    "isownsubcategory": "own_subcategory",
    "quantity": "quantity",
    "measure": "measure",
    "wtg": "wt_g",
    "h2og": "h2o_g",
    "enerkcal": "ener_kcal",
    "protg": "prot_g",
    "carbog": "carbo_g",
    "fiberg": "fiber_g",
    "fatg": "fat_g",
    "sat": "sat_g",
    "mono": "mono_g",
    "poly": "poly_g",
    "trans": "trans_g",
    "cholmg": "chol_mg",
    "calcmg": "calc_mg",
    "ironmg": "iron_mg",
    "magnmg": "magn_mg",
    "potamg": "pota_mg",
    "sodimg": "sodi_mg",
    "zincmg": "zinc_mg",
    "vitaug": "vit_a_ug",
    "vitemga": "vit_e_mg",
    "vitemg": "vit_e_mg",
    "thiamg": "thia_mg",
    "ribomg": "ribo_mg",
    "niacmg": "niac_mg",
    "vitb6mg": "vit_b6_mg",
    "folaug": "fola_ug",
    "vitcmg": "vit_c_mg",
    "vitb12ug": "vit_b12_ug",
    "seleug": "sele_ug",
}

EXPECTED_EXCEL_COLUMNS = [
    "da_code",
    "food_description",
    "quantity",
    "measure",
    *NUMERIC_COLUMNS,
]
REQUIRED_COLUMNS = ["da_code", "food_description"]


@dataclass
class ImportStats:
    categories_created: int = 0
    categories_seen: int = 0
    subcategories_created: int = 0
    subcategories_seen: int = 0
    foods_inserted: int = 0
    foods_updated: int = 0
    foods_skipped: int = 0
    self_subcategory_foods: int = 0
    warnings: int = 0
    food_preview: list[dict[str, Any]] = field(default_factory=list)
    food_rows_processed: int = 0
    below_limit_values: int = 0
    trace_values: int = 0


def normalize_space(value: str) -> str:
    """Collapse repeated whitespace from Excel cells."""
    return re.sub(r"\s+", " ", value.strip())


def normalize_header(value: Any) -> str:
    if value is None:
        return ""
    text = normalize_space(str(value).replace("\n", " ").replace("\r", " "))
    return text.lower()


def simplify_header(value: Any) -> str:
    """Make messy Excel headers stable enough to map to DB columns."""
    normalized = normalize_header(value)
    return re.sub(r"[^a-z0-9]+", "", normalized)


def is_nan(value: Any) -> bool:
    return isinstance(value, float) and math.isnan(value)


def is_blank(value: Any) -> bool:
    if value is None or is_nan(value):
        return True
    if isinstance(value, str):
        return normalize_space(value) == ""
    return False


def clean_text(value: Any) -> str | None:
    if is_blank(value):
        return None
    return normalize_space(str(value))


def clean_bool(value: Any) -> bool:
    """Read optional TRUE/FALSE style flags from Excel."""
    if is_blank(value):
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0

    text = normalize_space(str(value)).lower()
    return text in {"true", "yes", "y", "1", "x"}


def parse_da_code(value: Any) -> int | None:
    """Return an integer DA code only for real food rows."""
    if is_blank(value):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return None

    text = normalize_space(str(value))
    if text == "":
        return None
    text = text.replace(",", "")
    if re.fullmatch(r"\d+", text):
        return int(text)
    if re.fullmatch(r"\d+\.0+", text):
        return int(float(text))
    return None


def clean_numeric(value: Any) -> float | None:
    """Normalize numeric nutrient cells while preserving unknown values as NULL."""
    cleaned_value, _note = clean_numeric_with_note(value)
    return cleaned_value


def parse_below_limit_note(text: str, raw_text: str) -> dict[str, Any] | None:
    if not text.startswith("<"):
        return None

    limit_text = text[1:].strip()
    if limit_text.startswith("."):
        limit_text = f"0{limit_text}"

    try:
        limit_value = float(limit_text)
    except ValueError:
        limit_value = None

    return {
        "raw": raw_text,
        "qualifier": "lt",
        "limit": limit_value,
    }


def clean_numeric_with_note(value: Any) -> tuple[float | None, dict[str, Any] | None]:
    """Return the numeric value plus optional source marker metadata."""
    if is_blank(value):
        return None, None
    if isinstance(value, bool):
        return None, None
    if isinstance(value, (int, float)):
        return float(value), None

    raw_text = normalize_space(str(value))
    text = raw_text.lower()
    if text in NULL_NUMERIC_TOKENS:
        return None, None
    if text in TRACE_NUMERIC_TOKENS:
        return BELOW_LIMIT_CALC_VALUE, {
            "raw": raw_text,
            "qualifier": "trace",
            "limit": None,
        }
    if text.startswith("<"):
        return BELOW_LIMIT_CALC_VALUE, parse_below_limit_note(text, raw_text)

    compact = text.replace(" ", "")
    if "," in compact and "." not in compact:
        compact = compact.replace(",", ".")

    try:
        return float(compact), None
    except ValueError:
        return None, None


def normalize_fraction_text(text: str) -> str:
    for src, target in UNICODE_FRACTIONS.items():
        text = text.replace(src, target)
    return text.replace("\u2044", "/")


def parse_fractional_number(text: str) -> float | None:
    normalized = normalize_fraction_text(normalize_space(text))
    normalized = normalized.replace(",", ".")
    normalized = re.sub(r"\s+", " ", normalized)
    if normalized == "":
        return None

    mixed_match = re.fullmatch(r"(-?\d+)\s+(\d+)\s*/\s*(\d+)", normalized)
    if mixed_match:
        whole = int(mixed_match.group(1))
        num = int(mixed_match.group(2))
        den = int(mixed_match.group(3))
        if den == 0:
            return None
        sign = -1 if whole < 0 else 1
        return whole + sign * (num / den)

    frac_match = re.fullmatch(r"(-?\d+)\s*/\s*(\d+)", normalized)
    if frac_match:
        num = int(frac_match.group(1))
        den = int(frac_match.group(2))
        if den == 0:
            return None
        return num / den

    try:
        return float(normalized)
    except ValueError:
        return None


def clean_quantity(value: Any) -> float | None:
    """Parse serving quantities, including fractional text values."""
    if is_blank(value):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = normalize_space(str(value)).lower()
    if text in NULL_NUMERIC_TOKENS:
        return None
    if text in TRACE_NUMERIC_TOKENS:
        return BELOW_LIMIT_CALC_VALUE
    if text.startswith("<"):
        return BELOW_LIMIT_CALC_VALUE

    parsed = parse_fractional_number(text)
    return parsed


def mostly_uppercase(text: str) -> bool:
    """Detect category headings, which are uppercase in the source workbook."""
    letters = [char for char in text if char.isalpha()]
    if len(letters) < 3:
        return False
    uppercase_count = sum(1 for char in letters if char.isupper())
    return (uppercase_count / len(letters)) >= 0.7


def heading_has_mostly_empty_nutrients(
    row: pd.Series, column_lookup: dict[str, Any], nutrient_columns_present: list[str]
) -> bool:
    """Protect against treating a real food row as a heading."""
    if not nutrient_columns_present:
        return True
    non_empty = 0
    for col in nutrient_columns_present:
        raw_value = row[column_lookup[col]]
        if not is_blank(raw_value):
            non_empty += 1
    threshold = max(1, int(len(nutrient_columns_present) * 0.2))
    return non_empty <= threshold


def warn(message: str, stats: ImportStats) -> None:
    stats.warnings += 1
    print(f"WARNING: {message}")


def build_column_lookup(
    columns: list[Any], stats: ImportStats, sheet_name: str, verbose: bool
) -> dict[str, Any]:
    lookup: dict[str, Any] = {}
    for original_column in columns:
        key = simplify_header(original_column)
        db_column = HEADER_ALIAS_TO_DB.get(key)
        if not db_column:
            continue
        if db_column in lookup:
            warn(
                f"[{sheet_name}] duplicate mapped header for '{db_column}': "
                f"keeping '{lookup[db_column]}', ignoring '{original_column}'",
                stats,
            )
            continue
        lookup[db_column] = original_column

    missing = [col for col in EXPECTED_EXCEL_COLUMNS if col not in lookup]
    for col in missing:
        warn(f"[{sheet_name}] missing column '{col}'", stats)

    required_missing = [col for col in REQUIRED_COLUMNS if col not in lookup]
    if required_missing:
        warn(
            f"[{sheet_name}] missing required columns: {', '.join(required_missing)}",
            stats,
        )

    if verbose:
        print(f"[{sheet_name}] mapped columns: {sorted(lookup.keys())}")
    return lookup


def row_is_totally_empty(row: pd.Series) -> bool:
    return all(is_blank(value) for value in row.tolist())


def upsert_category(
    cursor: pymysql.cursors.Cursor, category_name: str, stats: ImportStats
) -> int:
    """Create or reuse a Category and return its id."""
    sql = """
        INSERT INTO categories (name)
        VALUES (%s)
        ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)
    """
    cursor.execute(sql, (category_name,))
    if cursor.rowcount == 1:
        stats.categories_created += 1
    else:
        stats.categories_seen += 1
    category_id = cursor.lastrowid
    if category_id:
        return int(category_id)

    cursor.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
    result = cursor.fetchone()
    if not result:
        raise RuntimeError(f"Could not resolve category id for '{category_name}'")
    return int(result[0])


def upsert_subcategory(
    cursor: pymysql.cursors.Cursor,
    category_id: int,
    subcategory_name: str,
    stats: ImportStats,
) -> int:
    """Create or reuse a Food group inside one Category."""
    sql = """
        INSERT INTO subcategories (category_id, name)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)
    """
    cursor.execute(sql, (category_id, subcategory_name))
    if cursor.rowcount == 1:
        stats.subcategories_created += 1
    else:
        stats.subcategories_seen += 1
    subcategory_id = cursor.lastrowid
    if subcategory_id:
        return int(subcategory_id)

    cursor.execute(
        "SELECT id FROM subcategories WHERE category_id = %s AND name = %s",
        (category_id, subcategory_name),
    )
    result = cursor.fetchone()
    if not result:
        raise RuntimeError(
            f"Could not resolve subcategory id for category_id={category_id}, "
            f"name='{subcategory_name}'"
        )
    return int(result[0])


def upsert_food(
    cursor: pymysql.cursors.Cursor, row_data: dict[str, Any], stats: ImportStats
) -> None:
    """Insert a food or update the existing row with the same DA code."""
    insert_columns = ", ".join(FOOD_COLUMNS)
    placeholders = ", ".join(["%s"] * len(FOOD_COLUMNS))
    update_columns = [col for col in FOOD_COLUMNS if col != "da_code"]
    # COALESCE prevents blank Excel cells from deleting useful DB values.
    update_assignments = ", ".join(
        [
            (
                f"{col} = new.{col}"
                if col == "nutrient_value_notes"
                else f"{col} = COALESCE(new.{col}, foods.{col})"
            )
            for col in update_columns
        ]
        + ["updated_at = CURRENT_TIMESTAMP"]
    )

    sql = f"""
        INSERT INTO foods ({insert_columns})
        VALUES ({placeholders}) AS new
        ON DUPLICATE KEY UPDATE {update_assignments}
    """
    values = [row_data.get(col) for col in FOOD_COLUMNS]
    cursor.execute(sql, values)

    if cursor.rowcount == 1:
        stats.foods_inserted += 1
    else:
        stats.foods_updated += 1


def resolve_excel_path(excel_arg: str) -> Path:
    """Resolve Excel paths from the current folder first, then from this script."""
    path = Path(excel_arg)
    if path.is_absolute():
        return path
    cwd_path = (Path.cwd() / path).resolve()
    if cwd_path.exists():
        return cwd_path
    script_dir = Path(__file__).resolve().parent
    return (script_dir / path).resolve()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import/upsert TABEL ALIM Excel data into MySQL."
    )
    parser.add_argument(
        "--excel",
        default=r"..\data\FoodsFinal.xlsx",
        help="Path to Excel file (absolute path or relative to this script)",
    )
    parser.add_argument("--sheet", help="Single sheet to import (default: all sheets)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3307)
    parser.add_argument("--user", default="nutrition")
    parser.add_argument("--password", default="nutritionpass")
    parser.add_argument("--database", default="nutrition")
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="Parse and execute SQL, but rollback transaction at the end (default)",
    )
    parser.add_argument(
        "--commit",
        dest="dry_run",
        action="store_false",
        help="Commit changes to MySQL",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional max number of food rows to process",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def process_sheet(
    sheet_name: str,
    dataframe: pd.DataFrame,
    cursor: pymysql.cursors.Cursor,
    stats: ImportStats,
    args: argparse.Namespace,
) -> bool:
    """Process one Excel sheet while keeping the current category/food context."""
    column_lookup = build_column_lookup(
        columns=list(dataframe.columns), stats=stats, sheet_name=sheet_name, verbose=args.verbose
    )
    nutrient_columns_present = [
        col for col in NUMERIC_COLUMNS if col in column_lookup
    ]

    # Food rows inherit these ids from the most recent heading rows above them.
    current_category_id: int | None = None
    current_category_name: str | None = None
    current_subcategory_id: int | None = None
    current_subcategory_name: str | None = None

    for row_index, row in dataframe.iterrows():
        if args.limit is not None and stats.food_rows_processed >= args.limit:
            return True

        if row_is_totally_empty(row):
            continue

        da_raw = row[column_lookup["da_code"]] if "da_code" in column_lookup else None
        description = (
            clean_text(row[column_lookup["food_description"]])
            if "food_description" in column_lookup
            else None
        )
        da_code = parse_da_code(da_raw) if "da_code" in column_lookup else None

        if da_code is not None:
            stats.food_rows_processed += 1
            if not description:
                stats.foods_skipped += 1
                warn(
                    f"[{sheet_name}] row {row_index + 2}: food row with DA code "
                    f"{da_code} has no description; skipped",
                    stats,
                )
                continue

            # Some bold source rows are both a food and their own Food group.
            is_own_subcategory = (
                clean_bool(row[column_lookup["own_subcategory"]])
                if "own_subcategory" in column_lookup
                else False
            )

            if is_own_subcategory:
                if current_category_id is None:
                    warn(
                        f"[{sheet_name}] row {row_index + 2}: food '{description}' is marked "
                        "as own_subcategory but has no current category",
                        stats,
                    )
                else:
                    current_subcategory_id = upsert_subcategory(
                        cursor,
                        category_id=current_category_id,
                        subcategory_name=description,
                        stats=stats,
                    )
                    current_subcategory_name = description
                    stats.self_subcategory_foods += 1
                    if args.verbose:
                        print(
                            f"[{sheet_name}] food '{description}' becomes its own subcategory"
                        )

            if current_subcategory_id is None:
                warn(
                    f"[{sheet_name}] row {row_index + 2}: food '{description}' has no "
                    "current subcategory; inserting with NULL subcategory_id",
                    stats,
                )

            food_row: dict[str, Any] = {
                "da_code": da_code,
                "subcategory_id": current_subcategory_id,
                "food_description": description,
                "quantity": (
                    clean_quantity(row[column_lookup["quantity"]])
                    if "quantity" in column_lookup
                    else None
                ),
                "measure": (
                    clean_text(row[column_lookup["measure"]])
                    if "measure" in column_lookup
                    else None
                ),
            }
            nutrient_value_notes: dict[str, dict[str, Any]] = {}
            for numeric_col in NUMERIC_COLUMNS:
                if numeric_col in column_lookup:
                    cleaned_value, note = clean_numeric_with_note(
                        row[column_lookup[numeric_col]]
                    )
                    food_row[numeric_col] = cleaned_value
                    if note:
                        nutrient_value_notes[numeric_col] = note
                        if note["qualifier"] == "lt":
                            stats.below_limit_values += 1
                        elif note["qualifier"] == "trace":
                            stats.trace_values += 1
                else:
                    food_row[numeric_col] = None
            food_row["nutrient_value_notes"] = (
                json.dumps(nutrient_value_notes, sort_keys=True)
                if nutrient_value_notes
                else None
            )

            if args.verbose and len(stats.food_preview) < 5:
                stats.food_preview.append(dict(food_row))

            upsert_food(cursor, food_row, stats)
            continue

        # Rows without DA codes can still change the current hierarchy context.
        da_text = clean_text(da_raw)
        is_category_heading = bool(da_text and mostly_uppercase(da_text))
        is_subcategory_heading = bool(description)
        if not (is_category_heading or is_subcategory_heading):
            continue

        is_heading = heading_has_mostly_empty_nutrients(
            row=row,
            column_lookup=column_lookup,
            nutrient_columns_present=nutrient_columns_present,
        )
        if not is_heading:
            continue

        if is_category_heading:
            current_category_id = upsert_category(cursor, da_text, stats)
            current_category_name = da_text
            current_subcategory_id = None
            current_subcategory_name = None
            continue

        heading_text = description
        if current_category_id is None:
            warn(
                f"[{sheet_name}] row {row_index + 2}: subcategory '{heading_text}' has no "
                "current category; ignoring subcategory context",
                stats,
            )
            current_subcategory_id = None
            current_subcategory_name = None
            continue

        current_subcategory_id = upsert_subcategory(
            cursor=cursor,
            category_id=current_category_id,
            subcategory_name=heading_text,
            stats=stats,
        )
        current_subcategory_name = heading_text

        if args.verbose:
            print(
                f"[{sheet_name}] category='{current_category_name}' "
                f"subcategory='{current_subcategory_name}'"
            )

    return False


def main() -> int:
    """CLI entry point. Defaults to dry-run until --commit is provided."""
    args = parse_arguments()
    excel_path = resolve_excel_path(args.excel)
    if not excel_path.exists():
        print(f"ERROR: Excel file not found: {excel_path}")
        return 1

    stats = ImportStats()
    print(f"Excel file: {excel_path}")
    print("Mode: dry-run (rollback at end)" if args.dry_run else "Mode: commit")

    try:
        workbook = pd.ExcelFile(excel_path, engine="openpyxl")
    except Exception as exc:
        print(f"ERROR: Failed to open Excel file: {exc}")
        return 1

    if args.sheet:
        if args.sheet not in workbook.sheet_names:
            print(
                f"ERROR: Sheet '{args.sheet}' not found. Available sheets: "
                f"{', '.join(workbook.sheet_names)}"
            )
            return 1
        target_sheets = [args.sheet]
    else:
        target_sheets = workbook.sheet_names

    if args.verbose:
        print(f"Sheets to import: {target_sheets}")

    connection = pymysql.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        charset="utf8mb4",
        autocommit=False,
    )

    try:
        with connection.cursor() as cursor:
            stop_for_limit = False
            for sheet_name in target_sheets:
                if args.limit is not None and stats.food_rows_processed >= args.limit:
                    break

                dataframe = workbook.parse(sheet_name=sheet_name, dtype=object)
                if args.verbose:
                    print(f"[{sheet_name}] rows loaded: {len(dataframe)}")

                stop_for_limit = process_sheet(
                    sheet_name=sheet_name,
                    dataframe=dataframe,
                    cursor=cursor,
                    stats=stats,
                    args=args,
                )
                if stop_for_limit:
                    break

        if args.dry_run:
            connection.rollback()
            print("Dry-run complete: rolled back transaction.")
        else:
            connection.commit()
            print("Commit complete.")
    except Exception as exc:
        connection.rollback()
        print(f"ERROR: Import failed, transaction rolled back: {exc}")
        return 1
    finally:
        connection.close()

    print("")
    print("Summary:")
    print(f"  categories created: {stats.categories_created}")
    print(f"  categories seen:    {stats.categories_seen}")
    print(f"  subcategories created: {stats.subcategories_created}")
    print(f"  subcategories seen:    {stats.subcategories_seen}")
    print(f"  foods inserted: {stats.foods_inserted}")
    print(f"  foods updated:  {stats.foods_updated}")
    print(f"  foods skipped:  {stats.foods_skipped}")
    print(f"  own-subcategory foods: {stats.self_subcategory_foods}")
    print(f"  below-limit nutrient values: {stats.below_limit_values}")
    print(f"  trace nutrient values:       {stats.trace_values}")
    print(f"  warnings:       {stats.warnings}")

    if args.limit is not None:
        print(f"  food rows processed (limit): {stats.food_rows_processed}/{args.limit}")
    else:
        print(f"  food rows processed: {stats.food_rows_processed}")

    if args.verbose and stats.food_preview:
        print("")
        print("First parsed food rows:")
        for index, preview in enumerate(stats.food_preview, start=1):
            print(f"  [{index}] {pformat(preview)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
