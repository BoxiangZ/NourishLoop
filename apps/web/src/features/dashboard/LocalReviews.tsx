"use client";

import { useEffect, useState } from "react";
import { api, type LocalFoodArea } from "@nourishloop/api-client";
import type { ExternalNoteRead } from "@nourishloop/api-client/schema";
import { FOOD_AREAS } from "./foodAreas";
import Pager from "./Pager";
import PublicReviewCard from "./PublicReviewCard";

const PAGE_SIZE = 6;
const REVIEW_AREAS = ["all", ...(Object.keys(FOOD_AREAS) as LocalFoodArea[])] as const;

export default function LocalReviews() {
  const [scope, setScope] = useState<LocalFoodArea | "all">("all");
  const [page, setPage] = useState(0);
  const [notes, setNotes] = useState<ExternalNoteRead[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setNotes(null); setError("");
    api.externalNotes(scope, PAGE_SIZE + 1, page * PAGE_SIZE)
      .then(rows => { if (active) setNotes(rows); })
      .catch((cause: Error) => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, [scope, page]);

  return <section id="local-reviews" role="tabpanel" aria-labelledby="local-reviews-tab">
    <p className="nl-directory-note">Public dining reviews and neighbourhood food discussions from Reddit and OpenRice.</p>
    <div className="nl-filter-row" aria-label="Review area">{REVIEW_AREAS.map(area =>
      <button key={area} className="nl-chip" data-active={scope === area} aria-pressed={scope === area}
        onClick={() => { setScope(area); setPage(0); }}>
        {area === "all" ? "All areas" : FOOD_AREAS[area]}
      </button>)}</div>
    {error && <div role="alert" className="nl-alert">{error}</div>}
    {notes === null && !error && <p role="status">Loading local reviews…</p>}
    {notes?.length === 0 && <p className="nl-empty">No public reviews added for this area yet.</p>}
    <div className="nl-source-grid">{notes?.slice(0, PAGE_SIZE).map(note =>
      <PublicReviewCard key={note.id} note={note} />)}</div>
    <Pager page={page} hasNext={(notes?.length ?? 0) > PAGE_SIZE} onChange={setPage} label="reviews" />
  </section>;
}
