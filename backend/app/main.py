from __future__ import annotations

import logging
import secrets
from typing import Any, Iterator

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pymysql.connections import Connection

from app import db, repositories, schemas

BASE_NUTRIENTS = [
    # Internal DB column -> public API field used by the calculator.
    ("ener_kcal", "kcal"),
    ("prot_g", "protein_g"),
    ("carbo_g", "carbs_g"),
    ("fat_g", "fat_g"),
    ("fiber_g", "fiber_g"),
]
logger = logging.getLogger(__name__)


def _as_float(value: Any) -> float:
    """Convert nullable DB values to numbers for calculation."""
    if value is None:
        return 0.0
    return float(value)


def _rounded_nutrients(payload: dict[str, float]) -> dict[str, float]:
    """Keep API responses readable without losing too much precision."""
    return {key: round(value, 4) for key, value in payload.items()}


def get_db_connection() -> Iterator[Connection]:
    """FastAPI dependency that opens and closes one DB connection per request."""
    connection = db.get_connection()
    try:
        yield connection
    finally:
        connection.close()


def require_admin_token(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    """Protect local admin endpoints with a simple shared token."""
    expected = db.get_admin_token()
    if expected is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin token is not configured",
        )
    if not x_admin_token or not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token",
        )


app = FastAPI(title="Nutrition Data Platform API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=db.get_frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/categories", response_model=list[schemas.CategoryOut])
def get_categories(
    lang: schemas.Lang = Query(default="en"),
    connection: Connection = Depends(get_db_connection),
) -> list[dict[str, Any]]:
    """List all Category values in the requested display language."""
    with connection.cursor() as cursor:
        return repositories.list_categories(cursor, lang)


@app.get(
    "/api/categories/{category_id}/subcategories",
    response_model=list[schemas.SubcategoryOut],
)
def get_subcategories(
    category_id: int,
    lang: schemas.Lang = Query(default="en"),
    connection: Connection = Depends(get_db_connection),
) -> list[dict[str, Any]]:
    """List Food groups inside one Category."""
    with connection.cursor() as cursor:
        return repositories.list_subcategories(cursor, category_id, lang)


@app.get("/api/foods", response_model=schemas.FoodsListResponse)
def get_foods(
    search: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    subcategory_id: int | None = Query(default=None),
    lang: schemas.Lang = Query(default="en"),
    limit: int = Query(default=5000, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    connection: Connection = Depends(get_db_connection),
) -> schemas.FoodsListResponse:
    """Return Food Description rows filtered by search/category/food group."""
    with connection.cursor() as cursor:
        rows, total = repositories.list_foods(
            cursor,
            search=search,
            category_id=category_id,
            subcategory_id=subcategory_id,
            lang=lang,
            limit=limit,
            offset=offset,
        )
    return schemas.FoodsListResponse(items=rows, limit=limit, offset=offset, count=total)


@app.get("/api/foods/{food_id}", response_model=schemas.FoodDetailOut)
def get_food_detail(
    food_id: int,
    lang: schemas.Lang = Query(default="en"),
    connection: Connection = Depends(get_db_connection),
) -> schemas.FoodDetailOut:
    """Return one food with all stored nutrient values."""
    with connection.cursor() as cursor:
        food = repositories.get_food_detail(cursor, food_id, lang)

    if food is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food id={food_id} not found",
        )

    return schemas.FoodDetailOut(**food)


