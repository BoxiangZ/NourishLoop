"use client";

import type { MenuItemRead, RecommendationRead } from "@nourishloop/api-client/schema";

type Props = {
  item: MenuItemRead;
  venue: string;
  busy: boolean;
  onPlan: () => void;
  recommendation?: RecommendationRead;
  featured?: boolean;
};

export default function FoodCard({ item, venue, busy, onPlan, recommendation, featured = false }: Props) {
  return <article className={`nl-food-card ${featured ? "nl-food-card-featured" : ""}`}>
    <div className={`nl-meal-art nl-art-${item.category}`} aria-hidden="true">
      <span className="nl-meal-plate"><i /><b /><em /></span>
      <span className="nl-art-label">{venue}</span>
    </div>
    <div className="nl-food-body">
      {recommendation && <p className="nl-card-kicker">SUGGESTED FOR YOU · #{recommendation.rank}</p>}
      <h3>{item.name}</h3>
      <p className="nl-food-venue">{venue} · {item.category.replaceAll("_", " ")}</p>
      <p className="nl-food-description">{item.description}</p>
      <div className="nl-food-meta">
        <span>≈ {item.nutrition.calories_kcal} kcal</span>
        <span>{item.nutrition.protein_g} g protein</span>
        {item.price_hkd !== null && <span>HK${item.price_hkd}</span>}
      </div>
      {recommendation && <div className="nl-reason">
        <strong>Why this fits</strong><p>{recommendation.explanation}</p>
        <small>{recommendation.confidence} confidence · {recommendation.confidence_reason}</small>
      </div>}
      <button className="nl-button nl-button-primary nl-food-action" disabled={busy} onClick={onPlan}>Plan this meal <span aria-hidden="true">→</span></button>
    </div>
  </article>;
}
