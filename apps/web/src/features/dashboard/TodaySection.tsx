"use client";

import { useEffect, useState } from "react";
import { api } from "@nourishloop/api-client";
import type { DailySummary, WorkoutSessionRead } from "@nourishloop/api-client/schema";
import type { Screen } from "./AppShell";
import { todayFocus } from "./todayFocus";

type Props = {
  onNavigate: (screen: Screen) => void;
  onAction: (screen: Screen) => void;
};

function hongKongDate(value: string | Date): string {
  return new Date(value).toLocaleDateString("en-CA", { timeZone: "Asia/Hong_Kong" });
}

export default function TodaySection({ onNavigate, onAction }: Props) {
  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [sessions, setSessions] = useState<WorkoutSessionRead[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([api.summary(), api.workoutSessions(100, 0)])
      .then(([nextSummary, nextSessions]) => {
        if (!active) return;
        setSummary(nextSummary);
        setSessions(nextSessions);
      })
      .catch((cause: Error) => {
        if (active) setError(cause.message);
      });
    return () => { active = false; };
  }, []);

  const today = hongKongDate(new Date());
  const workoutMinutes = sessions
    .filter(session => hongKongDate(session.completed_at) === today)
    .reduce((sum, session) => sum + session.duration_min, 0);
  const focus = todayFocus({ mealCount: summary?.meal_count ?? 0, workoutMinutes });
  const actionLabel = focus.action === "workouts" ? "Log a workout" : focus.action === "history"
    ? "Review today" : "Find a meal";

  if (error) return <div role="alert" className="nl-alert">{error}</div>;

  return <section className="nl-today-focus">
    <div className="nl-page-intro"><span className="nl-eyebrow">TODAY / CHECK-IN</span>
      <h1>Your day, at a glance<span className="nl-orange-dot">.</span></h1>
      <p>One factual check-in for food and movement. No calorie or nutrition claims today.</p></div>
    <div className="nl-today-card">
      <p className="nl-today-headline">{focus.headline}</p>
      <div className="nl-today-actions">
        <button className="nl-button nl-button-primary" onClick={() => onAction(focus.action)}>{actionLabel}</button>
        <button className="nl-button nl-button-soft" onClick={() => onNavigate("food")}>Food</button>
        <button className="nl-button nl-button-soft" onClick={() => onNavigate("workouts")}>Move</button>
      </div>
      <p className="nl-today-note">Demo data is illustrative and nutrition labels remain estimates.</p>
    </div>
  </section>;
}
