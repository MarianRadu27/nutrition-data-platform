#!/usr/bin/env python3
"""Run a small end-to-end smoke test against a temporary MySQL database."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pymysql
from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
SAMPLE_EXCEL = BACKEND_DIR / "data" / "FoodsFinal_sample.xlsx"
TEMP_DB_PREFIX = "nutrition_smoke_test"
CALC_NOTE_FIELDS = {
    "ener_kcal": "kcal",
    "prot_g": "protein_g",
    "carbo_g": "carbs_g",
    "fat_g": "fat_g",
    "fiber_g": "fiber_g",
}


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


def safe_identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", value):
        raise ValueError(f"Unsafe MySQL identifier: {value}")
    return value


def quote_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def print_ok(message: str) -> None:
    print(f"OK {message}")


def run_command(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    verbose: bool,
) -> None:
    completed = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if verbose and completed.stdout:
        print(completed.stdout.rstrip())
    if completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout.rstrip())
        if completed.stderr:
            print(completed.stderr.rstrip(), file=sys.stderr)
        raise RuntimeError(f"Command failed: {' '.join(args)}")


def root_connection() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=env_str("DB_HOST", "127.0.0.1"),
        port=env_int("DB_PORT", 3307),
        user=env_str("DB_ROOT_USER", "root"),
        password=env_str("DB_ROOT_PASSWORD", "rootpass"),
        charset="utf8mb4",
        autocommit=True,
    )


def app_connection(database: str) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=env_str("DB_HOST", "127.0.0.1"),
        port=env_int("DB_PORT", 3307),
        user=env_str("DB_USER", "nutrition"),
        password=env_str("DB_PASSWORD", "nutritionpass"),
        database=database,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )


def create_temp_database(database: str) -> None:
    database = safe_identifier(database)
    app_user = env_str("DB_USER", "nutrition")
    app_user_sql = quote_string(app_user)
    with root_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS `{database}`")
            cursor.execute(
                f"CREATE DATABASE `{database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
            )
            cursor.execute(
                f"GRANT ALL PRIVILEGES ON `{database}`.* TO {app_user_sql}@'%'"
            )
            cursor.execute("FLUSH PRIVILEGES")


def drop_temp_database(database: str) -> None:
    database = safe_identifier(database)
    with root_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS `{database}`")


def fetch_one(connection: pymysql.connections.Connection, sql: str) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(sql)
        row = cursor.fetchone()
    if row is None:
        raise AssertionError(f"No row returned for SQL: {sql}")
    return row


def assert_database_shape(database: str) -> int:
    with app_connection(database) as connection:
        counts = {
            "categories": fetch_one(
                connection, "SELECT COUNT(*) AS count FROM categories"
            )["count"],
            "subcategories": fetch_one(
                connection, "SELECT COUNT(*) AS count FROM subcategories"
            )["count"],
            "foods": fetch_one(connection, "SELECT COUNT(*) AS count FROM foods")[
                "count"
            ],
            "foods_with_notes": fetch_one(
                connection,
                """
                SELECT COUNT(*) AS count
                FROM foods
                WHERE nutrient_value_notes IS NOT NULL
                """,
            )["count"],
        }
        if counts != {
            "categories": 3,
            "subcategories": 12,
            "foods": 40,
            "foods_with_notes": 25,
        }:
            raise AssertionError(f"Unexpected sample import counts: {counts}")

        row = fetch_one(
            connection,
            """
            SELECT id
            FROM foods
            WHERE JSON_EXTRACT(nutrient_value_notes, '$.fat_g') IS NOT NULL
               OR JSON_EXTRACT(nutrient_value_notes, '$.fiber_g') IS NOT NULL
               OR JSON_EXTRACT(nutrient_value_notes, '$.prot_g') IS NOT NULL
               OR JSON_EXTRACT(nutrient_value_notes, '$.carbo_g') IS NOT NULL
               OR JSON_EXTRACT(nutrient_value_notes, '$.ener_kcal') IS NOT NULL
            LIMIT 1
            """,
        )
        return int(row["id"])


def assert_api_behaviour(database: str, calc_food_id: int) -> None:
    os.environ["DB_NAME"] = database
    os.environ.setdefault("ADMIN_TOKEN", "smoke-test-admin-token")
    sys.path.insert(0, str(BACKEND_DIR))

    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    categories = client.get("/api/categories")
    if categories.status_code != 200 or len(categories.json()) != 3:
        raise AssertionError(f"Unexpected /api/categories response: {categories.text}")

    foods = client.get("/api/foods?limit=5")
    foods_payload = foods.json()
    if foods.status_code != 200 or foods_payload["count"] != 40:
        raise AssertionError(f"Unexpected /api/foods response: {foods.text}")

    detail = client.get(f"/api/foods/{calc_food_id}")
    detail_payload = detail.json()
    if detail.status_code != 200 or not detail_payload.get("nutrient_value_notes"):
        raise AssertionError(f"Expected nutrient notes in food detail: {detail.text}")

    calc = client.post(
        "/api/calc/meal",
        json={"items": [{"food_id": calc_food_id, "grams": 100}]},
    )
    if calc.status_code != 200:
        raise AssertionError(f"Unexpected /api/calc/meal response: {calc.text}")
    calc_item = calc.json()["items"][0]
    calc_notes = calc_item.get("nutrient_value_notes") or {}
    if not calc_notes:
        raise AssertionError("Expected calculator response to include source notes")

    for db_field, calc_field in CALC_NOTE_FIELDS.items():
        if db_field in detail_payload["nutrient_value_notes"]:
            if calc_field not in calc_notes:
                raise AssertionError(f"Missing calculator note for {calc_field}")
            if calc_item["nutrients"][calc_field] != 0.0:
                raise AssertionError(f"Expected {calc_field} to calculate as 0")
            break

    invalid_admin = client.post(
        "/api/admin/foods",
        headers={"X-Admin-Token": os.environ["ADMIN_TOKEN"]},
        json={
            "category_name": "Smoke Category",
            "subcategory_name": "Smoke Food",
            "food_description": "Smoke Negative Fat Test",
            "wt_g": 100,
            "ener_kcal": 10,
            "prot_g": 1,
            "carbo_g": 1,
            "fat_g": -1,
            "fiber_g": 1,
        },
    )
    if invalid_admin.status_code != 422:
        raise AssertionError(
            f"Expected admin negative value validation to return 422, "
            f"got {invalid_admin.status_code}: {invalid_admin.text}"
        )


def assert_no_admin_test_row(database: str) -> None:
    with app_connection(database) as connection:
        row = fetch_one(
            connection,
            """
            SELECT COUNT(*) AS count
            FROM foods
            WHERE food_description = 'Smoke Negative Fat Test'
            """,
        )
        if int(row["count"]) != 0:
            raise AssertionError("Invalid admin payload created a food row")


def run_frontend_build(verbose: bool) -> None:
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if npm is None:
        raise RuntimeError("npm was not found on PATH")
    run_command([npm, "run", "build"], cwd=FRONTEND_DIR, verbose=verbose)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a local smoke test using a temporary MySQL database."
    )
    parser.add_argument(
        "--database",
        default=f"{TEMP_DB_PREFIX}_{int(time.time())}",
        help="Temporary database name to create and drop.",
    )
    parser.add_argument(
        "--keep-db",
        action="store_true",
        help="Keep the temporary database after the test for debugging.",
    )
    parser.add_argument(
        "--with-frontend-build",
        action="store_true",
        help="Also run npm run build in the frontend.",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(BACKEND_DIR / ".env")
    database = safe_identifier(args.database)

    if not SAMPLE_EXCEL.exists():
        print(f"ERROR missing sample Excel file: {SAMPLE_EXCEL}", file=sys.stderr)
        return 1

    child_env = dict(os.environ)
    child_env["DB_NAME"] = database

    try:
        create_temp_database(database)
        print_ok(f"created temporary database {database}")

        run_command(
            [sys.executable, str(BACKEND_DIR / "scripts" / "apply_migrations.py")],
            cwd=PROJECT_DIR,
            env=child_env,
            verbose=args.verbose,
        )
        print_ok("migrations")

        run_command(
            [
                sys.executable,
                str(BACKEND_DIR / "scripts" / "import_data_db.py"),
                "--database",
                database,
                "--excel",
                str(SAMPLE_EXCEL),
                "--commit",
            ],
            cwd=PROJECT_DIR,
            verbose=args.verbose,
        )
        print_ok("sample import")

        calc_food_id = assert_database_shape(database)
        print_ok("database counts and nutrient notes")

        assert_api_behaviour(database, calc_food_id)
        assert_no_admin_test_row(database)
        print_ok("API endpoints and admin validation")

        if args.with_frontend_build:
            run_frontend_build(args.verbose)
            print_ok("frontend build")

        print("Smoke test passed.")
        return 0
    except Exception as exc:
        print(f"ERROR smoke test failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if args.keep_db:
            print(f"Kept temporary database: {database}")
        else:
            try:
                drop_temp_database(database)
                print_ok(f"dropped temporary database {database}")
            except Exception as exc:
                print(
                    f"WARNING failed to drop temporary database {database}: {exc}",
                    file=sys.stderr,
                )


if __name__ == "__main__":
    sys.exit(main())
