"use client";

import type { Screen } from "./AppShell";
import { todayFocus } from "./todayFocus";

type Props = {
  mealCount: number;
  workoutMinutes: number;
  onNavigate: (screen: Screen) => void;
  onAction: (screen: Screen) => void;
};

export default function TodaySection({ mealCount, workoutMinutes, onNavigate, onAction }: Props) {
  const focus = todayFocus({ mealCount, workoutMinutes });
  const actionLabel = focus.action === "workouts" ? "Log a workout" : focus.action === "history"
    ? "Review today" : "Find a meal";

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
