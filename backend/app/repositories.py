from __future__ import annotations

import json
from typing import Any

from app.schemas import AdminFoodCreateIn, Lang

CUSTOM_DA_CODE_START = 90_000_000


def _display_expr(lang: Lang, ro_col: str, en_col: str) -> str:
    """Choose Romanian text when requested, falling back to English if missing."""
    if lang == "ro":
        return f"COALESCE({ro_col}, {en_col})"
    return en_col


def _parse_nutrient_value_notes(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) and parsed else None
    return None


def _normalize_nutrient_value_notes(row: dict[str, Any]) -> dict[str, Any]:
    row["nutrient_value_notes"] = _parse_nutrient_value_notes(
        row.get("nutrient_value_notes")
    )
    return row


def _normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_normalize_nutrient_value_notes(row) for row in rows]


def list_categories(cursor: Any, lang: Lang) -> list[dict[str, Any]]:
    """Return top-level Category options for filters."""
    name_display_expr = _display_expr(lang, "name_ro", "name")
    sql = f"""
        SELECT
            id,
            name,
            name_ro,
            {name_display_expr} AS name_display
        FROM categories
        ORDER BY name_display ASC
    """
    cursor.execute(sql)
    return cursor.fetchall()


def list_subcategories(cursor: Any, category_id: int, lang: Lang) -> list[dict[str, Any]]:
    """Return Food groups for one Category.

    The DB name is subcategories, but the frontend labels this level as Food.
    """
    name_display_expr = _display_expr(lang, "name_ro", "name")
    sql = f"""
        SELECT
            id,
            category_id,
            name,
            name_ro,
            {name_display_expr} AS name_display
        FROM subcategories
        WHERE category_id = %s
        ORDER BY name_display ASC
    """
    cursor.execute(sql, (category_id,))
    return cursor.fetchall()


