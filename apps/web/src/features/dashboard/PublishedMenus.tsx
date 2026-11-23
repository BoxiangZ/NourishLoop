"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type LocalFoodArea } from "@nourishloop/api-client";
import type { MenuLocationRead, PublishedDishRead, VenueRead } from "@nourishloop/api-client/schema";
import { FOOD_AREAS } from "./foodAreas";
import Pager from "./Pager";
import SourcePhoto from "./SourcePhoto";
import useNearbyMenuLocations from "./useNearbyMenuLocations";

const PAGE_SIZE = 6;
const AREA_KEYS = Object.keys(FOOD_AREAS) as LocalFoodArea[];
const MAP_SEARCH = "https://www.google.com/maps/search/?api=1&query=restaurants%20in%20shopping%20malls%20near%20me";

export default function PublishedMenus({ venue }: { venue: VenueRead | null }) {
  const [scope, setScope] = useState<LocalFoodArea>(
    AREA_KEYS.find(area => area === venue?.scope) ?? "hkust",
  );
  const [selectedVenue, setSelectedVenue] = useState(venue);
  const [selectedLocation, setSelectedLocation] = useState<MenuLocationRead | null>(null);
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [rows, setRows] = useState<PublishedDishRead[] | null>(null);
  const [error, setError] = useState("");
  const selectLocation = useCallback((place: MenuLocationRead) => {
    setScope(place.scope); setSelectedVenue(null); setSelectedLocation(place); setPage(0);
  }, []);
  const { result: nearby, locate, stopLocating } = useNearbyMenuLocations(selectLocation, !venue);

  useEffect(() => {
    let active = true;
    setRows(null); setError("");
    api.publishedDishes({ scope, q: query, limit: PAGE_SIZE + 1,
      offset: page * PAGE_SIZE, venueId: selectedVenue?.id, locationId: selectedLocation?.id })
      .then(value => { if (active) { setRows(value); setError(""); } })
      .catch((cause: Error) => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, [scope, query, page, selectedVenue, selectedLocation]);

  function browseArea(area: LocalFoodArea) {
    stopLocating();
    setScope(area); setSelectedVenue(null); setSelectedLocation(null); setPage(0);
  }

  return <section aria-label="Published restaurant menus">
    <div className="nl-section-heading nl-menu-heading"><h2>Browse real menus</h2>
      <button type="button" className="nl-button nl-button-soft" onClick={locate}
        disabled={nearby.status === "locating"}>
        {nearby.status === "locating" ? "Finding nearby menus…" : "Find food near me"}
      </button>
    </div>
    <p className="nl-directory-note">Public menus and product photos. Check with the branch for current prices and availability.</p>
    {(nearby.status === "outside" || nearby.status === "error") && <div className="nl-nearby" role="status">
      <p>{nearby.status === "error" ? nearby.message : "No published menus within 5 km of your location."}</p>
      <a className="nl-text-link" href={MAP_SEARCH} target="_blank" rel="noreferrer">Search nearby food on Google Maps ↗</a>
    </div>}
    {nearby.status === "ready" && <section className="nl-nearby" aria-label="Nearby menu locations">
      <h3>Nearby malls and food locations</h3>
      <div className="nl-filter-row">{nearby.places.map(place =>
        <button type="button" key={place.id} className="nl-chip" aria-pressed={selectedLocation?.id === place.id}
          data-active={selectedLocation?.id === place.id} onClick={() => selectLocation(place)}>
          {place.name} · {place.distanceKm < 0.1 ? "<100 m" : `${place.distanceKm.toFixed(1)} km`}
        </button>)}</div>
      <p>Approximate straight-line distance · <a href="https://www.openstreetmap.org/copyright"
        target="_blank" rel="noreferrer">© OpenStreetMap contributors</a></p>
    </section>}
    <div className="nl-filter-row" aria-label="Menu area">{AREA_KEYS.map(area =>
      <button className="nl-chip" key={area} data-active={scope === area}
        onClick={() => browseArea(area)}>{FOOD_AREAS[area]}</button>)}</div>
    {(selectedLocation || selectedVenue) && <p className="nl-menu-selection">
      <strong>{selectedLocation?.name ?? selectedVenue?.name}</strong>
      {selectedLocation && <a href={selectedLocation.source_url} target="_blank" rel="noreferrer">View map ↗</a>}
      <button type="button" className="nl-text-link" onClick={() => browseArea(scope)}>Show all in area</button>
    </p>}
    <form className="nl-search" onSubmit={event => { event.preventDefault(); setPage(0); setQuery(draft.trim()); }}>
      <span aria-hidden="true">⌕</span><input aria-label="Search real menus" value={draft}
        placeholder="Search dish, restaurant or mall" onChange={event => setDraft(event.target.value)} />
      <button>Search</button>
    </form>
    {error && <div role="alert" className="nl-alert">{error}</div>}
    {!rows && !error && <p role="status">Loading published menus…</p>}
    <div className="nl-place-grid">{rows?.slice(0, PAGE_SIZE).map(dish =>
      <article key={dish.id} className="nl-place-card">
        {dish.source_photo && <SourcePhoto photo={dish.source_photo} />}
        <div className="nl-place-body">
        <span className="nl-eyebrow">{dish.source_scope === "branch" ? "BRANCH SOURCE" : "BRAND MENU"}</span>
        <h3>{dish.name}</h3><p>{dish.venue.name} · {dish.venue.campus_area}</p>
        {dish.price_hkd !== null && <p><strong>Reference price · HK${dish.price_hkd}</strong></p>}
        <p>{dish.reference_note}</p>
        <div className="nl-place-links">
          <a href={dish.source_url} target="_blank" rel="noreferrer">View source ↗</a>
          {dish.venue.source_url && <a href={dish.venue.source_url} target="_blank" rel="noreferrer">View place ↗</a>}
        </div>
        <small>Source checked {dish.source_checked_at}</small>
      </div></article>)}</div>
    {rows?.length === 0 && !error && <div className="nl-empty">No sourced menu entries match.
      {selectedVenue?.source_url && <> <a href={selectedVenue.source_url} target="_blank" rel="noreferrer">Check the place listing ↗</a></>}
    </div>}
    <Pager page={page} hasNext={(rows?.length ?? 0) > PAGE_SIZE} onChange={setPage} label="real menus" />
  </section>;
}
