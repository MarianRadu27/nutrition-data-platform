"use client";

import { FormEvent, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

type AdminResponse = {
  da_code: number;
  food: {
    id: number;
    name_display: string;
    da_code: number;
  };
};

export default function AdminAddFoodPage() {
  // The admin form allows either existing ids or new names for Category and Food.
  const [adminToken, setAdminToken] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [categoryName, setCategoryName] = useState("");
  const [categoryNameRo, setCategoryNameRo] = useState("");
  const [subcategoryId, setSubcategoryId] = useState("");
  const [subcategoryName, setSubcategoryName] = useState("");
  const [subcategoryNameRo, setSubcategoryNameRo] = useState("");
  const [foodDescription, setFoodDescription] = useState("");
  const [foodDescriptionRo, setFoodDescriptionRo] = useState("");
  const [quantity, setQuantity] = useState("");
  const [measure, setMeasure] = useState("");
  const [wtG, setWtG] = useState("");
  const [enerKcal, setEnerKcal] = useState("");
  const [protG, setProtG] = useState("");
  const [carboG, setCarboG] = useState("");
  const [fatG, setFatG] = useState("");
  const [fiberG, setFiberG] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AdminResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    // Empty optional strings become undefined/null so the backend can validate intent.
    const payload: Record<string, unknown> = {
      food_description: foodDescription,
      food_description_ro: foodDescriptionRo || undefined,
      quantity: quantity ? Number(quantity) : null,
      measure: measure || null,
      wt_g: Number(wtG),
      ener_kcal: Number(enerKcal),
      prot_g: Number(protG),
      carbo_g: Number(carboG),
      fat_g: Number(fatG),
      fiber_g: Number(fiberG),
    };

    if (categoryId) {
      payload.category_id = Number(categoryId);
    } else {
      // If no existing category_id is provided, the backend upserts by name.
      payload.category_name = categoryName;
      payload.category_name_ro = categoryNameRo || undefined;
    }

    if (subcategoryId) {
      payload.subcategory_id = Number(subcategoryId);
    } else {
      // Same pattern for Food groups, which are stored as subcategories in the DB.
      payload.subcategory_name = subcategoryName;
      payload.subcategory_name_ro = subcategoryNameRo || undefined;
    }

    try {
      const response = await fetch(`${API_BASE}/api/admin/foods`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Token": adminToken,
        },
        body: JSON.stringify(payload),
      });

      const data = (await response.json()) as AdminResponse | { detail?: string };
      if (!response.ok) {
        throw new Error((data as { detail?: string }).detail ?? "Request failed");
      }

      setResult(data as AdminResponse);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: 24, maxWidth: 900, fontFamily: "sans-serif" }}>
      <h1>Admin - Add Food</h1>

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 10 }}>
        <label>
          Admin token
          <input
            required
            type="password"
            autoComplete="current-password"
            value={adminToken}
            onChange={(event) => setAdminToken(event.target.value)}
            style={{ display: "block", width: "100%", padding: 8 }}
          />
        </label>

        <fieldset style={{ border: "1px solid #ddd", padding: 12 }}>
          <legend>Category</legend>
          <label>
            category_id (optional)
            <input
              type="number"
              min="1"
              value={categoryId}
              onChange={(event) => setCategoryId(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            category_name (used when category_id missing)
            <input
              value={categoryName}
              onChange={(event) => setCategoryName(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            category_name_ro (optional)
            <input
              value={categoryNameRo}
              onChange={(event) => setCategoryNameRo(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
        </fieldset>

        <fieldset style={{ border: "1px solid #ddd", padding: 12 }}>
          <legend>Food</legend>
          <label>
            subcategory_id (optional)
            <input
              type="number"
              min="1"
              value={subcategoryId}
              onChange={(event) => setSubcategoryId(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            subcategory_name (used when subcategory_id missing)
            <input
              value={subcategoryName}
              onChange={(event) => setSubcategoryName(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            subcategory_name_ro (optional)
            <input
              value={subcategoryNameRo}
              onChange={(event) => setSubcategoryNameRo(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
        </fieldset>

        <fieldset style={{ border: "1px solid #ddd", padding: 12 }}>
          <legend>Food Description</legend>
          <label>
            food_description (EN)
            <input
              required
              value={foodDescription}
              onChange={(event) => setFoodDescription(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            food_description_ro (optional)
            <input
              value={foodDescriptionRo}
              onChange={(event) => setFoodDescriptionRo(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            quantity (optional)
            <input
              type="number"
              min="0"
              step="0.01"
              value={quantity}
              onChange={(event) => setQuantity(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            measure (optional)
            <input
              value={measure}
              onChange={(event) => setMeasure(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            wt_g
            <input
              required
              type="number"
              min="0.01"
              step="0.01"
              value={wtG}
              onChange={(event) => setWtG(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            ener_kcal
            <input
              required
              type="number"
              min="0"
              step="0.01"
              value={enerKcal}
              onChange={(event) => setEnerKcal(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            prot_g
            <input
              required
              type="number"
              min="0"
              step="0.01"
              value={protG}
              onChange={(event) => setProtG(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            carbo_g
            <input
              required
              type="number"
              min="0"
              step="0.01"
              value={carboG}
              onChange={(event) => setCarboG(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            fat_g
            <input
              required
              type="number"
              min="0"
              step="0.01"
              value={fatG}
              onChange={(event) => setFatG(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
          <label>
            fiber_g
            <input
              required
              type="number"
              min="0"
              step="0.01"
              value={fiberG}
              onChange={(event) => setFiberG(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8 }}
            />
          </label>
        </fieldset>

        <button type="submit" disabled={loading} style={{ padding: 10 }}>
          {loading ? "Submitting..." : "Create Food"}
        </button>
      </form>

      {error && <p style={{ color: "crimson", marginTop: 12 }}>{error}</p>}
      {result && (
        <pre
          style={{
            marginTop: 12,
            background: "#f5f5f5",
            border: "1px solid #ddd",
            padding: 12,
            overflowX: "auto",
          }}
        >
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </main>
  );
}
