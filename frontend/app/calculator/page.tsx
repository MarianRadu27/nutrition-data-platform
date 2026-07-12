"use client";

import { FormEvent, useMemo, useState } from "react";

type SourceCode = "NEVO" | "ANSES_CIQUAL";

type ExternalFood = {
  id: number;
  data_source_code: string;
  source_food_code: string;
  name_display: string;
  category_name_display: string | null;
  basis: string | null;
};

type ExternalFoodsResponse = {
  items: ExternalFood[];
  limit: number;
  offset: number;
  count: number;
};

type NutrientKey =
  | "energy_kcal"
  | "protein_g"
  | "carbohydrate_g"
  | "fat_g"
  | "fiber_g";

type ExternalNutrientValue = {
  canonical_code: string | null;
  canonical_name_display: string | null;
  raw_value: string | null;
  value: number | null;
  value_qualifier: string | null;
  unit: string | null;
  basis: string | null;
};

type ExternalFoodNutrientsResponse = {
  food: ExternalFood;
  nutrients: ExternalNutrientValue[];
};

type MealItem = {
  id: number;
  food: ExternalFood;
  grams: number;
  nutrients: Partial<Record<NutrientKey, ExternalNutrientValue>>;
};

type NutrientColumn = {
  key: NutrientKey;
  label: string;
  unit: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";
const SEARCH_LIMIT = 25;

const SOURCES: Array<{ code: SourceCode; label: string; detail: string }> = [
  { code: "NEVO", label: "NEVO", detail: "Netherlands" },
  { code: "ANSES_CIQUAL", label: "ANSES/Ciqual", detail: "France" },
];

const NUTRIENT_COLUMNS: NutrientColumn[] = [
  { key: "energy_kcal", label: "Calorii", unit: "kcal" },
  { key: "protein_g", label: "Proteine", unit: "g" },
  { key: "carbohydrate_g", label: "Carbohidrați", unit: "g" },
  { key: "fat_g", label: "Grăsimi", unit: "g" },
  { key: "fiber_g", label: "Fibre", unit: "g" },
];

const shellStyle = {
  margin: "0 auto",
  maxWidth: 1180,
  padding: "42px 24px 72px",
} as const;

const panelStyle = {
  backgroundColor: "#ffffff",
  border: "1px solid rgba(23, 33, 29, 0.12)",
  borderRadius: 8,
  boxShadow: "0 18px 42px rgba(32, 45, 39, 0.08)",
} as const;

const labelStyle = {
  color: "#52645b",
  display: "block",
  fontSize: 13,
  fontWeight: 800,
  marginBottom: 7,
} as const;

const inputStyle = {
  border: "1px solid rgba(23, 33, 29, 0.18)",
  borderRadius: 8,
  boxSizing: "border-box",
  color: "#17211d",
  fontSize: 15,
  outline: "none",
  padding: "12px 13px",
  width: "100%",
} as const;

const primaryButtonStyle = {
  backgroundColor: "#1f4f40",
  border: "1px solid #1f4f40",
  borderRadius: 8,
  color: "#ffffff",
  cursor: "pointer",
  fontSize: 15,
  fontWeight: 800,
  padding: "12px 16px",
} as const;

const secondaryButtonStyle = {
  backgroundColor: "#ffffff",
  border: "1px solid rgba(23, 33, 29, 0.18)",
  borderRadius: 8,
  color: "#17211d",
  cursor: "pointer",
  fontSize: 14,
  fontWeight: 800,
  padding: "10px 13px",
} as const;

function formatNumber(value: number, digits = 2): string {
  return value.toFixed(digits);
}

function scaleValue(value: number | null | undefined, grams: number): number {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return 0;
  }
  return value * (grams / 100);
}

function buildNutrientMap(
  nutrients: ExternalNutrientValue[],
): Partial<Record<NutrientKey, ExternalNutrientValue>> {
  const map: Partial<Record<NutrientKey, ExternalNutrientValue>> = {};

  for (const nutrient of nutrients) {
    const canonicalCode = nutrient.canonical_code as NutrientKey | null;
    if (!canonicalCode) {
      continue;
    }

    if (NUTRIENT_COLUMNS.some((column) => column.key === canonicalCode)) {
      map[canonicalCode] = nutrient;
    }
  }

  return map;
}

function hasSourceMarker(item: MealItem): boolean {
  return NUTRIENT_COLUMNS.some((column) => {
    const nutrient = item.nutrients[column.key];
    return Boolean(nutrient?.value_qualifier && nutrient.raw_value);
  });
}

