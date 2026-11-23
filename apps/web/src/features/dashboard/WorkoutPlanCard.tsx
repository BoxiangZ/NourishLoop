import type { ReactNode } from "react";
import type { WorkoutPlanRead } from "@nourishloop/api-client/schema";
import SourcePhoto from "./SourcePhoto";

export default function WorkoutPlanCard({ plan, compact, children }: {
  plan: WorkoutPlanRead;
  compact?: boolean;
  children: ReactNode;
}) {
  return <section className="nl-plan-card" aria-label="Suggested workout">
    <div className="nl-section-heading"><div>
      <span className="nl-eyebrow">{plan.minutes} MINUTES · {plan.stage}</span>
      <h3>{plan.focus[0].toUpperCase() + plan.focus.slice(1)} session</h3>
    </div></div>
    <p>{plan.explanation}</p>
    {compact ? <p>{plan.exercises.map(row => row.exercise.name).join(" · ")}</p> :
      <div className="nl-plan-exercises">{plan.exercises.map(row => <article key={row.exercise.id}>
        {row.exercise.source_photo && <SourcePhoto photo={row.exercise.source_photo} variant="workout" />}
        <div><strong>{row.exercise.name}</strong>
          <small>{row.sets} sets · {row.reps} · {row.rest_seconds}s rest</small>
          <small>Equipment · {row.exercise.equipment_detail ?? row.exercise.equipment}</small>
          <p>{row.exercise.instructions}</p></div>
        <a href={row.exercise.source_url} target="_blank" rel="noreferrer">ACE guide ↗</a>
      </article>)}</div>}
    {children}
  </section>;
}
