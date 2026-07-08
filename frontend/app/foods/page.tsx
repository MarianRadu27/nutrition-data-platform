"use client";

import React, { useEffect, useMemo, useState } from "react";

type Lang = "en" | "ro";
type SortDirection = "asc" | "desc";

type Category = {
  id: number;
  name: string;
  name_ro: string | null;
  name_display: string;
};

type Subcategory = {
  id: number;
  category_id: number;
  name: string;
  name_ro: string | null;
  name_display: string;
};

type NutrientField =
  | "wt_g"
  | "h2o_g"
  | "ener_kcal"
  | "prot_g"
  | "carbo_g"
  | "fiber_g"
  | "fat_g"
  | "sat_g"
  | "mono_g"
  | "poly_g"
  | "trans_g"
  | "chol_mg"
  | "calc_mg"
  | "iron_mg"
  | "magn_mg"
  | "pota_mg"
  | "sodi_mg"
  | "zinc_mg"
  | "vit_a_ug"
  | "vit_e_mg"
  | "thia_mg"
  | "ribo_mg"
  | "niac_mg"
  | "vit_b6_mg"
  | "fola_ug"
  | "vit_c_mg"
  | "vit_b12_ug"
  | "sele_ug";

type NutrientValueNote = {
  raw: string;
  qualifier: "lt" | "trace";
  limit: number | null;
};

type NutrientValueNotes = Partial<Record<NutrientField, NutrientValueNote>>;

type Food = {
  id: number;
  da_code: number;
  subcategory_id: number | null;
  category_id: number | null;
  name_display: string;
  category_name_display: string | null;
  subcategory_name_display: string | null;
  quantity: number | null;
  measure: string | null;
  wt_g: number | null;
  ener_kcal: number | null;
  prot_g: number | null;
  carbo_g: number | null;
  fat_g: number | null;
  fiber_g: number | null;
  h2o_g: number | null;
  sat_g: number | null;
  mono_g: number | null;
  poly_g: number | null;
  trans_g: number | null;
  chol_mg: number | null;
  calc_mg: number | null;
  iron_mg: number | null;
  magn_mg: number | null;
  pota_mg: number | null;
  sodi_mg: number | null;
  zinc_mg: number | null;
  vit_a_ug: number | null;
  vit_e_mg: number | null;
  thia_mg: number | null;
  ribo_mg: number | null;
  niac_mg: number | null;
  vit_b6_mg: number | null;
  fola_ug: number | null;
  vit_c_mg: number | null;
  vit_b12_ug: number | null;
  sele_ug: number | null;
  nutrient_value_notes: NutrientValueNotes | null;
};

type FoodsResponse = {
  items: Food[];
  limit: number;
  offset: number;
  count: number;
};

type FoodGroup = {
  // This group represents one Food section inside a Category.
  key: string;
  name: string;
  items: Food[];
};

