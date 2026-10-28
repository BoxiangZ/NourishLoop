"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { api } from "@nourishloop/api-client";
import type { PhotoMealRead } from "@nourishloop/api-client/schema";

type Props = { onCompleted: () => Promise<void> };

export default function MealCheckinCard({ onCompleted }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [record, setRecord] = useState<PhotoMealRead | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!file) { setPreview(null); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  useEffect(() => {
    if (!record || !["pending", "processing"].includes(record.review_status ?? "not_requested")) return;
    let cancelled = false;
    const timer = window.setInterval(() => {
      api.photoReview(record.id).then(next => {
        if (cancelled) return;
        setRecord(next);
        if (next.review_status === "completed") void onCompleted();
      }).catch(cause => { if (!cancelled) setError(cause instanceof Error ? cause.message : "Could not check photo status"); });
    }, 2000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [record, onCompleted]);

  function choose(selected?: File) {
    setRecord(null); setError(null);
    if (!selected) { setFile(null); return; }
    if (!["image/jpeg", "image/png", "image/webp"].includes(selected.type)) {
      setFile(null); setError("Choose a JPEG, PNG or WebP image."); return;
    }
    if (selected.size > 8 * 1024 * 1024) {
      setFile(null); setError("Choose an image smaller than 8 MB."); return;
    }
    setFile(selected);
  }

  async function submit() {
    if (!file) return;
    setBusy(true); setError(null);
    try { setRecord(await api.startPhotoReview(file, notes)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Photo upload failed"); }
    finally { setBusy(false); }
  }

  async function retry() {
    if (!record) return;
    setBusy(true); setError(null);
    try { setRecord(await api.retryPhotoReview(record.id)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not retry the review"); }
    finally { setBusy(false); }
  }

  async function remove() {
    if (!record) return;
    setBusy(true); setError(null);
    try { await api.deletePhotoReview(record.id); setRecord(null); setFile(null); await onCompleted(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not remove the photo"); }
    finally { setBusy(false); }
  }

  const source = record?.nutrition;
  const ai = record?.ai_review;
  return <section className="nl-photo-card" aria-label="Background photo review">
    <div className="nl-photo-copy"><span className="nl-eyebrow">PHOTO / AI CHECK-IN</span>
      <h2>Check in a meal</h2>
      <p>Upload once. We identify the meal in the background, estimate nutrition, and save the result to History automatically.</p>
      <p className="nl-photo-privacy">The photo is stored temporarily while it is processed or waiting for a retry, and sent to the configured OpenRouter vision provider. It is deleted after a successful review. Avoid faces or private details.</p>
      <label className="nl-field-label">Anything we should know? (optional)
        <input value={notes} maxLength={500} onChange={event => setNotes(event.target.value)} placeholder="e.g. half portion, sauce on the side" />
      </label>
      <div className="nl-photo-actions">
        <label className="nl-photo-picker">Take a photo<input aria-label="Take check-in photo" type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={event => choose(event.target.files?.[0])} /></label>
        <label className="nl-photo-picker">Upload a photo<input aria-label="Check-in photo" type="file" accept="image/jpeg,image/png,image/webp" onChange={event => choose(event.target.files?.[0])} /></label>
      </div>
      <button className="nl-button nl-button-primary" disabled={!file || busy || !!record} onClick={() => void submit()}>{busy ? "Uploading…" : "Check in this meal"}</button>
    </div>
    <div className="nl-photo-panel">{preview ? <Image src={preview} alt="Selected meal preview" width={500} height={310} unoptimized /> :
      <div className="nl-photo-empty"><span>◒</span><strong>Your photo preview</strong><small>JPEG · PNG · WebP · up to 8 MB</small></div>}</div>
    {error && <p className="nl-photo-error" role="alert">{error}</p>}
    {record && <div className="nl-photo-result" aria-live="polite"><span className="nl-eyebrow">PHOTO REVIEW</span>
      <h3>{record.review_status === "completed" ? "Your meal result" : record.review_status === "failed" ? "Review needs another try" : "Review in progress"}</h3>
      <p>Attempt {record.review_attempts} of 3 · {record.review_status}</p>
      {record.review_status === "failed" && <><p>{record.review_error}</p><div className="nl-photo-actions"><button className="nl-button nl-button-soft" disabled={busy || (record.review_attempts ?? 0) >= 3} onClick={() => void retry()}>Retry review</button><button className="nl-text-link" disabled={busy} onClick={() => void remove()}>Remove photo</button></div></>}
      {record.review_status === "completed" && <>
        <p>{record.foods.map(food => food.name).join(", ")}</p>
        {source && <div className="nl-nutrition-estimate"><strong>{record.nutrition_status === "partial" ? "Matched foods only · " : "Approx. "}{source.calories_kcal} kcal · USDA</strong><span>Protein {source.protein_g} g · Carbs {source.carbs_g} g · Fat {source.fat_g} g</span>
          {(record.nutrition_items ?? []).map(item => <a key={`${item.fdc_id}-${item.name}`} href={item.source_url} target="_blank" rel="noreferrer">{item.name}: {item.grams} g · USDA {item.fdc_id} ↗</a>)}
        </div>}
        {ai?.estimated_nutrition && <div className="nl-nutrition-estimate"><strong>AI visual estimate · approx. {ai.estimated_nutrition.calories_kcal} kcal</strong><span>Protein {ai.estimated_nutrition.protein_g} g · Carbs {ai.estimated_nutrition.carbs_g} g · Fat {ai.estimated_nutrition.fat_g} g</span><p>{ai.summary} Model confidence {Math.round(ai.confidence * 100)}% (uncalibrated). AI estimates are not counted in daily totals.</p>{(ai.assumptions ?? []).map((item, index) => <small key={index}>{item}</small>)}{(ai.suggestions ?? []).map((item, index) => <small key={`tip-${index}`}>Tip: {item}</small>)}</div>}
        {(record.unresolved_foods?.length ?? 0) > 0 && <p>Not included in source totals: {record.unresolved_foods?.join("; ")}</p>}
        <p>Saved to History. You can use the instant photo flow to adjust a result.</p>
      </>}
    </div>}
  </section>;
}
