"use client";

import { useEffect, useMemo, useState } from "react";

type Lang = "en" | "ro";

type FoodSearchItem = {
  id: number;
  category_id: number | null;
  subcategory_id: number | null;
  name_display: string;
  category_name_display: string | null;
  subcategory_name_display: string | null;
  quantity: number | null;
  measure: string | null;
  wt_g: number | null;
};

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

type MealEntry = {
  food_id: number;
  category_name: string;
  subcategory_name: string;
  name: string;
  grams: number;
};

type CalcNutrientField = "kcal" | "protein_g" | "carbs_g" | "fat_g" | "fiber_g";

type NutrientValueNote = {
  raw: string;
  qualifier: "lt" | "trace";
  limit: number | null;
};

type CalcItem = {
  food_id: number;
  name: string;
  grams: number;
  factor: number | null;
  nutrients: Record<CalcNutrientField, number>;
  nutrient_value_notes: Partial<Record<CalcNutrientField, NutrientValueNote>> | null;
  incomplete_data: boolean;
  error: string | null;
};

type CalcResponse = {
  totals: {
    kcal: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    fiber_g: number;
  };
  incomplete_data: boolean;
  items: CalcItem[];
};

type CalcGroup = {
  grams: number;
  items: CalcItem[];
};

type NutrientTotals = {
  kcal: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";
const LANG_KEY = "app_lang";

function formatNumber(value: number): string {
  return value.toFixed(2);
}

function formatCalcNutrient(item: CalcItem, field: CalcNutrientField): string {
  const value = formatNumber(item.nutrients[field]);
  const note = item.nutrient_value_notes?.[field];
  return note ? `${value} (${note.raw} source)` : value;
}

function hasBelowLimitNotes(items: CalcItem[]): boolean {
  return items.some((item) => {
    const notes = item.nutrient_value_notes;
    return notes ? Object.keys(notes).length > 0 : false;
  });
}

function findMealEntry(
  mealItems: MealEntry[],
  foodId: number,
): MealEntry | undefined {
  // The calculation result only has food_id, so we look up display details from the selected meal items.
  return mealItems.find((item) => item.food_id === foodId);
}

function groupCalcItemsByGrams(items: CalcItem[]): CalcGroup[] {
  // Each group becomes one results table for foods calculated with the same grams value.
  const groupMap = new Map<number, CalcGroup>();

  for (const item of items) {
    let group = groupMap.get(item.grams);

    if (!group) {
      group = {
        grams: item.grams,
        items: [],
      };

      groupMap.set(item.grams, group);
    }

    group.items.push(item);
  }

  return Array.from(groupMap.values()).sort(
    (firstGroup, secondGroup) => firstGroup.grams - secondGroup.grams,
  );
}

function sumCalcItems(items: CalcItem[]): NutrientTotals {
  // Sum all calculated nutrients in one grams group.
  return items.reduce(
    (totals, item) => ({
      kcal: totals.kcal + item.nutrients.kcal,
      protein_g: totals.protein_g + item.nutrients.protein_g,
      carbs_g: totals.carbs_g + item.nutrients.carbs_g,
      fat_g: totals.fat_g + item.nutrients.fat_g,
      fiber_g: totals.fiber_g + item.nutrients.fiber_g,
    }),
    {
      kcal: 0,
      protein_g: 0,
      carbs_g: 0,
      fat_g: 0,
      fiber_g: 0,
    },
  );
}

export default function CalculatorPage() {
  // Search state describes the picker; mealItems describes what the user selected.
  const [lang, setLang] = useState<Lang>("en");
  const [searchInput, setSearchInput] = useState("");
  const [searchResults, setSearchResults] = useState<FoodSearchItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [subcategories, setSubcategories] = useState<Subcategory[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState("");
  const [selectedSubcategoryId, setSelectedSubcategoryId] = useState("");
  const [selectedFoodId, setSelectedFoodId] = useState("");
  const [mealItems, setMealItems] = useState<MealEntry[]>([]);
  const [calcResult, setCalcResult] = useState<CalcResponse | null>(null);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingCalc, setLoadingCalc] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const calcGroups = calcResult ? groupCalcItemsByGrams(calcResult.items) : [];

  useEffect(() => {
    // Reuse the same language preference as the foods page.
    const stored = window.localStorage.getItem(LANG_KEY);
    if (stored === "en" || stored === "ro") {
      setLang(stored);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(LANG_KEY, lang);
  }, [lang]);

  useEffect(() => {
    // Category labels change when lang changes, so they are reloaded by language.
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
      // Food groups are only meaningful inside a selected Category.
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

  const searchUrl = useMemo(() => {
    // The food picker is /api/foods with filters; the backend handles search.
    const params = new URLSearchParams();
    params.set("lang", lang);
    params.set("limit", "5000");
    params.set("offset", "0");
    if (searchInput.trim()) {
      params.set("search", searchInput.trim());
    }

    if (selectedCategoryId) {
      params.set("category_id", selectedCategoryId);
    }
    if (selectedSubcategoryId) {
      params.set("subcategory_id", selectedSubcategoryId);
    }
    return `${API_BASE}/api/foods?${params.toString()}`;
  }, [lang, searchInput, selectedCategoryId, selectedSubcategoryId]);

  useEffect(() => {
    // Refetch the picker any time filters or search text change.
    setLoadingSearch(true);
    setError(null);
    fetch(searchUrl)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("Failed to search foods");
        }
        const payload = (await response.json()) as { items: FoodSearchItem[] };
        setSearchResults(payload.items);
      })
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Unknown error";
        setError(message);
      })
      .finally(() => setLoadingSearch(false));
  }, [searchUrl]);

  function addFood(food: FoodSearchItem) {
    setMealItems((current) => {
      // Prevent duplicates; grams can be edited after selection.
      const exists = current.some((item) => item.food_id === food.id);
      if (exists) {
        return current;
      }
      return [
        ...current,
        {
          food_id: food.id,
          category_name: food.category_name_display ?? "-",
          subcategory_name: food.subcategory_name_display ?? "-",
          name: food.name_display,
          grams: 100,
        },
      ];
    });
  }

  function updateGrams(foodId: number, grams: number) {
    // Keep the selected food identity stable while changing only its grams.
    setMealItems((current) =>
      current.map((item) =>
        item.food_id === foodId ? { ...item, grams } : item,
      ),
    );
  }

  function removeMealItem(foodId: number) {
    setMealItems((current) =>
      current.filter((item) => item.food_id !== foodId),
    );
  }

  async function calculateMeal() {
    if (mealItems.length === 0) {
      setError("Add at least one food before calculating");
      return;
    }

    setLoadingCalc(true);
    setError(null);
    setCalcResult(null);

    try {
      // The backend does nutrient math so UI and API stay consistent.
      const response = await fetch(`${API_BASE}/api/calc/meal?lang=${lang}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: mealItems.map((item) => ({
            food_id: item.food_id,
            grams: item.grams,
          })),
        }),
      });

      if (!response.ok) {
        const payload = (await response.json()) as { detail?: string };
        throw new Error(payload.detail ?? "Calculation failed");
      }

      const payload = (await response.json()) as CalcResponse;
      setCalcResult(payload);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setLoadingCalc(false);
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h1>Meal Calculator</h1>
      <p>Compute totals by grams using wt_g as scaling base.</p>

      <section style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <button
          type="button"
          onClick={() => setLang("en")}
          disabled={lang === "en"}
        >
          EN
        </button>
        <button
          type="button"
          onClick={() => setLang("ro")}
          disabled={lang === "ro"}
        >
          RO
        </button>
      </section>

      <section style={{ display: "grid", gap: 8, marginBottom: 16 }}>
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

          <select
            value={selectedFoodId}
            onChange={(event) => {
              const foodId = event.target.value;
              setSelectedFoodId(foodId);

              const selectedFood = searchResults.find(
                (food) => String(food.id) === foodId,
              );

              if (selectedFood) {
                addFood(selectedFood);
              }
            }}
            style={{ padding: 8, minWidth: 280 }}
          >
            <option value="">All food descriptions</option>
            {searchResults.map((food) => (
              <option key={food.id} value={String(food.id)}>
                {food.name_display}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section style={{ marginBottom: 16 }}>
        <h2>Meal Items</h2>
        {mealItems.length === 0 && <p>No foods selected yet.</p>}
        {mealItems.length > 0 && (
          <table style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr>
                {[
                  "Category",
                  "Food",
                  "Food Description",
                  "Grams",
                  "Remove",
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
              {mealItems.map((item) => (
                <tr key={item.food_id}>
                  <td style={{ border: "1px solid #ddd", padding: 8 }}>
                    {item.category_name}
                  </td>
                  <td style={{ border: "1px solid #ddd", padding: 8 }}>
                    {item.subcategory_name}
                  </td>
                  <td style={{ border: "1px solid #ddd", padding: 8 }}>
                    {item.name}
                  </td>
                  <td style={{ border: "1px solid #ddd", padding: 8 }}>
                    <input
                      type="number"
                      value={item.grams}
                      min={1}
                      step={1}
                      onChange={(event) =>
                        updateGrams(item.food_id, Number(event.target.value))
                      }
                      style={{ width: 100 }}
                    />
                  </td>
                  <td style={{ border: "1px solid #ddd", padding: 8 }}>
                    <button
                      type="button"
                      onClick={() => removeMealItem(item.food_id)}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <button
          type="button"
          onClick={calculateMeal}
          disabled={loadingCalc || mealItems.length === 0}
          style={{ marginTop: 12 }}
        >
          {loadingCalc ? "Calculating..." : "Calculate"}
        </button>
      </section>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {calcResult && (
        <section>
          <h2>Totals</h2>
          {calcResult.incomplete_data && (
            <p style={{ color: "darkorange" }}>
              Warning: some nutrients are missing, totals may be underestimated.
            </p>
          )}
          {hasBelowLimitNotes(calcResult.items) && (
            <p style={{ color: "darkorange" }}>
              Some source values were below reporting limits and were calculated as 0.
            </p>
          )}
          {calcGroups.map((group) => {
            const groupTotals = sumCalcItems(group.items);

            return (
              <section key={group.grams} style={{ marginBottom: 16 }}>
                <h3>Calculated for {formatNumber(group.grams)} g</h3>

                <table style={{ borderCollapse: "collapse", width: "100%" }}>
                  <thead>
                    <tr>
                      {[
                        "Category",
                        "Food",
                        "Food Description",
                        "Grams",
                        "Factor",
                        "Kcal",
                        "Protein (g)",
                        "Carbs (g)",
                        "Fat (g)",
                        "Fiber (g)",
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
                    {group.items.map((item) => {
                      const mealEntry = findMealEntry(mealItems, item.food_id);

                      return (
                        <tr key={item.food_id}>
                          <td style={{ border: "1px solid #ddd", padding: 8 }}>
                            {mealEntry?.category_name ?? "-"}
                          </td>
                          <td style={{ border: "1px solid #ddd", padding: 8 }}>
                            {mealEntry?.subcategory_name ?? "-"}
                          </td>
                          <td style={{ border: "1px solid #ddd", padding: 8 }}>
                            {item.name}
                          </td>
                          <td style={{ border: "1px solid #ddd", padding: 8 }}>
                            {formatNumber(item.grams)}
                          </td>
                          <td style={{ border: "1px solid #ddd", padding: 8 }}>
                            {item.factor === null
                              ? "-"
                              : item.factor.toFixed(4)}
                          </td>
                          <td style={{ border: "1px solid #ddd", padding: 8 }}>
                            {formatCalcNutrient(item, "kcal")}
                          </td>
                          <td style={{ border: "1px solid #ddd", padding: 8 }}>
                            {formatCalcNutrient(item, "protein_g")}
                          </td>
                          <td style={{ border: "1px solid #ddd", padding: 8 }}>
                            {formatCalcNutrient(item, "carbs_g")}
                          </td>
                          <td style={{ border: "1px solid #ddd", padding: 8 }}>
                            {formatCalcNutrient(item, "fat_g")}
                          </td>
                          <td style={{ border: "1px solid #ddd", padding: 8 }}>
                            {formatCalcNutrient(item, "fiber_g")}
                          </td>
                        </tr>
                      );
                    })}

                    <tr>
                      <td
                        colSpan={5}
                        style={{
                          border: "1px solid #ddd",
                          padding: 8,
                          fontWeight: "bold",
                        }}
                      >
                        TOTAL
                      </td>
                      <td
                        style={{
                          border: "1px solid #ddd",
                          padding: 8,
                          fontWeight: "bold",
                        }}
                      >
                        {formatNumber(groupTotals.kcal)}
                      </td>
                      <td
                        style={{
                          border: "1px solid #ddd",
                          padding: 8,
                          fontWeight: "bold",
                        }}
                      >
                        {formatNumber(groupTotals.protein_g)}
                      </td>
                      <td
                        style={{
                          border: "1px solid #ddd",
                          padding: 8,
                          fontWeight: "bold",
                        }}
                      >
                        {formatNumber(groupTotals.carbs_g)}
                      </td>
                      <td
                        style={{
                          border: "1px solid #ddd",
                          padding: 8,
                          fontWeight: "bold",
                        }}
                      >
                        {formatNumber(groupTotals.fat_g)}
                      </td>
                      <td
                        style={{
                          border: "1px solid #ddd",
                          padding: 8,
                          fontWeight: "bold",
                        }}
                      >
                        {formatNumber(groupTotals.fiber_g)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </section>
            );
          })}
        </section>
      )}
    </main>
  );
}