def list_foods(
    cursor: Any,
    *,
    search: str | None,
    category_id: int | None,
    subcategory_id: int | None,
    lang: Lang,
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], int]:
    """Return filtered food description rows plus the total count for pagination."""
    food_display_expr = _display_expr(lang, "f.food_description_ro", "f.food_description")
    category_display_expr = _display_expr(lang, "c.name_ro", "c.name")
    subcategory_display_expr = _display_expr(lang, "s.name_ro", "s.name")

    # Build WHERE pieces separately so optional filters can be combined safely.
    where_parts: list[str] = []
    params: list[Any] = []

    if search:
        where_parts.append(
            "(f.food_description LIKE %s OR f.food_description_ro LIKE %s)"
        )
        token = f"%{search.strip()}%"
        params.extend([token, token])

    if category_id is not None:
        where_parts.append("s.category_id = %s")
        params.append(category_id)

    if subcategory_id is not None:
        where_parts.append("f.subcategory_id = %s")
        params.append(subcategory_id)

    where_sql = ""
    if where_parts:
        where_sql = "WHERE " + " AND ".join(where_parts)

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM foods f
        LEFT JOIN subcategories s ON s.id = f.subcategory_id
        LEFT JOIN categories c ON c.id = s.category_id
        {where_sql}
    """
    cursor.execute(count_sql, params)
    total = int(cursor.fetchone()["total"])

    rows_sql = f"""
        SELECT
            f.id,
            f.da_code,
            f.subcategory_id,
            s.category_id,
            f.food_description,
            f.food_description_ro,
            {food_display_expr} AS name_display,
            f.quantity,
            f.measure,
            f.wt_g,
            f.ener_kcal,
            f.prot_g,
            f.carbo_g,
            f.fat_g,
            f.fiber_g,
            f.h2o_g,
            f.sat_g,
            f.mono_g,
            f.poly_g,
            f.trans_g,
            f.chol_mg,
            f.calc_mg,
            f.iron_mg,
            f.magn_mg,
            f.pota_mg,
            f.sodi_mg,
            f.zinc_mg,
            f.vit_a_ug,
            f.vit_e_mg,
            f.thia_mg,
            f.ribo_mg,
            f.niac_mg,
            f.vit_b6_mg,
            f.fola_ug,
            f.vit_c_mg,
            f.vit_b12_ug,
            f.sele_ug,
            f.nutrient_value_notes,
            {category_display_expr} AS category_name_display,
            {subcategory_display_expr} AS subcategory_name_display
        FROM foods f
        LEFT JOIN subcategories s ON s.id = f.subcategory_id
        LEFT JOIN categories c ON c.id = s.category_id
        {where_sql}
        ORDER BY f.food_description ASC
        LIMIT %s OFFSET %s
    """
    page_params = [*params, limit, offset]
    cursor.execute(rows_sql, page_params)
    rows = cursor.fetchall()
    return _normalize_rows(rows), total


def get_foods_for_calc(
    cursor: Any, food_ids: list[int], lang: Lang
) -> dict[int, dict[str, Any]]:
    """Fetch only the nutrient columns needed by the meal calculator."""
    if not food_ids:
        return {}

    food_display_expr = _display_expr(lang, "f.food_description_ro", "f.food_description")
    placeholders = ", ".join(["%s"] * len(food_ids))
    sql = f"""
        SELECT
            f.id,
            f.food_description,
            f.food_description_ro,
            {food_display_expr} AS name_display,
            f.wt_g,
            f.ener_kcal,
            f.prot_g,
            f.carbo_g,
            f.fat_g,
            f.fiber_g,
            f.nutrient_value_notes
        FROM foods f
        WHERE f.id IN ({placeholders})
    """
    cursor.execute(sql, food_ids)
    rows = _normalize_rows(cursor.fetchall())
    return {int(row["id"]): row for row in rows}


def get_food_detail(cursor: Any, food_id: int, lang: Lang) -> dict[str, Any] | None:
    """Return one food with all nutrient columns."""
    food_name_display = (
        "COALESCE(f.food_description_ro, f.food_description)"
        if lang == "ro"
        else "f.food_description"
    )
    category_name_display = (
        "COALESCE(c.name_ro, c.name)"
        if lang == "ro"
        else "c.name"
    )
    subcategory_name_display = (
        "COALESCE(s.name_ro, s.name)"
        if lang == "ro"
        else "s.name"
    )

    sql = f"""
        SELECT
            f.id,
            f.da_code,
            f.subcategory_id,
            s.category_id,
            f.food_description,
            f.food_description_ro,
            {food_name_display} AS name_display,
            f.quantity,
            f.measure,
            f.wt_g,
            f.h2o_g,
            f.ener_kcal,
            f.prot_g,
            f.carbo_g,
            f.fat_g,
            f.fiber_g,
            f.sat_g,
            f.mono_g,
            f.poly_g,
            f.trans_g,
            f.chol_mg,
            f.calc_mg,
            f.iron_mg,
            f.magn_mg,
            f.pota_mg,
            f.sodi_mg,
            f.zinc_mg,
            f.vit_a_ug,
            f.vit_e_mg,
            f.thia_mg,
            f.ribo_mg,
            f.niac_mg,
            f.vit_b6_mg,
            f.fola_ug,
            f.vit_c_mg,
            f.vit_b12_ug,
            f.sele_ug,
            f.nutrient_value_notes,
            {category_name_display} AS category_name_display,
            {subcategory_name_display} AS subcategory_name_display
        FROM foods f
        LEFT JOIN subcategories s ON s.id = f.subcategory_id
        LEFT JOIN categories c ON c.id = s.category_id
        WHERE f.id = %s
    """

    cursor.execute(sql, (food_id,))
    row = cursor.fetchone()
    return _normalize_nutrient_value_notes(row) if row else None


def get_category_by_id(cursor: Any, category_id: int) -> dict[str, Any] | None:
    """Look up a category before linking a manually-added food."""
    cursor.execute(
        """
        SELECT id, name, name_ro
        FROM categories
        WHERE id = %s
        """,
        (category_id,),
    )
    return cursor.fetchone()


def get_subcategory_by_id(cursor: Any, subcategory_id: int) -> dict[str, Any] | None:
    """Look up a Food group before linking a manually-added food."""
    cursor.execute(
        """
        SELECT id, category_id, name, name_ro
        FROM subcategories
        WHERE id = %s
        """,
        (subcategory_id,),
    )
    return cursor.fetchone()


def upsert_category_by_name(
    cursor: Any, category_name: str, category_name_ro: str | None
) -> int:
    """Create or reuse a category by name and return its id."""
    cursor.execute(
        """
        INSERT INTO categories (name, name_ro)
        VALUES (%s, %s) AS new
        ON DUPLICATE KEY UPDATE
            id = LAST_INSERT_ID(id),
            name_ro = COALESCE(categories.name_ro, new.name_ro)
        """,
        (category_name, category_name_ro),
    )
    return int(cursor.lastrowid)


def upsert_subcategory_by_name(
    cursor: Any,
    category_id: int,
    subcategory_name: str,
    subcategory_name_ro: str | None,
) -> int:
    """Create or reuse a Food group within a category and return its id."""
    cursor.execute(
        """
        INSERT INTO subcategories (category_id, name, name_ro)
        VALUES (%s, %s, %s) AS new
        ON DUPLICATE KEY UPDATE
            id = LAST_INSERT_ID(id),
            name_ro = COALESCE(subcategories.name_ro, new.name_ro)
        """,
        (category_id, subcategory_name, subcategory_name_ro),
    )
    return int(cursor.lastrowid)


def get_next_custom_da_code(cursor: Any) -> int:
    """Generate DA codes for manually-added foods in a separate high range."""
    cursor.execute(
        """
        SELECT MAX(da_code) AS max_da_code
        FROM foods
        WHERE da_code >= %s
        """,
        (CUSTOM_DA_CODE_START,),
    )
    row = cursor.fetchone()
    max_code = row["max_da_code"] if row else None
    if max_code is None:
        return CUSTOM_DA_CODE_START
    return int(max_code) + 1


def insert_custom_food(
    cursor: Any,
    *,
    da_code: int,
    subcategory_id: int,
    payload: AdminFoodCreateIn,
) -> int:
    """Insert one manually-added food with the base nutrient fields."""
    cursor.execute(
        """
        INSERT INTO foods (
            da_code,
            subcategory_id,
            food_description,
            food_description_ro,
            quantity,
            measure,
            wt_g,
            ener_kcal,
            prot_g,
            carbo_g,
            fat_g,
            fiber_g
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            da_code,
            subcategory_id,
            payload.food_description.strip(),
            payload.food_description_ro.strip() if payload.food_description_ro else None,
            payload.quantity,
            payload.measure.strip() if payload.measure else None,
            payload.wt_g,
            payload.ener_kcal,
            payload.prot_g,
            payload.carbo_g,
            payload.fat_g,
            payload.fiber_g,
        ),
    )
    return int(cursor.lastrowid)


def get_food_by_id(cursor: Any, food_id: int, lang: Lang) -> dict[str, Any] | None:
    """Return the created food in the same shape used by the frontend."""
    food_display_expr = _display_expr(lang, "f.food_description_ro", "f.food_description")
    category_display_expr = _display_expr(lang, "c.name_ro", "c.name")
    subcategory_display_expr = _display_expr(lang, "s.name_ro", "s.name")
    sql = f"""
        SELECT
            f.id,
            f.da_code,
            f.subcategory_id,
            s.category_id,
            f.food_description,
            f.food_description_ro,
            {food_display_expr} AS name_display,
            f.quantity,
            f.measure,
            f.wt_g,
            f.ener_kcal,
            f.prot_g,
            f.carbo_g,
            f.fat_g,
            f.fiber_g,
            f.nutrient_value_notes,
            {category_display_expr} AS category_name_display,
            {subcategory_display_expr} AS subcategory_name_display
        FROM foods f
        LEFT JOIN subcategories s ON s.id = f.subcategory_id
        LEFT JOIN categories c ON c.id = s.category_id
        WHERE f.id = %s
    """
    cursor.execute(sql, (food_id,))
    row = cursor.fetchone()
    return _normalize_nutrient_value_notes(row) if row else None
