"use client";

import { useEffect, useState } from "react";
import { api } from "@nourishloop/api-client";
import type { ExternalNoteRead, VenueRead } from "@nourishloop/api-client/schema";
import Pager from "./Pager";

const PAGE_SIZE = 6;

export default function PlacesSection() {
  const [scope, setScope] = useState<"hkust" | "lohas">("hkust");
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
      api.externalNotes(scope),
    ]).then(([rows, publicNotes]) => {
      if (!active) return;
      setPlaces(rows.slice(0, PAGE_SIZE)); setHasNext(rows.length > PAGE_SIZE);
      setNotes(publicNotes); setError("");
    }).catch((cause: Error) => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, [scope, page, search]);

  return <>
    <div className="nl-section-heading"><div><span className="nl-eyebrow">VERIFIED DIRECTORY</span>
      <h2>Find a real place</h2></div></div>
    <p className="nl-directory-note">Names and locations are sourced from the official operator listings. Menus, prices and nutrition have not been verified.</p>
    <div className="nl-filter-row" aria-label="Place area">
      <button className="nl-chip" data-active={scope === "hkust"} onClick={() => { setScope("hkust"); setPage(0); }}>HKUST campus</button>
      <button className="nl-chip" data-active={scope === "lohas"} onClick={() => { setScope("lohas"); setPage(0); }}>THE LOHAS · 日出康城</button>
    </div>
    <form className="nl-search" onSubmit={event => { event.preventDefault(); setPage(0); setSearch(draft.trim()); }}>
      <span aria-hidden="true">⌕</span><input aria-label="Search real places" placeholder="Search restaurant or location"
        value={draft} onChange={event => setDraft(event.target.value)} />
      <button>Search</button>
    </form>
    {error && <div role="alert" className="nl-alert">{error}</div>}
    <div className="nl-place-grid">{places.map(place => <article className="nl-place-card" key={place.id}>
      <div className="nl-place-art"><span>{scope === "hkust" ? "HKUST" : "THE LOHAS"}</span><b>⌑</b></div>
      <div className="nl-place-body"><span className="nl-eyebrow">OFFICIAL DIRECTORY · CHECKED {place.source_checked_at}</span>
        <h3>{place.name}</h3><p>{place.campus_area}</p>
        <div className="nl-place-links">
          {place.source_url && <a href={place.source_url} target="_blank" rel="noreferrer">Official listing ↗</a>}
          <a href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${place.name} ${scope === "hkust" ? "HKUST" : "The LOHAS"} Hong Kong`)}`}
            target="_blank" rel="noreferrer">View map & reviews ↗</a>
        </div>
      </div>
    </article>)}</div>
    {!places.length && <div className="nl-empty">No places match this search.</div>}
    <Pager page={page} hasNext={hasNext} onChange={setPage} label="places" />
    <div className="nl-section-heading"><div><span className="nl-eyebrow">PUBLIC CONVERSATIONS</span>
      <h2>Outside perspectives</h2></div></div>
    <p className="nl-directory-note">Short paraphrases of linked Reddit discussions. These are individual opinions, not verified restaurant ratings or NourishLoop posts.</p>
    <div className="nl-source-grid">{notes.map(note => <article className="nl-source-card" key={note.id}>
      <span className="nl-eyebrow">{note.source_platform} · CHECKED {note.source_checked_at}</span>
      <h3>{note.title}</h3><p>{note.summary}</p>
      <a href={note.source_url} target="_blank" rel="noreferrer">Read original discussion ↗</a>
    </article>)}</div>
  </>;
}
