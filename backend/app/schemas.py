from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

Lang = Literal["en", "ro"]


class NutrientValueNote(BaseModel):
    """Source marker for nutrient values stored numerically for calculations."""

    raw: str
    qualifier: Literal["lt", "trace"]
    limit: float | None = None


class CategoryOut(BaseModel):
    """Category returned to the frontend.

    name_display is already selected in the requested language by the repository.
    """

    id: int
    name: str
    name_ro: str | None = None
    name_display: str


class SubcategoryOut(BaseModel):
    """Food group returned to the frontend.

    In the UI this is called Food, while the database table is still subcategories.
    """

    id: int
    category_id: int
    name: str
    name_ro: str | None = None
    name_display: str


class FoodOut(BaseModel):
    """Food description row with the nutrients needed by the foods table."""

    id: int
    da_code: int
    subcategory_id: int | None = None
    category_id: int | None = None
    food_description: str
    food_description_ro: str | None = None
    name_display: str
    quantity: float | None = None
    measure: str | None = None
    wt_g: float | None = None
    ener_kcal: float | None = None
    prot_g: float | None = None
    carbo_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    h2o_g: float | None = None
    sat_g: float | None = None
    mono_g: float | None = None
    poly_g: float | None = None
    trans_g: float | None = None
    chol_mg: float | None = None
    calc_mg: float | None = None
    iron_mg: float | None = None
    magn_mg: float | None = None
    pota_mg: float | None = None
    sodi_mg: float | None = None
    zinc_mg: float | None = None
    vit_a_ug: float | None = None
    vit_e_mg: float | None = None
    thia_mg: float | None = None
    ribo_mg: float | None = None
    niac_mg: float | None = None
    vit_b6_mg: float | None = None
    fola_ug: float | None = None
    vit_c_mg: float | None = None
    vit_b12_ug: float | None = None
    sele_ug: float | None = None
    nutrient_value_notes: dict[str, NutrientValueNote] | None = None
    category_name_display: str | None = None
    subcategory_name_display: str | None = None


class FoodDetailOut(BaseModel):
    """Detailed food payload used when the frontend needs every nutrient column."""

    id: int
    da_code: int
    subcategory_id: int | None = None
    category_id: int | None = None
    food_description: str
    food_description_ro: str | None = None
    name_display: str
    quantity: float | None = None
    measure: str | None = None
    wt_g: float | None = None
    h2o_g: float | None = None
    ener_kcal: float | None = None
    prot_g: float | None = None
    carbo_g: float | None = None
    fiber_g: float | None = None
    fat_g: float | None = None
    sat_g: float | None = None
    mono_g: float | None = None
    poly_g: float | None = None
    trans_g: float | None = None
    chol_mg: float | None = None
    calc_mg: float | None = None
    iron_mg: float | None = None
    magn_mg: float | None = None
    pota_mg: float | None = None
    sodi_mg: float | None = None
    zinc_mg: float | None = None
    vit_a_ug: float | None = None
    vit_e_mg: float | None = None
    thia_mg: float | None = None
    ribo_mg: float | None = None
    niac_mg: float | None = None
    vit_b6_mg: float | None = None
    fola_ug: float | None = None
    vit_c_mg: float | None = None
    vit_b12_ug: float | None = None
    sele_ug: float | None = None
    nutrient_value_notes: dict[str, NutrientValueNote] | None = None
    category_name_display: str | None = None
    subcategory_name_display: str | None = None


class FoodsListResponse(BaseModel):
    """Paginated response for /api/foods."""

    items: list[FoodOut]
    limit: int
    offset: int
    count: int


class MealCalcItemIn(BaseModel):
    """One user-selected food and the grams to calculate."""

    food_id: int = Field(gt=0)
    grams: float = Field(gt=0)


class MealCalcRequest(BaseModel):
    """Meal calculation request; it must contain at least one item."""

    items: list[MealCalcItemIn]

    @model_validator(mode="after")
    def validate_items(self) -> "MealCalcRequest":
        if not self.items:
            raise ValueError("items must contain at least one entry")
        return self


class NutrientsOut(BaseModel):
    """Small nutrient summary used by the meal calculator."""

    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float


class MealCalcItemOut(BaseModel):
    """Calculated nutrients for one selected meal item."""

    food_id: int
    name: str
    grams: float
    factor: float | None = None
    nutrients: NutrientsOut
    nutrient_value_notes: dict[str, NutrientValueNote] | None = None
    incomplete_data: bool
    error: str | None = None


class MealCalcResponse(BaseModel):
    """Meal calculation response including totals and per-item details."""

    totals: NutrientsOut
    incomplete_data: bool
    items: list[MealCalcItemOut]


class AdminFoodCreateIn(BaseModel):
    """Payload for manually adding one custom food in local admin tools."""

    category_id: int | None = None
    category_name: str | None = None
    category_name_ro: str | None = None

    subcategory_id: int | None = None
    subcategory_name: str | None = None
    subcategory_name_ro: str | None = None

    food_description: str = Field(min_length=1, max_length=255)
    food_description_ro: str | None = Field(default=None, max_length=255)
    quantity: float | None = None
    measure: str | None = Field(default=None, max_length=255)
    wt_g: float = Field(gt=0)
    ener_kcal: float
    prot_g: float
    carbo_g: float
    fat_g: float
    fiber_g: float

    @model_validator(mode="after")
    def validate_refs(self) -> "AdminFoodCreateIn":
        """Require either an existing id or a new name for both hierarchy levels."""
        has_category_id = self.category_id is not None
        has_category_name = bool(self.category_name and self.category_name.strip())
        if not has_category_id and not has_category_name:
            raise ValueError("Provide category_id or category_name")

        has_subcategory_id = self.subcategory_id is not None
        has_subcategory_name = bool(self.subcategory_name and self.subcategory_name.strip())
        if not has_subcategory_id and not has_subcategory_name:
            raise ValueError("Provide subcategory_id or subcategory_name")

        return self


class AdminFoodResponse(BaseModel):
    da_code: int
    food: FoodOut