function hasMissingNutrient(item: MealItem): boolean {
  return NUTRIENT_COLUMNS.some((column) => !item.nutrients[column.key]);
}

export default function CalculatorPage() {
  const [selectedSource, setSelectedSource] = useState<SourceCode>("NEVO");
  const [searchInput, setSearchInput] = useState("");
  const [searchResults, setSearchResults] = useState<ExternalFood[]>([]);
  const [mealItems, setMealItems] = useState<MealItem[]>([]);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingFoodId, setLoadingFoodId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const totals = useMemo(() => {
    return NUTRIENT_COLUMNS.reduce(
      (acc, column) => {
        acc[column.key] = mealItems.reduce((sum, item) => {
          const nutrient = item.nutrients[column.key];
          return sum + scaleValue(nutrient?.value, item.grams);
        }, 0);
        return acc;
      },
      {} as Record<NutrientKey, number>,
    );
  }, [mealItems]);

  const sourceMarkersVisible = mealItems.some(hasSourceMarker);
  const missingValuesVisible = mealItems.some(hasMissingNutrient);

  async function searchFoods(event: FormEvent) {
    event.preventDefault();
    const query = searchInput.trim();
    if (!query) {
      setError("Scrie numele unui aliment.");
      setSearchResults([]);
      return;
    }

    setLoadingSearch(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.set("search", query);
      params.set("lang", "ro");
      params.set("limit", String(SEARCH_LIMIT));
      params.set("offset", "0");

      const response = await fetch(
        `${API_BASE}/api/external/sources/${selectedSource}/foods?${params.toString()}`,
      );

      if (!response.ok) {
        throw new Error("Căutarea nu a reușit.");
      }

      const payload = (await response.json()) as ExternalFoodsResponse;
      setSearchResults(payload.items);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Eroare necunoscută";
      setError(message);
      setSearchResults([]);
    } finally {
      setLoadingSearch(false);
    }
  }

  async function addFood(food: ExternalFood) {
    if (mealItems.some((item) => item.id === food.id)) {
      return;
    }

    setLoadingFoodId(food.id);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/external/foods/${food.id}/nutrients?lang=ro&canonical_only=true`,
      );

      if (!response.ok) {
        throw new Error("Nu am putut încărca nutrienții pentru aliment.");
      }

      const payload = (await response.json()) as ExternalFoodNutrientsResponse;
      setMealItems((currentItems) => [
        ...currentItems,
        {
          id: food.id,
          food: payload.food,
          grams: 100,
          nutrients: buildNutrientMap(payload.nutrients),
        },
      ]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Eroare necunoscută";
      setError(message);
    } finally {
      setLoadingFoodId(null);
    }
  }

  function updateGrams(foodId: number, grams: number) {
    setMealItems((currentItems) =>
      currentItems.map((item) =>
        item.id === foodId
          ? { ...item, grams: Number.isFinite(grams) && grams > 0 ? grams : 1 }
          : item,
      ),
    );
  }

  function removeFood(foodId: number) {
    setMealItems((currentItems) =>
      currentItems.filter((item) => item.id !== foodId),
    );
  }

  function renderNutrientCell(item: MealItem, column: NutrientColumn) {
    const nutrient = item.nutrients[column.key];
    const scaledValue = scaleValue(nutrient?.value, item.grams);

    return (
      <td
        key={column.key}
        style={{
          borderBottom: "1px solid rgba(23, 33, 29, 0.09)",
          padding: "14px 12px",
          verticalAlign: "top",
        }}
      >
        <strong>{formatNumber(scaledValue)}</strong>
        <span style={{ color: "#52645b", fontSize: 12 }}> {column.unit}</span>
        {nutrient?.value_qualifier && nutrient.raw_value && (
          <div style={{ color: "#9a5a32", fontSize: 12, marginTop: 4 }}>
            sursă: {nutrient.raw_value}
          </div>
        )}
        {!nutrient && (
          <div style={{ color: "#9a5a32", fontSize: 12, marginTop: 4 }}>
            lipsă în sursă
          </div>
        )}
      </td>
    );
  }

  return (
    <main style={shellStyle}>
      <section
        style={{
          display: "grid",
          gap: 28,
          gridTemplateColumns: "minmax(0, 0.9fr) minmax(0, 1.1fr)",
          marginBottom: 28,
        }}
      >
        <div>
          <p
            style={{
              color: "#2d5f4c",
              fontSize: 13,
              fontWeight: 800,
              margin: "0 0 12px",
              textTransform: "uppercase",
            }}
          >
            Calculator nutrițional
          </p>
          <h1
            style={{
              fontSize: 46,
              lineHeight: 1.08,
              margin: "0 0 14px",
              maxWidth: 620,
            }}
          >
            Calculează rapid macronutrienții pe baza sursei alese.
          </h1>
          <p
            style={{
              color: "#52645b",
              fontSize: 18,
              lineHeight: 1.65,
              margin: 0,
              maxWidth: 640,
            }}
          >
            Datele vin din surse alimentare europene importate în platformă.
          </p>
        </div>

        <div
          style={{
            ...panelStyle,
            alignSelf: "start",
            display: "grid",
            gap: 14,
            padding: 20,
          }}
        >
          <span style={labelStyle}>Sursă</span>
          <div style={{ display: "grid", gap: 10, gridTemplateColumns: "1fr 1fr" }}>
            {SOURCES.map((source) => {
              const isSelected = source.code === selectedSource;

              return (
                <button
                  key={source.code}
                  type="button"
                  onClick={() => {
                    setSelectedSource(source.code);
                    setSearchResults([]);
                    setError(null);
                  }}
                  style={{
                    border: isSelected
                      ? "1px solid #1f4f40"
                      : "1px solid rgba(23, 33, 29, 0.14)",
                    borderRadius: 8,
                    backgroundColor: isSelected ? "#e7f1ec" : "#ffffff",
                    color: "#17211d",
                    cursor: "pointer",
                    padding: "13px 14px",
                    textAlign: "left",
                  }}
                >
                  <strong style={{ display: "block", fontSize: 15 }}>
                    {source.label}
                  </strong>
                  <span style={{ color: "#52645b", fontSize: 12 }}>
                    {source.detail}
                  </span>
                </button>
              );
            })}
          </div>

          <form
            onSubmit={searchFoods}
            style={{
              display: "grid",
              gap: 10,
              gridTemplateColumns: "minmax(0, 1fr) auto",
              marginTop: 6,
            }}
          >
            <label>
              <span style={labelStyle}>Aliment</span>
              <input
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                placeholder="ex: banana, potato, milk"
                style={inputStyle}
              />
            </label>
            <button
              type="submit"
              disabled={loadingSearch}
              style={{ ...primaryButtonStyle, alignSelf: "end" }}
            >
              {loadingSearch ? "Caut..." : "Caută"}
            </button>
          </form>
        </div>
      </section>

      {error && (
        <p
          style={{
            backgroundColor: "#fff5f0",
            border: "1px solid #efb99b",
            borderRadius: 8,
            color: "#8a3f1f",
            margin: "0 0 18px",
            padding: "12px 14px",
          }}
        >
          {error}
        </p>
      )}

      <section
        style={{
          display: "grid",
          gap: 22,
          gridTemplateColumns: "minmax(300px, 0.8fr) minmax(0, 1.2fr)",
        }}
      >
        <div style={{ ...panelStyle, overflow: "hidden" }}>
          <div
            style={{
              borderBottom: "1px solid rgba(23, 33, 29, 0.1)",
              padding: "18px 20px",
            }}
          >
            <h2 style={{ fontSize: 20, margin: 0 }}>Rezultate căutare</h2>
          </div>

          <div style={{ display: "grid", gap: 0 }}>
            {searchResults.length === 0 && (
              <p style={{ color: "#52645b", lineHeight: 1.55, margin: 0, padding: 20 }}>
                Caută un aliment ca să îl adaugi în calcul.
              </p>
            )}

            {searchResults.map((food) => (
              <div
                key={food.id}
                style={{
                  borderBottom: "1px solid rgba(23, 33, 29, 0.08)",
                  display: "grid",
                  gap: 12,
                  gridTemplateColumns: "minmax(0, 1fr) auto",
                  padding: "15px 20px",
                }}
              >
                <div>
                  <strong style={{ display: "block", lineHeight: 1.35 }}>
                    {food.name_display}
                  </strong>
                  <span style={{ color: "#52645b", fontSize: 13 }}>
                    {food.category_name_display ?? "Fără categorie"} ·{" "}
                    {food.basis ?? "per_100g"}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => addFood(food)}
                  disabled={
                    loadingFoodId === food.id ||
                    mealItems.some((item) => item.id === food.id)
                  }
                  style={secondaryButtonStyle}
                >
                  {mealItems.some((item) => item.id === food.id)
                    ? "Adăugat"
                    : loadingFoodId === food.id
                      ? "..."
                      : "Adaugă"}
                </button>
              </div>
            ))}
          </div>
        </div>

        <div style={{ ...panelStyle, overflow: "hidden" }}>
          <div
            style={{
              alignItems: "center",
              borderBottom: "1px solid rgba(23, 33, 29, 0.1)",
              display: "flex",
              gap: 16,
              justifyContent: "space-between",
              padding: "18px 20px",
            }}
          >
            <h2 style={{ fontSize: 20, margin: 0 }}>Tabel calcul</h2>
            <span style={{ color: "#52645b", fontSize: 13 }}>
              {mealItems.length} alimente
            </span>
          </div>

          {mealItems.length === 0 ? (
            <p style={{ color: "#52645b", lineHeight: 1.55, margin: 0, padding: 20 }}>
              Adaugă cel puțin un aliment pentru tabelul de nutrienți.
            </p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table
                style={{
                  borderCollapse: "collapse",
                  minWidth: 920,
                  width: "100%",
                }}
              >
                <thead>
                  <tr>
                    {[
                      "Aliment",
                      "Sursă",
                      "Grame",
                      ...NUTRIENT_COLUMNS.map((column) => column.label),
                      "",
                    ].map((header) => (
                      <th
                        key={header}
                        style={{
                          backgroundColor: "#f2f5f1",
                          borderBottom: "1px solid rgba(23, 33, 29, 0.12)",
                          color: "#52645b",
                          fontSize: 12,
                          padding: "12px",
                          textAlign: "left",
                          textTransform: "uppercase",
                        }}
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {mealItems.map((item) => (
                    <tr key={item.id}>
                      <td
                        style={{
                          borderBottom: "1px solid rgba(23, 33, 29, 0.09)",
                          padding: "14px 12px",
                          verticalAlign: "top",
                        }}
                      >
                        <strong style={{ display: "block", lineHeight: 1.35 }}>
                          {item.food.name_display}
                        </strong>
                        <span style={{ color: "#52645b", fontSize: 12 }}>
                          {item.food.category_name_display ?? "Fără categorie"}
                        </span>
                      </td>
                      <td
                        style={{
                          borderBottom: "1px solid rgba(23, 33, 29, 0.09)",
                          padding: "14px 12px",
                          verticalAlign: "top",
                        }}
                      >
                        {item.food.data_source_code}
                      </td>
                      <td
                        style={{
                          borderBottom: "1px solid rgba(23, 33, 29, 0.09)",
                          padding: "14px 12px",
                          verticalAlign: "top",
                        }}
                      >
                        <input
                          min={1}
                          onChange={(event) =>
                            updateGrams(item.id, Number(event.target.value))
                          }
                          step={1}
                          type="number"
                          value={item.grams}
                          style={{ ...inputStyle, maxWidth: 92, padding: "9px 10px" }}
                        />
                      </td>
                      {NUTRIENT_COLUMNS.map((column) =>
                        renderNutrientCell(item, column),
                      )}
                      <td
                        style={{
                          borderBottom: "1px solid rgba(23, 33, 29, 0.09)",
                          padding: "14px 12px",
                          textAlign: "right",
                          verticalAlign: "top",
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => removeFood(item.id)}
                          style={{
                            ...secondaryButtonStyle,
                            color: "#8a3f1f",
                            padding: "9px 11px",
                          }}
                        >
                          Șterge
                        </button>
                      </td>
                    </tr>
                  ))}
                  <tr>
                    <td
                      colSpan={3}
                      style={{
                        backgroundColor: "#eef4ef",
                        fontWeight: 900,
                        padding: "15px 12px",
                      }}
                    >
                      Total
                    </td>
                    {NUTRIENT_COLUMNS.map((column) => (
                      <td
                        key={column.key}
                        style={{
                          backgroundColor: "#eef4ef",
                          fontWeight: 900,
                          padding: "15px 12px",
                        }}
                      >
                        {formatNumber(totals[column.key])}{" "}
                        <span style={{ color: "#52645b", fontSize: 12 }}>
                          {column.unit}
                        </span>
                      </td>
                    ))}
                    <td style={{ backgroundColor: "#eef4ef" }} />
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {(sourceMarkersVisible || missingValuesVisible) && (
            <div
              style={{
                borderTop: "1px solid rgba(23, 33, 29, 0.1)",
                color: "#52645b",
                display: "grid",
                gap: 6,
                fontSize: 13,
                lineHeight: 1.55,
                padding: "14px 20px",
              }}
            >
              {sourceMarkersVisible && (
                <span>
                  Valorile marcate cu sursă precum &lt; 0,01 sau traces sunt
                  calculate ca 0, dar textul original rămâne vizibil.
                </span>
              )}
              {missingValuesVisible && (
                <span>
                  Nutrienții lipsă în sursa aleasă sunt calculați ca 0 în total.
                </span>
              )}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
