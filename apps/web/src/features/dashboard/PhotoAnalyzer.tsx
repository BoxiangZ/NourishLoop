"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { api } from "@nourishloop/api-client";
import type {
  NutritionFoodRead, PhotoAnalysisRead, PhotoFood, PhotoNutritionEstimateRead,
  PhotoNutritionSelection,
} from "@nourishloop/api-client/schema";

const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];

async function imageForAnalysis(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file);
  try {
    const scale = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const context = canvas.getContext("2d");
    if (!context) throw new Error("This browser cannot prepare the photo");
    context.fillStyle = "white";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    // Canvas re-encoding drops camera metadata before the image leaves the browser.
    const encoded = canvas.toDataURL("image/jpeg", 0.82).split(",")[1];
    if (!encoded || encoded.length > 7_000_000) throw new Error("The prepared photo is too large");
    return encoded;
  } finally {
    bitmap.close();
  }
}

type Props = {
  onConfirmed: () => Promise<void>;
};

export default function PhotoAnalyzer({ onConfirmed }: Props) {
  const analysisRun = useRef(0);
  const resultRef = useRef<HTMLDivElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [analysis, setAnalysis] = useState<PhotoAnalysisRead | null>(null);
  const [foods, setFoods] = useState<PhotoFood[]>([]);
  const [queries, setQueries] = useState<Record<number, string>>({});
  const [matches, setMatches] = useState<Record<number, NutritionFoodRead[]>>({});
  const [selected, setSelected] = useState<Record<number, {
    fdcId: number; grams: string; portionBasis?: PhotoNutritionSelection["portion_basis"];
  }>>({});
  const [estimate, setEstimate] = useState<PhotoNutritionEstimateRead | null>(null);
  const [partialEstimate, setPartialEstimate] = useState<PhotoNutritionEstimateRead | null>(null);
  const [adjusting, setAdjusting] = useState(false);
  const [unresolved, setUnresolved] = useState<string[]>([]);
  const [searchingIndex, setSearchingIndex] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!file) { setPreview(null); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  useEffect(() => {
    if (analysis && !busy) resultRef.current?.scrollIntoView?.({ behavior: "smooth", block: "start" });
  }, [analysis, busy]);

  function selectFile(selected?: File) {
    ++analysisRun.current;
    setAnalysis(null); setFoods([]); setError(null);
    setQueries({}); setMatches({}); setSelected({}); setEstimate(null); setPartialEstimate(null);
    setAdjusting(false); setUnresolved([]);
    setBusy(false);
    if (!selected) { setFile(null); return; }
    if (!ACCEPTED.includes(selected.type)) {
      setFile(null); setError("Choose a JPEG, PNG or WebP image."); return;
    }
    if (selected.size > 5_000_000) {
      setFile(null); setError("Choose an image smaller than 5 MB."); return;
    }
    setFile(selected);
  }

  async function analyze(selectedFile: File, requestNotes: string, run: number) {
    setBusy(true); setError(null); setAnalysis(null);
    try {
      const image_base64 = await imageForAnalysis(selectedFile);
      const result = await api.analyzePhoto({ image_base64, mime_type: "image/jpeg", notes: requestNotes });
      if (run !== analysisRun.current) return;
      setFoods(result.foods);
      setQueries(Object.fromEntries(result.foods.map((food, index) =>
        [index, `${food.name} ${food.preparation ?? ""}`.trim()])));
      setMatches({}); setSelected({}); setEstimate(null); setPartialEstimate(null);
      if (result.foods.length) {
        try {
          const automatic = await api.autoEstimatePhotoNutrition({ foods: result.foods });
          if (run !== analysisRun.current) return;
          setMatches(Object.fromEntries((automatic.matches ?? []).flatMap(item => item.match
            ? [[item.food_index, [item.match]]] : [])));
          const foundSelections = Object.fromEntries((automatic.matches ?? []).flatMap(item => item.match
            ? [[item.food_index, { fdcId: item.match.fdc_id, grams: "", portionBasis: "user_adjusted" as const }]]
            : []));
          setSelected({ ...foundSelections, ...Object.fromEntries((automatic.selections ?? []).map(item => [item.food_index,
            { fdcId: item.fdc_id, grams: String(item.grams), portionBasis: item.portion_basis }])) });
          setEstimate(automatic.estimate ?? null);
          setPartialEstimate(automatic.partial_estimate ?? null);
          setUnresolved(automatic.unresolved ?? []);
        } catch {
          if (run !== analysisRun.current) return;
          setUnresolved(["Automatic nutrition lookup is unavailable. You can adjust details or save the food record."]);
        }
      }
      if (run === analysisRun.current) setAnalysis(result);
    } catch (cause) {
      if (run === analysisRun.current) {
        setError(cause instanceof Error ? cause.message : "Photo analysis failed");
      }
    } finally { if (run === analysisRun.current) setBusy(false); }
  }

  function retryAnalysis() {
    if (!file || busy) return;
    const run = ++analysisRun.current;
    setAdjusting(false); setUnresolved([]);
    void analyze(file, notes, run);
  }

  function removeFood(index: number) {
    const shift = <T,>(entries: Record<number, T>): Record<number, T> => Object.fromEntries(
      Object.entries(entries).flatMap(([key, value]) => {
        const position = Number(key);
        return position === index ? [] : [[position > index ? position - 1 : position, value]];
      }),
    );
    setFoods(current => current.filter((_, position) => position !== index));
    setQueries(current => shift(current));
    setMatches(current => shift(current));
    setSelected(current => shift(current));
    setEstimate(null); setPartialEstimate(null);
  }

  function updateFood(index: number, key: keyof PhotoFood, value: string) {
    setFoods(current => current.map((food, position) => position === index
      ? { ...food, [key]: key === "name" ? value : value || null } : food));
    if (key === "name" || key === "preparation") {
      setQueries(current => ({ ...current, [index]: value }));
      setMatches(current => ({ ...current, [index]: [] }));
      setSelected(current => { const next = { ...current }; delete next[index]; return next; });
      setEstimate(null); setPartialEstimate(null);
    }
  }

  function nutritionSelections(): PhotoNutritionSelection[] {
    return foods.flatMap((_, index) => {
      const entry = selected[index];
      const grams = Number(entry?.grams);
      return entry?.fdcId && Number.isFinite(grams) && grams > 0 && grams <= 5000
        ? [{ food_index: index, fdc_id: entry.fdcId, grams,
          portion_basis: entry.portionBasis ?? "user_adjusted" }] : [];
    });
  }

  async function findNutrition(index: number) {
    const query = queries[index]?.trim();
    if (!query || query.length < 2) { setError("Enter at least two letters to search USDA foods."); return; }
    setSearchingIndex(index); setError(null);
    try {
      const found = await api.nutritionFoods(query);
      setMatches(current => ({ ...current, [index]: found }));
      setSelected(current => { const next = { ...current }; delete next[index]; return next; });
      setEstimate(null); setPartialEstimate(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "USDA search failed");
    } finally { setSearchingIndex(null); }
  }

  async function previewNutrition() {
    const nutrition_selections = nutritionSelections();
    if (nutrition_selections.length !== foods.length) return;
    setBusy(true); setError(null);
    try {
      setEstimate(await api.estimatePhotoNutrition({ foods, nutrition_selections }));
      setPartialEstimate(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Nutrition preview failed");
    } finally { setBusy(false); }
  }

  async function confirm() {
    if (!analysis || !foods.some(food => food.name.trim()) ||
        !(estimate || partialEstimate || analysis.ai_review?.estimated_nutrition)) return;
    setBusy(true); setError(null);
    try {
      await api.recordPhotoMeal({
        foods: foods.map(food => ({
          name: food.name.trim(), preparation: food.preparation?.trim() || null,
          quantity_from_notes: food.quantity_from_notes?.trim() || null,
          estimated_grams: food.estimated_grams ?? null,
          portion_basis: food.portion_basis,
        })),
        notes, model: analysis.model,
        nutrition_selections: estimate || partialEstimate ? nutritionSelections() : [],
        ai_review: analysis.ai_review ?? null,
      });
      setFile(null); setAnalysis(null); setFoods([]); setNotes("");
      setQueries({}); setMatches({}); setSelected({}); setEstimate(null); setPartialEstimate(null);
      setAdjusting(false); setUnresolved([]);
      await onConfirmed();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not save the meal");
    } finally { setBusy(false); }
  }

  const visibleEstimate = estimate ?? partialEstimate;
  const visualEstimate = analysis?.ai_review?.estimated_nutrition;
  const hasNutrition = !!(visibleEstimate || visualEstimate);

  return <section className="nl-photo-card" aria-label="Food photo recognition">
    <div className="nl-photo-copy"><span className="nl-eyebrow">PHOTO / REMEMBER</span>
      <h2>What&apos;s on your plate?</h2>
      <p>Take or upload a food photo, then tap Recognize food to see the nutrition result.</p>
      <p className="nl-photo-privacy">When you tap Recognize food, your photo goes to the configured OpenRouter vision provider. NourishLoop does not store the photo. Avoid faces or private details.</p>
      <label className="nl-field-label">Anything the photo might miss? (optional)
        <input value={notes} maxLength={500} onChange={event => setNotes(event.target.value)}
          placeholder="e.g. half a bowl, tofu under the rice" />
      </label>
      <div className="nl-photo-actions">
        <label className="nl-photo-picker">Take a photo
          <input aria-label="Take food photo" type="file" accept="image/jpeg,image/png,image/webp"
            capture="environment" onChange={event => selectFile(event.target.files?.[0])} />
        </label>
        <label className="nl-photo-picker">Upload a photo
          <input aria-label="Food photo" type="file" accept="image/jpeg,image/png,image/webp"
            onChange={event => selectFile(event.target.files?.[0])} />
        </label>
      </div>
      <button type="button" className="nl-button nl-button-primary" disabled={!file || busy}
        onClick={retryAnalysis}>{busy ? "Recognizing food and nutrition…" :
          analysis ? "Recognize again" : "Recognize food"}</button>
    </div>
    <div className="nl-photo-panel">
      {preview ? <Image src={preview} alt="Selected food photo preview" width={500} height={310} unoptimized /> :
        <div className="nl-photo-empty" aria-hidden="true"><span>◒</span><strong>Your photo preview</strong><small>JPEG · PNG · WebP · up to 5 MB</small></div>}
    </div>
    {error && <p role="alert" className="nl-photo-error">{error}</p>}
    {busy && <p role="status" className="nl-photo-result">Identifying food and calculating nutrition…</p>}
    {analysis && !busy && <div ref={resultRef} className="nl-photo-result" aria-live="polite"><span className="nl-eyebrow">YOUR PHOTO RESULT</span>
      <h3>{estimate ? "Nutrition estimate" : partialEstimate ? "Known foods · partial nutrition" :
        visualEstimate ? "AI visual nutrition estimate" :
        foods.length ? "Foods identified" : "No food found"}</h3>
      <p>{estimate ? "Your result is ready. You can save it to History or adjust it below." :
        partialEstimate ? "This USDA total covers only matched foods. The AI estimate below covers the visible meal." :
        visualEstimate ? "A visual estimate is ready. You can save it to History or adjust the food details." :
          "Nutrition could not be estimated for this photo. Retry recognition or adjust the foods before saving."}</p>
      {visibleEstimate && <div className="nl-nutrition-estimate" role="status">
        <strong>{estimate ? "Approx." : "Matched foods only · approx."} {visibleEstimate.nutrition.calories_kcal} kcal</strong>
        <span>Protein {visibleEstimate.nutrition.protein_g} g · Carbs {visibleEstimate.nutrition.carbs_g} g · Fat {visibleEstimate.nutrition.fat_g} g</span>
        <p>{visibleEstimate.uncertainty_note}</p>
        {visibleEstimate.items.map(item => <a key={item.fdc_id + item.name} href={item.source_url} target="_blank" rel="noreferrer">
          {item.name}: about {item.grams} g of {item.source_description} ({item.portion_basis === "visual_estimate" ? "photo estimate" : "reviewed portion"}) ↗</a>)}
      </div>}
      {visualEstimate && <div className="nl-nutrition-estimate" role="status">
        <strong>AI visual estimate · approx. {visualEstimate.calories_kcal} kcal</strong>
        <span>Protein {visualEstimate.protein_g} g · Carbs {visualEstimate.carbs_g} g · Fat {visualEstimate.fat_g} g</span>
        <p>{analysis.ai_review?.summary} This is an unverified visual estimate and is not included in daily nutrition totals.</p>
        {(analysis.ai_review?.assumptions ?? []).map((item, index) => <small key={index}>{item}</small>)}
      </div>}
      {foods.map((food, index) => <p key={index}><strong>{food.name}</strong>{food.preparation ? ` · ${food.preparation}` : ""}
        {selected[index]?.grams ? ` · about ${selected[index].grams} g` : " · portion unclear"}</p>)}
      {unresolved.length > 0 && <p role="status">{unresolved.join("; ")}</p>}
      {foods.length > 0 && <button type="button" className="nl-button nl-button-soft" onClick={() => setAdjusting(current => !current)}>
        {adjusting ? "Hide details" : "Adjust foods and portions"}</button>
      }
      {adjusting && foods.map((food, index) => <div className="nl-photo-food" key={index}>
        <label>Food name<input aria-label={`Food ${index + 1} name`} value={food.name}
          onChange={event => updateFood(index, "name", event.target.value)} /></label>
        <label>Preparation<input aria-label={`Food ${index + 1} preparation`} value={food.preparation ?? ""}
          onChange={event => updateFood(index, "preparation", event.target.value)} /></label>
        <label>Quantity from your notes<input aria-label={`Food ${index + 1} quantity`} value={food.quantity_from_notes ?? ""}
          onChange={event => updateFood(index, "quantity_from_notes", event.target.value)} /></label>
        <button type="button" className="nl-text-link" onClick={() => removeFood(index)}>Remove</button>
        <div className="nl-nutrition-match">
          <label>Search USDA food (English)
            <input aria-label={`USDA search ${index + 1}`} value={queries[index] ?? ""}
              onChange={event => setQueries(current => ({ ...current, [index]: event.target.value }))}
              placeholder="e.g. egg whole cooked fried" /></label>
          <button type="button" className="nl-button nl-button-soft" disabled={searchingIndex !== null || busy}
            onClick={() => void findNutrition(index)}>{searchingIndex === index ? "Searching…" : "Find match"}</button>
          {matches[index] && (matches[index].length ? <>
            <label>USDA entry
              <select aria-label={`USDA match ${index + 1}`} value={selected[index]?.fdcId ?? ""}
                onChange={event => {
                  setSelected(current => ({ ...current, [index]: {
                    fdcId: Number(event.target.value), grams: current[index]?.grams ?? "",
                    portionBasis: "user_adjusted",
                  } })); setEstimate(null); setPartialEstimate(null);
                }}>
                <option value="">Select the correct food and preparation</option>
                {matches[index].map(match => <option key={match.fdc_id} value={match.fdc_id}>
                  {match.description} · {match.calories_kcal} kcal/100 g
                </option>)}
              </select></label>
            <label>Edible grams you ate
              <input aria-label={`Food ${index + 1} grams`} type="number" min="1" max="5000" step="1"
                value={selected[index]?.grams ?? ""} placeholder="e.g. 150"
                onChange={event => {
                  setSelected(current => ({ ...current, [index]: {
                    fdcId: current[index]?.fdcId ?? 0, grams: event.target.value,
                    portionBasis: "user_adjusted",
                  } })); setEstimate(null); setPartialEstimate(null);
                }} /></label>
          </> : <p>No complete USDA match found. Try a more specific English term or save without nutrition.</p>)}
        </div>
      </div>)}
      {adjusting && analysis.review_questions.length > 0 && <ul className="nl-photo-questions">
        {analysis.review_questions.map((question, index) => <li key={index}>{question}</li>)}
      </ul>}
      {adjusting && <div className="nl-photo-actions"><button type="button" className="nl-button nl-button-soft"
        onClick={() => { setFoods(current => [...current, { name: "", preparation: null, quantity_from_notes: null }]); setEstimate(null); setPartialEstimate(null); }}>Add food</button>
        <button type="button" className="nl-button nl-button-soft" disabled={busy || !foods.length || nutritionSelections().length !== foods.length}
          onClick={() => void previewNutrition()}>{busy ? "Calculating…" : "Recalculate nutrition"}</button></div>}
      {foods.length > 0 && <div className="nl-photo-actions">
        <button type="button" className="nl-button nl-button-primary"
          disabled={busy || !hasNutrition || !foods.every(food => food.name.trim())}
          onClick={() => void confirm()}>{busy ? "Saving…" :
            estimate ? "Save result to History" : partialEstimate
              ? "Save partial estimate to History" : visualEstimate ? "Save AI estimate to History" : "Nutrition unavailable"}</button>
      </div>}
    </div>}
  </section>;
}
