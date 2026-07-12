"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type SourceCode = "NEVO" | "ANSES_CIQUAL";

type ExternalCategory = {
  category_original: string | null;
  category_en: string | null;
  category_ro: string | null;
  name_display: string;
  food_count: number;
};

type ExternalFood = {
  id: number;
  data_source_code: string;
  source_food_code: string;
  name_display: string;
  food_name_en: string | null;
  food_name_original: string | null;
  category_name_display: string | null;
  category_en: string | null;
  category_original: string | null;
  basis: string | null;
  notes: string | null;
};

type ExternalFoodsResponse = {
  items: ExternalFood[];
  limit: number;
  offset: number;
  count: number;
};

type ExternalNutrientValue = {
  source_nutrient_code: string;
  nutrient_name_display: string;
  source_standard_tag: string | null;
  canonical_code: string | null;
  canonical_name_display: string | null;
  raw_value: string | null;
  value: number | null;
  value_qualifier: string | null;
  unit: string | null;
  basis: string | null;
  reference_code: string | null;
};

type ExternalFoodNutrientsResponse = {
  food: ExternalFood;
  nutrients: ExternalNutrientValue[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";
const SEARCH_LIMIT = 50;

const SOURCES: Array<{ code: SourceCode; label: string; detail: string }> = [
  { code: "NEVO", label: "NEVO", detail: "Țările de Jos" },
  { code: "ANSES_CIQUAL", label: "ANSES/Ciqual", detail: "Franța" },
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

function formatNumber(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "-";
  }
  return value.toFixed(2);
}

function categoryFilterValue(category: ExternalCategory): string {
  return category.category_en ?? category.category_original ?? category.name_display;
}

function formatNotes(notes: string | null): string[] {
  if (!notes) {
    return [];
  }
  return notes.split("\n").filter(Boolean);
}

export default function FoodsPage() {
  const [selectedSource, setSelectedSource] = useState<SourceCode>("NEVO");
  const [categories, setCategories] = useState<ExternalCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [foodsData, setFoodsData] = useState<ExternalFoodsResponse | null>(null);
  const [selectedFoodDetails, setSelectedFoodDetails] =
    useState<ExternalFoodNutrientsResponse | null>(null);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [loadingFoods, setLoadingFoods] = useState(false);
  const [loadingDetailsId, setLoadingDetailsId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedSourceMeta = useMemo(
    () => SOURCES.find((source) => source.code === selectedSource) ?? SOURCES[0],
    [selectedSource],
  );

  useEffect(() => {
    async function loadCategories() {
      setLoadingCategories(true);
      setError(null);
      setCategories([]);
      setSelectedCategory("");
      setFoodsData(null);
      setSelectedFoodDetails(null);

      try {
        const response = await fetch(
          `${API_BASE}/api/external/sources/${selectedSource}/categories?lang=ro`,
        );
        if (!response.ok) {
          throw new Error("Nu am putut încărca lista de categorii.");
        }
        const payload = (await response.json()) as ExternalCategory[];
        setCategories(payload);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Eroare necunoscută";
        setError(message);
      } finally {
        setLoadingCategories(false);
      }
    }

    loadCategories();
  }, [selectedSource]);

  async function searchFoods(event?: FormEvent) {
    event?.preventDefault();
    setLoadingFoods(true);
    setError(null);
    setSelectedFoodDetails(null);

    try {
      const params = new URLSearchParams();
      params.set("lang", "ro");
      params.set("limit", String(SEARCH_LIMIT));
      params.set("offset", "0");

      if (searchInput.trim()) {
        params.set("search", searchInput.trim());
      }

      if (selectedCategory) {
        params.set("category", selectedCategory);
      }

      const response = await fetch(
        `${API_BASE}/api/external/sources/${selectedSource}/foods?${params.toString()}`,
      );

      if (!response.ok) {
        throw new Error("Nu am putut încărca alimentele.");
      }

      const payload = (await response.json()) as ExternalFoodsResponse;
      setFoodsData(payload);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Eroare necunoscută";
      setError(message);
      setFoodsData(null);
    } finally {
      setLoadingFoods(false);
    }
  }

  async function loadFoodDetails(food: ExternalFood) {
    setLoadingDetailsId(food.id);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/external/foods/${food.id}/nutrients?lang=ro&canonical_only=true`,
      );

      if (!response.ok) {
        throw new Error("Nu am putut încărca detaliile alimentului.");
      }

      const payload = (await response.json()) as ExternalFoodNutrientsResponse;
      setSelectedFoodDetails(payload);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Eroare necunoscută";
      setError(message);
    } finally {
      setLoadingDetailsId(null);
    }
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
            Bază de date alimente
          </p>
          <h1
            style={{
              fontSize: 46,
              lineHeight: 1.08,
              margin: "0 0 14px",
              maxWidth: 620,
            }}
          >
            Explorează alimente din surse europene validate.
          </h1>
          <p
            style={{
              color: "#52645b",
              fontSize: 18,
              lineHeight: 1.65,
              margin: 0,
              maxWidth: 660,
            }}
          >
            Compară structura datelor din NEVO și ANSES/Ciqual și verifică
            valorile canonice folosite de calculatorul nutrițional.
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
                  onClick={() => setSelectedSource(source.code)}
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
              gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr) auto",
              marginTop: 6,
            }}
          >
            <label>
              <span style={labelStyle}>Categorie</span>
              <select
                disabled={loadingCategories}
                onChange={(event) => setSelectedCategory(event.target.value)}
                style={inputStyle}
                value={selectedCategory}
              >
                <option value="">Toate categoriile</option>
                {categories.map((category) => (
                  <option
                    key={`${category.name_display}-${category.food_count}`}
                    value={categoryFilterValue(category)}
                  >
                    {category.name_display} ({category.food_count})
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span style={labelStyle}>Caută aliment</span>
              <input
                onChange={(event) => setSearchInput(event.target.value)}
                placeholder="ex: banana, potato, milk"
                style={inputStyle}
                value={searchInput}
              />
            </label>

            <button
              disabled={loadingFoods}
              style={{ ...primaryButtonStyle, alignSelf: "end" }}
              type="submit"
            >
              {loadingFoods ? "Caut..." : "Caută"}
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
          gridTemplateColumns: "minmax(320px, 0.85fr) minmax(0, 1.15fr)",
        }}
      >
        <div style={{ ...panelStyle, overflow: "hidden" }}>
          <div
            style={{
              borderBottom: "1px solid rgba(23, 33, 29, 0.1)",
              padding: "18px 20px",
            }}
          >
            <h2 style={{ fontSize: 20, margin: 0 }}>
              {selectedSourceMeta.label}
            </h2>
            <p style={{ color: "#52645b", lineHeight: 1.5, margin: "6px 0 0" }}>
              {foodsData
                ? `${foodsData.items.length} afișate din ${foodsData.count} rezultate`
                : "Alege o categorie sau caută după numele alimentului."}
            </p>
          </div>

          {loadingFoods && (
            <p style={{ color: "#52645b", margin: 0, padding: 20 }}>
              Se încarcă alimentele...
            </p>
          )}

          {!loadingFoods && !foodsData && (
            <p style={{ color: "#52645b", lineHeight: 1.55, margin: 0, padding: 20 }}>
              Caută un aliment ca să vezi valorile nutriționale canonice.
            </p>
          )}

          {!loadingFoods && foodsData?.items.length === 0 && (
            <p style={{ color: "#52645b", lineHeight: 1.55, margin: 0, padding: 20 }}>
              Nu am găsit alimente pentru filtrul ales.
            </p>
          )}

          {!loadingFoods &&
            foodsData?.items.map((food) => {
              const isSelected = selectedFoodDetails?.food.id === food.id;

              return (
                <button
                  key={food.id}
                  onClick={() => loadFoodDetails(food)}
                  style={{
                    backgroundColor: isSelected ? "#eef4ef" : "#ffffff",
                    border: 0,
                    borderBottom: "1px solid rgba(23, 33, 29, 0.08)",
                    color: "#17211d",
                    cursor: "pointer",
                    display: "grid",
                    gap: 7,
                    padding: "15px 20px",
                    textAlign: "left",
                    width: "100%",
                  }}
                  type="button"
                >
                  <strong style={{ fontSize: 15, lineHeight: 1.35 }}>
                    {food.name_display}
                  </strong>
                  <span style={{ color: "#52645b", fontSize: 13 }}>
                    {food.category_name_display ?? "Fără categorie"} ·{" "}
                    {food.basis ?? "per_100g"} · cod {food.source_food_code}
                  </span>
                  {loadingDetailsId === food.id && (
                    <span style={{ color: "#2d5f4c", fontSize: 13 }}>
                      Se încarcă detaliile...
                    </span>
                  )}
                </button>
              );
            })}
        </div>

        <div style={{ ...panelStyle, overflow: "hidden" }}>
          <div
            style={{
              borderBottom: "1px solid rgba(23, 33, 29, 0.1)",
              padding: "18px 20px",
            }}
          >
            <h2 style={{ fontSize: 20, margin: 0 }}>Detalii aliment</h2>
          </div>

          {!selectedFoodDetails ? (
            <p style={{ color: "#52645b", lineHeight: 1.55, margin: 0, padding: 20 }}>
              Selectează un aliment din listă pentru a vedea nutrienții canonici.
            </p>
          ) : (
            <>
              <div style={{ padding: "20px 20px 8px" }}>
                <p
                  style={{
                    color: "#2d5f4c",
                    fontSize: 13,
                    fontWeight: 800,
                    margin: "0 0 8px",
                    textTransform: "uppercase",
                  }}
                >
                  {selectedFoodDetails.food.data_source_code}
                </p>
                <h3 style={{ fontSize: 28, lineHeight: 1.18, margin: "0 0 10px" }}>
                  {selectedFoodDetails.food.name_display}
                </h3>
                <p style={{ color: "#52645b", lineHeight: 1.55, margin: 0 }}>
                  {selectedFoodDetails.food.category_name_display ?? "Fără categorie"} ·{" "}
                  {selectedFoodDetails.food.basis ?? "per_100g"} · cod sursă{" "}
                  {selectedFoodDetails.food.source_food_code}
                </p>
                {formatNotes(selectedFoodDetails.food.notes).length > 0 && (
                  <div
                    style={{
                      color: "#52645b",
                      display: "grid",
                      fontSize: 13,
                      gap: 4,
                      lineHeight: 1.5,
                      marginTop: 12,
                    }}
                  >
                    {formatNotes(selectedFoodDetails.food.notes).map((note) => (
                      <span key={note}>{note}</span>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ overflowX: "auto" }}>
                <table
                  style={{
                    borderCollapse: "collapse",
                    minWidth: 780,
                    width: "100%",
                  }}
                >
                  <thead>
                    <tr>
                      {[
                        "Nutrient",
                        "Cod canonic",
                        "Valoare",
                        "Unitate",
                        "Valoare sursă",
                        "Cod sursă",
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
                    {selectedFoodDetails.nutrients.map((nutrient) => (
                      <tr key={`${nutrient.source_nutrient_code}-${nutrient.canonical_code}`}>
                        <td
                          style={{
                            borderBottom: "1px solid rgba(23, 33, 29, 0.09)",
                            padding: "13px 12px",
                          }}
                        >
                          <strong>
                            {nutrient.canonical_name_display ??
                              nutrient.nutrient_name_display}
                          </strong>
                        </td>
                        <td
                          style={{
                            borderBottom: "1px solid rgba(23, 33, 29, 0.09)",
                            color: "#52645b",
                            padding: "13px 12px",
                          }}
                        >
                          {nutrient.canonical_code ?? "-"}
                        </td>
                        <td
                          style={{
                            borderBottom: "1px solid rgba(23, 33, 29, 0.09)",
                            padding: "13px 12px",
                          }}
                        >
                          {formatNumber(nutrient.value)}
                        </td>
                        <td
                          style={{
                            borderBottom: "1px solid rgba(23, 33, 29, 0.09)",
                            color: "#52645b",
                            padding: "13px 12px",
                          }}
                        >
                          {nutrient.unit ?? "-"}
                        </td>
                        <td
                          style={{
                            borderBottom: "1px solid rgba(23, 33, 29, 0.09)",
                            color: nutrient.value_qualifier ? "#9a5a32" : "#52645b",
                            padding: "13px 12px",
                          }}
                        >
                          {nutrient.raw_value ?? "-"}
                          {nutrient.value_qualifier && (
                            <span style={{ display: "block", fontSize: 12 }}>
                              {nutrient.value_qualifier}
                            </span>
                          )}
                        </td>
                        <td
                          style={{
                            borderBottom: "1px solid rgba(23, 33, 29, 0.09)",
                            color: "#52645b",
                            padding: "13px 12px",
                          }}
                        >
                          {nutrient.source_nutrient_code}
                          {nutrient.source_standard_tag && (
                            <span style={{ display: "block", fontSize: 12 }}>
                              {nutrient.source_standard_tag}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
