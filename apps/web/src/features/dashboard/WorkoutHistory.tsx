import { useEffect, useState } from "react";
import { api } from "@nourishloop/api-client";
import type { WorkoutSessionRead } from "@nourishloop/api-client/schema";
import Pager from "./Pager";

const PAGE_SIZE = 5;
const localDate = new Intl.DateTimeFormat("en-HK", { dateStyle: "medium", timeZone: "Asia/Hong_Kong" });

export default function WorkoutHistory() {
  const [page, setPage] = useState(0);
  const [sessions, setSessions] = useState<WorkoutSessionRead[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setError(""); setSessions(null);
    api.workoutSessions(PAGE_SIZE + 1, page * PAGE_SIZE)
      .then(rows => { if (active) setSessions(rows); })
      .catch((cause: Error) => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, [page]);

  return <>
    {error && <p role="alert" className="nl-alert">{error}</p>}
    {!sessions && !error && <p role="status">Loading training history…</p>}
    {sessions?.length === 0 && <p className="nl-empty">Completed sessions will appear here after you confirm one.</p>}
    <div className="nl-history-list">{sessions?.slice(0, PAGE_SIZE).map(session =>
      <article className="nl-history-row" key={session.id}>
        <span className="nl-history-icon" aria-hidden="true">↗</span>
        <div><strong className="nl-training-focus">{session.focus} · {session.stage}</strong>
          <small>{localDate.format(new Date(session.completed_at))}</small>
          <small>{session.exercise_names.join(" · ")}</small></div>
        <span className="nl-history-kcal">{session.duration_min} min</span>
      </article>)}</div>
    <Pager page={page} hasNext={(sessions?.length ?? 0) > PAGE_SIZE} onChange={setPage} label="workout history" />
  </>;
}