type CategoryGroup = {
  // This group represents one Category section that contains multiple Food groups.
  key: string;
  name: string;
  foods: FoodGroup[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";
const LANG_KEY = "app_lang";

type ExtraNutrientColumn = {
  label: string;
  field: NutrientField;
  getValue: (food: Food) => number | null;
};

const EXTRA_NUTRIENT_COLUMNS: ExtraNutrientColumn[] = [
  // These columns are shown only when the general nutrients button is active.
  { label: "Water (g)", field: "h2o_g", getValue: (food) => food.h2o_g },
  { label: "Saturated fat (g)", field: "sat_g", getValue: (food) => food.sat_g },
  { label: "Monounsaturated fat (g)", field: "mono_g", getValue: (food) => food.mono_g },
  { label: "Polyunsaturated fat (g)", field: "poly_g", getValue: (food) => food.poly_g },
  { label: "Trans fat (g)", field: "trans_g", getValue: (food) => food.trans_g },
  { label: "Cholesterol (mg)", field: "chol_mg", getValue: (food) => food.chol_mg },
  { label: "Calcium (mg)", field: "calc_mg", getValue: (food) => food.calc_mg },
  { label: "Iron (mg)", field: "iron_mg", getValue: (food) => food.iron_mg },
  { label: "Magnesium (mg)", field: "magn_mg", getValue: (food) => food.magn_mg },
  { label: "Potassium (mg)", field: "pota_mg", getValue: (food) => food.pota_mg },
  { label: "Sodium (mg)", field: "sodi_mg", getValue: (food) => food.sodi_mg },
  { label: "Zinc (mg)", field: "zinc_mg", getValue: (food) => food.zinc_mg },
  { label: "Vitamin A (ug)", field: "vit_a_ug", getValue: (food) => food.vit_a_ug },
  { label: "Vitamin E (mg)", field: "vit_e_mg", getValue: (food) => food.vit_e_mg },
  { label: "Thiamin (mg)", field: "thia_mg", getValue: (food) => food.thia_mg },
  { label: "Riboflavin (mg)", field: "ribo_mg", getValue: (food) => food.ribo_mg },
  { label: "Niacin (mg)", field: "niac_mg", getValue: (food) => food.niac_mg },
  { label: "Vitamin B6 (mg)", field: "vit_b6_mg", getValue: (food) => food.vit_b6_mg },
  { label: "Folate (ug)", field: "fola_ug", getValue: (food) => food.fola_ug },
  { label: "Vitamin C (mg)", field: "vit_c_mg", getValue: (food) => food.vit_c_mg },
  { label: "Vitamin B12 (ug)", field: "vit_b12_ug", getValue: (food) => food.vit_b12_ug },
  { label: "Selenium (ug)", field: "sele_ug", getValue: (food) => food.sele_ug },
];

function formatNumber(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "-";
  }
  return value.toFixed(2);
}

function formatNutrientValue(
  food: Food,
  field: NutrientField,
  value: number | null,
): string {
  const note = food.nutrient_value_notes?.[field];
  return note?.raw ?? formatNumber(value);
}

function groupFoodsByCategoryAndFood(items: Food[]): CategoryGroup[] {
  // We use maps internally so each category and food group is created only once.
  const categoryMap = new Map<string, CategoryGroup>();

  for (const item of items) {
    const categoryName = item.category_name_display ?? "Uncategorized";
    const foodName = item.subcategory_name_display ?? "Other";

    let categoryGroup = categoryMap.get(categoryName);

    if (!categoryGroup) {
      categoryGroup = {
        key: categoryName,
        name: categoryName,
        foods: [],
      };

      categoryMap.set(categoryName, categoryGroup);
    }

    let foodGroup = categoryGroup.foods.find((group) => group.name === foodName);

    if (!foodGroup) {
      foodGroup = {
        key: `${categoryName}-${foodName}`,
        name: foodName,
        items: [],
      };

      categoryGroup.foods.push(foodGroup);
    }

    foodGroup.items.push(item);
  }

  return Array.from(categoryMap.values());
}

function sortFoodsByName(items: Food[], direction: SortDirection): Food[] {
  // We copy the array before sorting so we do not mutate the original API response.
  return [...items].sort((firstFood, secondFood) => {
    const comparison = firstFood.name_display.localeCompare(secondFood.name_display);

    return direction === "asc" ? comparison : -comparison;
  });
}

export default function FoodsPage() {
  // Filter and UI state are kept separately so typing does not immediately refetch.
  const [lang, setLang] = useState<Lang>("en");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [limitInput, setLimitInput] = useState("5000");
  const [limit, setLimit] = useState(5000);
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [categories, setCategories] = useState<Category[]>([]);
  const [subcategories, setSubcategories] = useState<Subcategory[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>("");
  const [selectedSubcategoryId, setSelectedSubcategoryId] = useState<string>("");
  const [foodsData, setFoodsData] = useState<FoodsResponse | null>(null);
  const [showExtraNutrients, setShowExtraNutrients] = useState(false);
  const [hoveredFoodId, setHoveredFoodId] = useState<number | null>(null);
  const [openCategoryKeys, setOpenCategoryKeys] = useState<string[]>([]);
  const [openFoodKeys, setOpenFoodKeys] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Persisting language locally keeps Foods and Calculator in the same language.
    const stored = window.localStorage.getItem(LANG_KEY);
    if (stored === "en" || stored === "ro") {
      setLang(stored);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(LANG_KEY, lang);
  }, [lang]);

  useEffect(() => {
    // Categories depend on lang because the backend returns name_display.
    async function loadCategories() {
      const response = await fetch(`${API_BASE}/api/categories?lang=${lang}`);
      if (!response.ok) {
        throw new Error("Failed to load categories");
      }
      const data = (await response.json()) as Category[];
      setCategories(data);
    }

    loadCategories().catch((err: unknown) => {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    });
  }, [lang]);

  useEffect(() => {
    if (!selectedCategoryId) {
      // A Food group belongs to one Category, so clearing Category resets Food too.
      setSubcategories([]);
      setSelectedSubcategoryId("");
      return;
    }

    async function loadSubcategories() {
      const response = await fetch(
        `${API_BASE}/api/categories/${selectedCategoryId}/subcategories?lang=${lang}`,
      );
      if (!response.ok) {
        throw new Error("Failed to load subcategories");
      }
      const data = (await response.json()) as Subcategory[];
      setSubcategories(data);
    }

    loadSubcategories().catch((err: unknown) => {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    });
  }, [selectedCategoryId, lang]);

  const foodsUrl = useMemo(() => {
    // useMemo keeps the fetch URL stable until one of its real inputs changes.
    const params = new URLSearchParams();
    params.set("lang", lang);
    params.set("limit", String(limit));
    params.set("offset", "0");
    if (search.trim()) {
      params.set("search", search.trim());
    }
    if (selectedCategoryId) {
      params.set("category_id", selectedCategoryId);
    }
    if (selectedSubcategoryId) {
      params.set("subcategory_id", selectedSubcategoryId);
    }
    return `${API_BASE}/api/foods?${params.toString()}`;
  }, [lang, limit, search, selectedCategoryId, selectedSubcategoryId]);

  const sortedFoods = foodsData ? sortFoodsByName(foodsData.items, sortDirection) : [];
  const groupedFoods = groupFoodsByCategoryAndFood(sortedFoods);

  function toggleCategory(categoryKey: string) {
    // Store only open keys; default behavior is collapsed.
    setOpenCategoryKeys((currentKeys) =>
      currentKeys.includes(categoryKey)
        ? currentKeys.filter((key) => key !== categoryKey)
        : [...currentKeys, categoryKey],
    );
  }

  function toggleFood(foodKey: string) {
    // Food groups are opened independently from their parent Category rows.
    setOpenFoodKeys((currentKeys) =>
      currentKeys.includes(foodKey)
        ? currentKeys.filter((key) => key !== foodKey)
        : [...currentKeys, foodKey],
    );
  }

  useEffect(() => {
    // Any filter change refetches the current food page.
    setLoading(true);
    setError(null);

    fetch(foodsUrl)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("Failed to load foods");
        }
        const data = (await response.json()) as FoodsResponse;
        setFoodsData(data);
      })
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Unknown error";
        setError(message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [foodsUrl]);

  return (
    <main style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h1>Foods</h1>
      <p>Browse foods and base nutrients per serving.</p>

      <section style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 16 }}>
        <button
          type="button"
          onClick={() => setLang("en")}
          disabled={lang === "en"}
          style={{ padding: "6px 12px" }}
        >
          EN
        </button>
        <button
          type="button"
          onClick={() => setLang("ro")}
          disabled={lang === "ro"}
          style={{ padding: "6px 12px" }}
        >
          RO
        </button>
      </section>

      <section style={{ display: "grid", gap: 12, maxWidth: 960, marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search food description name..."
            style={{ flex: 1, padding: 8 }}
          />
          <button type="button" onClick={() => setSearch(searchInput)}>
            Search
          </button>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <select
            value={selectedCategoryId}
            onChange={(event) => {
              setSelectedCategoryId(event.target.value);
              setSelectedSubcategoryId("");
            }}
            style={{ padding: 8, minWidth: 240 }}
          >
            <option value="">All categories</option>
            {categories.map((category) => (
              <option key={category.id} value={String(category.id)}>
                {category.name_display}
              </option>
            ))}
          </select>

          <select
            value={selectedSubcategoryId}
            onChange={(event) => setSelectedSubcategoryId(event.target.value)}
            style={{ padding: 8, minWidth: 240 }}
            disabled={!selectedCategoryId}
          >
            <option value="">All foods</option>
            {subcategories.map((subcategory) => (
              <option key={subcategory.id} value={String(subcategory.id)}>
                {subcategory.name_display}
              </option>
            ))}
          </select>

          <input
            type="number"
            min="1"
            max="5000"
            value={limitInput}
            onChange={(event) => setLimitInput(event.target.value)}
            style={{ padding: 8, width: 100 }}
          />

          <button
            type="button"
            onClick={() => {
              const nextLimit = Number(limitInput);

              if (Number.isFinite(nextLimit) && nextLimit > 0) {
                setLimit(nextLimit);
              }
            }}
            style={{ padding: 8 }}
          >
            Apply rows
          </button>

          <button
            type="button"
            onClick={() => {
              if (foodsData) {
                setLimitInput(String(foodsData.count));
                setLimit(foodsData.count);
              }
            }}
            style={{ padding: 8 }}
          >
            All
          </button>

          <select
            value={sortDirection}
            onChange={(event) => setSortDirection(event.target.value as SortDirection)}
            style={{ padding: 8, minWidth: 120 }}
          >
            <option value="asc">Sort A-Z</option>
            <option value="desc">Sort Z-A</option>
          </select>

          <button
            type="button"
            onClick={() => setShowExtraNutrients((currentValue) => !currentValue)}
            style={{ padding: 8 }}
          >
            {showExtraNutrients ? "Show Less Nutrients" : "Show More Nutrients"}
          </button>
        </div>
      </section>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {!loading && foodsData && (
        <section>
          <p>
            Showing {foodsData.items.length} / {foodsData.count}
          </p>
          {foodsData.items.length < foodsData.count && (
            <p style={{ color: "#fc0f0f" }}>
              Groups may be incomplete because only part of the table is loaded. To see all the data, you need to load ALL rows.
            </p>
          )}
          <div style={{ overflowX: "auto" }}>
            <table style={{ borderCollapse: "collapse", width: "100%", minWidth: 980 }}>
              <thead>
                <tr>
                  {[
                    "Food Description",
                    "Qty",
                    "Measure",
                    "Wt (g)",
                    "Kcal",
                    "Protein (g)",
                    "Carbs (g)",
                    "Fat (g)",
                    "Fiber (g)",
                    ...(showExtraNutrients ? EXTRA_NUTRIENT_COLUMNS.map((column) => column.label) : []),
                  ].map((header) => (
                    <th
                      key={header}
                      style={{
                        border: "1px solid #ccc",
                        padding: 8,
                        textAlign: "left",
                        backgroundColor: "#f4f4f4",
                      }}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {groupedFoods.map((categoryGroup) => {
                  const isCategoryOpen = openCategoryKeys.includes(categoryGroup.key);

                  return (
                    <React.Fragment key={categoryGroup.key}>
                      {/* Category section row. */}
                      <tr onClick={() => toggleCategory(categoryGroup.key)} style={{ cursor: "pointer" }}>
                        <td
                          colSpan={showExtraNutrients ? 9 + EXTRA_NUTRIENT_COLUMNS.length : 9}
                          style={{
                            border: "1px solid #bbb",
                            padding: 10,
                            fontWeight: "bold",
                            backgroundColor: "#e8f0fe",
                          }}
                        >
                          {isCategoryOpen ? "v" : ">"} Category: {categoryGroup.name}
                        </td>
                      </tr>

                      {isCategoryOpen &&
                        categoryGroup.foods.map((foodGroup) => {
                          const isFoodOpen = openFoodKeys.includes(foodGroup.key);

                          return (
                            <React.Fragment key={foodGroup.key}>
                              {/* Food section row inside the current category. */}
                              <tr onClick={() => toggleFood(foodGroup.key)} style={{ cursor: "pointer" }}>
                                <td
                                  colSpan={showExtraNutrients ? 9 + EXTRA_NUTRIENT_COLUMNS.length : 9}
                                  style={{
                                    border: "1px solid #ccc",
                                    padding: 8,
                                    paddingLeft: 24,
                                    fontWeight: "bold",
                                    backgroundColor: "#f6f8fa",
                                  }}
                                >
                                  {isFoodOpen ? "v" : ">"} Food: {foodGroup.name}
                                </td>
                              </tr>

                              {isFoodOpen &&
                                foodGroup.items.map((food) => (
                                  <tr
                                    key={food.id}
                                    onMouseEnter={() => setHoveredFoodId(food.id)}
                                    onMouseLeave={() => setHoveredFoodId(null)}
                                    style={{
                                      backgroundColor: hoveredFoodId === food.id ? "#fff7d6" : "transparent",
                                    }}
                                  >
                                    <td style={{ border: "1px solid #ddd", padding: 8 }}>{food.name_display}</td>
                                    <td style={{ border: "1px solid #ddd", padding: 8 }}>
                                      {formatNumber(food.quantity)}
                                    </td>
                                    <td style={{ border: "1px solid #ddd", padding: 8 }}>{food.measure ?? "-"}</td>
                                    <td style={{ border: "1px solid #ddd", padding: 8 }}>
                                      {formatNutrientValue(food, "wt_g", food.wt_g)}
                                    </td>
                                    <td style={{ border: "1px solid #ddd", padding: 8 }}>
                                      {formatNutrientValue(food, "ener_kcal", food.ener_kcal)}
                                    </td>
                                    <td style={{ border: "1px solid #ddd", padding: 8 }}>
                                      {formatNutrientValue(food, "prot_g", food.prot_g)}
                                    </td>
                                    <td style={{ border: "1px solid #ddd", padding: 8 }}>
                                      {formatNutrientValue(food, "carbo_g", food.carbo_g)}
                                    </td>
                                    <td style={{ border: "1px solid #ddd", padding: 8 }}>
                                      {formatNutrientValue(food, "fat_g", food.fat_g)}
                                    </td>
                                    <td style={{ border: "1px solid #ddd", padding: 8 }}>
                                      {formatNutrientValue(food, "fiber_g", food.fiber_g)}
                                    </td>

                                    {showExtraNutrients &&
                                      EXTRA_NUTRIENT_COLUMNS.map((column) => (
                                        <td key={column.label} style={{ border: "1px solid #ddd", padding: 8}}>
                                          {formatNutrientValue(food, column.field, column.getValue(food))}
                                        </td>
                                      ))}
                                  </tr>
                                ))}
                            </React.Fragment>
                          );
                        })}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </main>
  );
}