@app.post("/api/calc/meal", response_model=schemas.MealCalcResponse)
def calculate_meal(
    payload: schemas.MealCalcRequest,
    lang: schemas.Lang = Query(default="en"),
    connection: Connection = Depends(get_db_connection),
) -> schemas.MealCalcResponse:
    # We intentionally scale by grams / wt_g because dataset values are per serving.
    # If wt_g is missing, grams-based math is undefined for that item.
    food_ids = sorted({item.food_id for item in payload.items})
    with connection.cursor() as cursor:
        foods_by_id = repositories.get_foods_for_calc(cursor, food_ids, lang)

    totals = {
        "kcal": 0.0,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 0.0,
        "fiber_g": 0.0,
    }
    items_out: list[schemas.MealCalcItemOut] = []
    total_incomplete = False

    for item in payload.items:
        db_food = foods_by_id.get(item.food_id)
        if db_food is None:
            total_incomplete = True
            items_out.append(
                schemas.MealCalcItemOut(
                    food_id=item.food_id,
                    name=f"food_id={item.food_id}",
                    grams=item.grams,
                    factor=None,
                    nutrients=schemas.NutrientsOut(
                        kcal=0.0,
                        protein_g=0.0,
                        carbs_g=0.0,
                        fat_g=0.0,
                        fiber_g=0.0,
                    ),
                    incomplete_data=True,
                    error="food not found",
                )
            )
            continue

        wt_g_value = db_food.get("wt_g")
        if wt_g_value is None or float(wt_g_value) <= 0:
            total_incomplete = True
            items_out.append(
                schemas.MealCalcItemOut(
                    food_id=item.food_id,
                    name=db_food["name_display"],
                    grams=item.grams,
                    factor=None,
                    nutrients=schemas.NutrientsOut(
                        kcal=0.0,
                        protein_g=0.0,
                        carbs_g=0.0,
                        fat_g=0.0,
                        fiber_g=0.0,
                    ),
                    incomplete_data=True,
                    error="cannot calculate by grams: wt_g is null or <= 0",
                )
            )
            continue

        factor = float(item.grams) / float(wt_g_value)
        item_incomplete = False
        nutrients = {
            "kcal": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0,
            "fiber_g": 0.0,
        }

        for db_col, out_col in BASE_NUTRIENTS:
            raw = db_food.get(db_col)
            if raw is None:
                # Business rule: NULL means unknown. For math we use 0 but mark incomplete.
                item_incomplete = True
                value = 0.0
            else:
                value = _as_float(raw)
            scaled = value * factor
            nutrients[out_col] = scaled
            totals[out_col] += scaled

        if item_incomplete:
            total_incomplete = True

        items_out.append(
            schemas.MealCalcItemOut(
                food_id=item.food_id,
                name=db_food["name_display"],
                grams=item.grams,
                factor=round(factor, 6),
                nutrients=schemas.NutrientsOut(**_rounded_nutrients(nutrients)),
                incomplete_data=item_incomplete,
                error=None,
            )
        )

    return schemas.MealCalcResponse(
        totals=schemas.NutrientsOut(**_rounded_nutrients(totals)),
        incomplete_data=total_incomplete,
        items=items_out,
    )


@app.post(
    "/api/admin/foods",
    response_model=schemas.AdminFoodResponse,
    dependencies=[Depends(require_admin_token)],
)
def create_food_admin(
    payload: schemas.AdminFoodCreateIn,
    connection: Connection = Depends(get_db_connection),
) -> schemas.AdminFoodResponse:
    """Create one custom food and link it to an existing or new hierarchy path."""
    try:
        with connection.cursor() as cursor:
            category_id: int | None = None

            if payload.category_id is not None:
                category_row = repositories.get_category_by_id(cursor, payload.category_id)
                if category_row is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Category id={payload.category_id} not found",
                    )
                category_id = int(category_row["id"])
            else:
                category_id = repositories.upsert_category_by_name(
                    cursor,
                    category_name=payload.category_name.strip(),
                    category_name_ro=payload.category_name_ro.strip()
                    if payload.category_name_ro
                    else None,
                )

            subcategory_id: int | None = None
            if payload.subcategory_id is not None:
                subcategory_row = repositories.get_subcategory_by_id(
                    cursor, payload.subcategory_id
                )
                if subcategory_row is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Subcategory id={payload.subcategory_id} not found",
                    )
                subcategory_id = int(subcategory_row["id"])
                if category_id is not None and int(subcategory_row["category_id"]) != category_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="subcategory_id does not belong to provided category",
                    )
            else:
                if category_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Could not resolve category for subcategory upsert",
                    )
                subcategory_id = repositories.upsert_subcategory_by_name(
                    cursor,
                    category_id=category_id,
                    subcategory_name=payload.subcategory_name.strip(),
                    subcategory_name_ro=payload.subcategory_name_ro.strip()
                    if payload.subcategory_name_ro
                    else None,
                )

            da_code = repositories.get_next_custom_da_code(cursor)
            food_id = repositories.insert_custom_food(
                cursor, da_code=da_code, subcategory_id=subcategory_id, payload=payload
            )
            created = repositories.get_food_by_id(cursor, food_id, "en")
            if created is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch created food",
                )

        connection.commit()
        return schemas.AdminFoodResponse(da_code=da_code, food=schemas.FoodOut(**created))
    except HTTPException:
        connection.rollback()
        raise
    except Exception as exc:
        connection.rollback()
        logger.exception("Failed to create food")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create food",
        ) from exc
