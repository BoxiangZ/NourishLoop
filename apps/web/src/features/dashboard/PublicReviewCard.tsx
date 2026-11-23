import type { ExternalNoteRead } from "@nourishloop/api-client/schema";
import type { LocalFoodArea } from "@nourishloop/api-client";
import { FOOD_AREAS } from "./foodAreas";

export default function PublicReviewCard({ note }: { note: ExternalNoteRead }) {
  return <article className="nl-source-card nl-local-review-card">
    <div className="nl-local-review-meta">
      <span className="nl-status-pill">{note.source_platform}</span>
      <span>{FOOD_AREAS[note.scope as LocalFoodArea] ?? note.scope}</span>
    </div>
    <h3>{note.title}</h3>
    <p>{note.summary}</p>
    <div className="nl-local-review-links">
      <a href={note.source_url} target="_blank" rel="noreferrer">Read on {note.source_platform} ↗</a>
      <small>Link checked {note.source_checked_at}</small>
    </div>
  </article>;
}
