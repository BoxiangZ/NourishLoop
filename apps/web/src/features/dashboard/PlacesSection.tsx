"use client";

import { useEffect, useState } from "react";
import { api, type LocalFoodArea } from "@nourishloop/api-client";
import type { ExternalNoteRead, VenueRead } from "@nourishloop/api-client/schema";
import Pager from "./Pager";
import { FOOD_AREAS } from "./foodAreas";
import PublicReviewCard from "./PublicReviewCard";

const PAGE_SIZE = 6;

export default function PlacesSection({ onViewMenu }: { onViewMenu: (place: VenueRead) => void }) {
  const [scope, setScope] = useState<LocalFoodArea>("hkust");
  const [page, setPage] = useState(0);
  const [draft, setDraft] = useState("");
  const [search, setSearch] = useState("");
  const [places, setPlaces] = useState<VenueRead[]>([]);
  const [notes, setNotes] = useState<ExternalNoteRead[]>([]);
  const [hasNext, setHasNext] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      api.venues({ scope, limit: PAGE_SIZE + 1, offset: page * PAGE_SIZE, q: search }),
      api.externalNotes(scope, 4),
    ]).then(([rows, publicNotes]) => {
      if (!active) return;
      setPlaces(rows.slice(0, PAGE_SIZE)); setHasNext(rows.length > PAGE_SIZE);
      setNotes(publicNotes); setError("");
    }).catch((cause: Error) => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, [scope, page, search]);

  return <>
    <div className="nl-section-heading"><h2>Find a real place</h2></div>
    <p className="nl-directory-note">Use the linked listings for branch locations. Check Real menus for sourced dishes and reference prices.</p>
    <div className="nl-filter-row" aria-label="Place area">
      {(Object.keys(FOOD_AREAS) as LocalFoodArea[]).map(area =>
        <button key={area} className="nl-chip" data-active={scope === area}
          onClick={() => { setScope(area); setPage(0); }}>{FOOD_AREAS[area]}</button>)}
    </div>
    <form className="nl-search" onSubmit={event => { event.preventDefault(); setPage(0); setSearch(draft.trim()); }}>
      <span aria-hidden="true">⌕</span><input aria-label="Search real places" placeholder="Search restaurant or location"
        value={draft} onChange={event => setDraft(event.target.value)} />
      <button>Search</button>
    </form>
    {error && <div role="alert" className="nl-alert">{error}</div>}
    <div className="nl-place-grid">{places.map(place => <article className="nl-place-card" key={place.id}>
      <div className="nl-place-art"><span>{FOOD_AREAS[scope]}</span><b>⌑</b></div>
      <div className="nl-place-body"><span className="nl-eyebrow">LISTING CHECKED {place.source_checked_at}</span>
        <h3>{place.name}</h3><p>{place.campus_area}</p>
        <div className="nl-place-links">
          <button className="nl-text-link" onClick={() => onViewMenu(place)}>Find menu items</button>
          {place.source_url && <a href={place.source_url} target="_blank" rel="noreferrer">View listing ↗</a>}
          <a href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${place.name} ${place.campus_area} ${FOOD_AREAS[scope]} Hong Kong`)}`}
            target="_blank" rel="noreferrer">View map & reviews ↗</a>
        </div>
      </div>
    </article>)}</div>
    {!places.length && <div className="nl-empty">No places match this search.</div>}
    <Pager page={page} hasNext={hasNext} onChange={setPage} label="places" />
    {notes.length > 0 && <><div className="nl-section-heading"><div><span className="nl-eyebrow">PUBLIC CONVERSATIONS</span>
      <h2>Outside perspectives</h2></div></div>
    <p className="nl-directory-note">Summaries of public dining experiences from Reddit and OpenRice.</p>
    <div className="nl-source-grid">{notes.map(note =>
      <PublicReviewCard key={note.id} note={note} />)}</div></>}
  </>;
}
