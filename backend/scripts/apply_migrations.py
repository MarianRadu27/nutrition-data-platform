#!/usr/bin/env python3
"""Apply SQL migrations to the configured MySQL database."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from pymysql.constants import CLIENT


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MIGRATIONS_DIR = BACKEND_DIR / "migrations"


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
    return pymysql.connect(
        host=env_str("DB_HOST", "127.0.0.1"),
        port=env_int("DB_PORT", 3307),
        user=env_str("DB_USER", "nutrition"),
        password=env_str("DB_PASSWORD", "nutritionpass"),
        database=env_str("DB_NAME", "nutrition"),
        charset="utf8mb4",
        autocommit=False,
        client_flag=CLIENT.MULTI_STATEMENTS,
    )


def consume_remaining_results(cursor: pymysql.cursors.Cursor) -> None:
    while cursor.nextset():
        pass


def ensure_migration_table(cursor: pymysql.cursors.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (filename)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )


def get_applied_migrations(cursor: pymysql.cursors.Cursor) -> set[str]:
    cursor.execute("SELECT filename FROM schema_migrations")
    return {str(row[0]) for row in cursor.fetchall()}


def apply_migration(
    connection: pymysql.connections.Connection,
    cursor: pymysql.cursors.Cursor,
    migration_path: Path,
) -> None:
    sql = migration_path.read_text(encoding="utf-8")
    cursor.execute(sql)
    consume_remaining_results(cursor)
    cursor.execute(
        "INSERT INTO schema_migrations (filename) VALUES (%s)",
        (migration_path.name,),
    )
    connection.commit()


def main() -> int:
    load_dotenv(BACKEND_DIR / ".env")

    migration_paths = sorted(DEFAULT_MIGRATIONS_DIR.glob("*.sql"))
    if not migration_paths:
        print(f"No migrations found in {DEFAULT_MIGRATIONS_DIR}")
        return 1

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            ensure_migration_table(cursor)
            connection.commit()

            applied = get_applied_migrations(cursor)
            pending = [path for path in migration_paths if path.name not in applied]

            if not pending:
                print("Database is up to date.")
                return 0

            for migration_path in pending:
                print(f"Applying {migration_path.name}...")
                apply_migration(connection, cursor, migration_path)

            print(f"Applied {len(pending)} migration(s).")
            return 0
    except Exception as exc:
        connection.rollback()
        print(f"ERROR: migration failed: {exc}", file=sys.stderr)
        return 1
    finally:
        connection.close()


if __name__ == "__main__":
    sys.exit(main())
