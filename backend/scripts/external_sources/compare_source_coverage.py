#!/usr/bin/env python3
"""Compare canonical nutrient coverage across external sources.

This script only reads the database. It does not import, update, or delete
anything.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal
import os
from pathlib import Path
from typing import Any

import pymysql
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"

DEFAULT_SOURCE_CODES = ["NEVO", "ANSES_CIQUAL"]


@dataclass(frozen=True)
class CoverageRow:
    """One coverage result for one source and one canonical nutrient."""

    data_source_code: str
    canonical_code: str
    name_en: str
    foods_with_value: int
    total_foods: int
    coverage_percent: Decimal
    value_rows: int
    less_than_rows: int
    trace_rows: int


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
        cursorclass=pymysql.cursors.DictCursor,
    )


def parse_source_codes(values: list[str]) -> list[str]:
    """Normalize source codes while preserving the requested order."""
    source_codes: list[str] = []
    seen: set[str] = set()

    for value in values:
        for item in value.split(","):
            source_code = item.strip()
            if not source_code or source_code in seen:
                continue
            source_codes.append(source_code)
            seen.add(source_code)

    return source_codes


def fetch_existing_source_codes(cursor: Any, source_codes: list[str]) -> set[str]:
    placeholders = ", ".join(["%s"] * len(source_codes))
    cursor.execute(
        f"""
        SELECT code
        FROM data_sources
        WHERE code IN ({placeholders})
        """,
        source_codes,
    )
    return {row["code"] for row in cursor.fetchall()}


def fetch_coverage_rows(
    cursor: Any,
    source_codes: list[str],
    *,
    hide_empty: bool,
) -> list[CoverageRow]:
    """Fetch coverage results for the requested source codes."""
    placeholders = ", ".join(["%s"] * len(source_codes))
    empty_filter = ""
    if hide_empty:
        empty_filter = "WHERE COALESCE(cv.value_rows, 0) > 0"

    sql = f"""
        WITH source_totals AS (
          SELECT
            ds.id AS data_source_id,
            ds.code AS data_source_code,
            COUNT(sf.id) AS total_foods
          FROM data_sources ds
          LEFT JOIN source_foods sf ON sf.data_source_id = ds.id
          WHERE ds.code IN ({placeholders})
          GROUP BY ds.id, ds.code
        ),
        canonical_values AS (
          SELECT
            ds.id AS data_source_id,
            cn.id AS canonical_nutrient_id,
            COUNT(DISTINCT sf.id) AS foods_with_value,
            COUNT(v.id) AS value_rows,
            SUM(CASE WHEN v.value_qualifier = 'less_than' THEN 1 ELSE 0 END)
              AS less_than_rows,
            SUM(CASE WHEN v.value_qualifier = 'trace' THEN 1 ELSE 0 END)
              AS trace_rows
          FROM source_food_nutrient_values v
          JOIN source_foods sf ON sf.id = v.source_food_id
          JOIN data_sources ds ON ds.id = sf.data_source_id
          JOIN source_nutrients sn ON sn.id = v.source_nutrient_id
          JOIN canonical_nutrients cn ON cn.id = sn.canonical_nutrient_id
          WHERE ds.code IN ({placeholders})
          GROUP BY ds.id, cn.id
        )
        SELECT
          st.data_source_code,
          cn.canonical_code,
          cn.name_en,
          COALESCE(cv.foods_with_value, 0) AS foods_with_value,
          st.total_foods,
          CASE
            WHEN st.total_foods = 0 THEN 0
            ELSE ROUND(COALESCE(cv.foods_with_value, 0) / st.total_foods * 100, 2)
          END AS coverage_percent,
          COALESCE(cv.value_rows, 0) AS value_rows,
          COALESCE(cv.less_than_rows, 0) AS less_than_rows,
          COALESCE(cv.trace_rows, 0) AS trace_rows
        FROM source_totals st
        CROSS JOIN canonical_nutrients cn
        LEFT JOIN canonical_values cv
          ON cv.data_source_id = st.data_source_id
         AND cv.canonical_nutrient_id = cn.id
        {empty_filter}
        ORDER BY cn.canonical_code, st.data_source_code
    """
    cursor.execute(sql, [*source_codes, *source_codes])

    return [
        CoverageRow(
            data_source_code=row["data_source_code"],
            canonical_code=row["canonical_code"],
            name_en=row["name_en"],
            foods_with_value=int(row["foods_with_value"]),
            total_foods=int(row["total_foods"]),
            coverage_percent=Decimal(str(row["coverage_percent"])),
            value_rows=int(row["value_rows"]),
            less_than_rows=int(row["less_than_rows"]),
            trace_rows=int(row["trace_rows"]),
        )
        for row in cursor.fetchall()
    ]


def format_percent(value: Decimal) -> str:
    return f"{value:.2f}"


def print_table(rows: list[CoverageRow]) -> None:
    """Print a simple aligned terminal table."""
    headers = [
        "source",
        "canonical",
        "name",
        "foods",
        "total",
        "coverage_%",
        "values",
        "less_than",
        "trace",
    ]
    table_rows = [
        [
            row.data_source_code,
            row.canonical_code,
            row.name_en,
            str(row.foods_with_value),
            str(row.total_foods),
            format_percent(row.coverage_percent),
            str(row.value_rows),
            str(row.less_than_rows),
            str(row.trace_rows),
        ]
        for row in rows
    ]
    widths = [
        max(len(header), *(len(row[index]) for row in table_rows))
        for index, header in enumerate(headers)
    ]

    header_line = "  ".join(
        header.ljust(widths[index])
        for index, header in enumerate(headers)
    )
    separator_line = "  ".join("-" * width for width in widths)
    print(header_line)
    print(separator_line)

    for row in table_rows:
        print(
            "  ".join(
                value.ljust(widths[index])
                for index, value in enumerate(row)
            )
        )


def print_markdown(rows: list[CoverageRow]) -> None:
    """Print a markdown table that can be pasted into docs."""
    print(
        "| Source | Canonical nutrient | Name | Foods with value | Total foods | "
        "Coverage % | Value rows | Less-than rows | Trace rows |"
    )
    print(
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    for row in rows:
        print(
            f"| {row.data_source_code} "
            f"| {row.canonical_code} "
            f"| {row.name_en} "
            f"| {row.foods_with_value} "
            f"| {row.total_foods} "
            f"| {format_percent(row.coverage_percent)} "
            f"| {row.value_rows} "
            f"| {row.less_than_rows} "
            f"| {row.trace_rows} |"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare canonical nutrient coverage for external sources."
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=DEFAULT_SOURCE_CODES,
        help=(
            "Source codes to compare. Use spaces or commas. "
            "Default: NEVO ANSES_CIQUAL."
        ),
    )
    parser.add_argument(
        "--hide-empty",
        action="store_true",
        help="Hide source/canonical rows with no value rows.",
    )
    parser.add_argument(
        "--format",
        choices=["table", "markdown"],
        default="table",
        help="Output format. Default: table.",
    )
    args = parser.parse_args()

    source_codes = parse_source_codes(args.sources)
    if not source_codes:
        print("ERROR: provide at least one source code.")
        return 1

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            existing_source_codes = fetch_existing_source_codes(cursor, source_codes)
            missing_source_codes = [
                source_code
                for source_code in source_codes
                if source_code not in existing_source_codes
            ]
            if missing_source_codes:
                print("ERROR: missing data_sources rows: " + ", ".join(missing_source_codes))
                return 1

            rows = fetch_coverage_rows(
                cursor,
                source_codes,
                hide_empty=args.hide_empty,
            )
    finally:
        connection.close()

    print("Canonical nutrient coverage")
    print("=" * 28)
    print("Sources: " + ", ".join(source_codes))
    if not args.hide_empty:
        print("Rows with 0 values are shown so missing source mappings are visible.")
    print()

    if args.format == "markdown":
        print_markdown(rows)
    else:
        print_table(rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
