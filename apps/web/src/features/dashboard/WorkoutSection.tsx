"use client";

import { useEffect, useState } from "react";
import { api } from "@nourishloop/api-client";
import type {
  ExerciseRead, WorkoutPlanRead, WorkoutProfileRead, WorkoutSessionRead,
} from "@nourishloop/api-client/schema";
import Pager from "./Pager";

const FOCI = ["back", "shoulders", "chest", "legs", "core"] as const;
const EQUIPMENT = ["bodyweight", "machine", "dumbbell", "cable"] as const;
const PAGE_SIZE = 6;
type Focus = typeof FOCI[number];

export default function WorkoutSection({ onCompleted }: { onCompleted: () => Promise<void> }) {
  const [focus, setFocus] = useState<Focus>("back");
  const [page, setPage] = useState(0);
  const [historyPage, setHistoryPage] = useState(0);
  const [exercises, setExercises] = useState<ExerciseRead[]>([]);
  const [hasNext, setHasNext] = useState(false);
  const [sessions, setSessions] = useState<WorkoutSessionRead[]>([]);
  const [historyHasNext, setHistoryHasNext] = useState(false);
  const [profile, setProfile] = useState<WorkoutProfileRead | null>(null);
  const [plan, setPlan] = useState<WorkoutPlanRead | null>(null);
  const [completedPlanId, setCompletedPlanId] = useState("");
  const [minutes, setMinutes] = useState(30);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;
    api.workoutProfile().then(value => { if (active) setProfile(value); })
      .catch((cause: Error) => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    api.exercises({ muscleGroup: focus, limit: PAGE_SIZE + 1, offset: page * PAGE_SIZE })
      .then(rows => { if (active) { setExercises(rows.slice(0, PAGE_SIZE)); setHasNext(rows.length > PAGE_SIZE); } })
      .catch((cause: Error) => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, [focus, page]);

  useEffect(() => {
    let active = true;
    api.workoutSessions(PAGE_SIZE + 1, historyPage * PAGE_SIZE)
      .then(rows => { if (active) { setSessions(rows.slice(0, PAGE_SIZE)); setHistoryHasNext(rows.length > PAGE_SIZE); } })
      .catch((cause: Error) => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, [historyPage, completedPlanId]);

  async function saveProfile() {
    if (!profile) return;
    setBusy(true); setError(""); setNotice("");
    try {
      setProfile(await api.updateWorkoutProfile({
        stage: profile.stage, equipment: profile.equipment, days_per_week: profile.days_per_week,
      }));
      setPlan(null); setNotice("Training context saved. Get a new suggestion to use it.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not save your stage"); }
    finally { setBusy(false); }
  }

  async function findWorkout() {
    if (!profile) return;
    setBusy(true); setError(""); setNotice("Preparing a stage-aware plan…");
    try {
      setProfile(await api.updateWorkoutProfile({
        stage: profile.stage, equipment: profile.equipment, days_per_week: profile.days_per_week,
      }));
      setPlan(await api.recommendWorkout({ focus, minutes })); setCompletedPlanId("");
      setNotice("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not build a plan"); setNotice(""); }
    finally { setBusy(false); }
  }

  async function completeWorkout() {
    if (!plan) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await api.completeWorkout({ plan_id: plan.id, duration_min: plan.minutes });
      setCompletedPlanId(plan.id); setHistoryPage(0);
      await onCompleted();
      setNotice("Workout recorded. Your habit progress has been updated.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not record workout"); }
    finally { setBusy(false); }
  }

  return <>
    <div className="nl-page-intro"><span className="nl-eyebrow">DISCOVER / WORKOUTS</span>
      <h1>Find your next session<span className="nl-orange-dot">.</span></h1>
      <p>Explore individual movements, then build a plan around your current stage and available equipment.</p></div>
    <div className="nl-workout-layout">
      <section className="nl-profile-card nl-workout-context"><span className="nl-eyebrow">YOUR TRAINING CONTEXT</span>
        <h2>Start where you are</h2><p>Choose the stage you can train comfortably at. The plan changes with your context and recent sessions.</p>
        {profile && <>
          <label className="nl-field-label">Current stage
            <select aria-label="Workout stage" value={profile.stage}
              onChange={event => setProfile({ ...profile, stage: event.target.value as WorkoutProfileRead["stage"] })}>
              <option value="beginner">Beginner · building consistency</option>
              <option value="intermediate">Intermediate · regular training</option>
              <option value="advanced">Advanced · experienced</option>
            </select></label>
          <label className="nl-field-label">Training days per week
            <select aria-label="Workout days per week" value={profile.days_per_week}
              onChange={event => setProfile({ ...profile, days_per_week: Number(event.target.value) })}>
              {[1, 2, 3, 4, 5, 6].map(day => <option value={day} key={day}>{day}</option>)}
            </select></label>
          <h3>Equipment you can use</h3><div className="nl-option-grid">{EQUIPMENT.map(item =>
            <label className="nl-check-option" key={item}><input type="checkbox" checked={profile.equipment.includes(item)}
              onChange={() => setProfile({ ...profile, equipment: profile.equipment.includes(item)
                ? profile.equipment.filter(value => value !== item) : [...profile.equipment, item] })} />
              {item}</label>)}</div>
          <button className="nl-button nl-button-soft" disabled={busy || !profile.equipment.length}
            onClick={() => void saveProfile()}>Save training context</button>
        </>}
      </section>
      <section className="nl-workout-suggestion"><span className="nl-eyebrow">FOR YOU / TODAY</span>
        <h2>Make a session that fits</h2>
        <div className="nl-filter-row" aria-label="Workout focus">{FOCI.map(item =>
          <button className="nl-chip" key={item} data-active={focus === item}
            onClick={() => { setFocus(item); setPage(0); }}>{item[0].toUpperCase() + item.slice(1)}</button>)}</div>
        <label className="nl-field-label">Time available
          <select aria-label="Workout minutes" value={minutes} onChange={event => setMinutes(Number(event.target.value))}>
            {[20, 30, 45, 60].map(value => <option value={value} key={value}>{value} minutes</option>)}
          </select></label>
        <button className="nl-button nl-button-primary" disabled={busy || !profile || !profile.equipment.length}
          onClick={() => void findWorkout()}>{busy ? "Working…" : "Recommend my session"}</button>
        <p className="nl-field-help">Exercise choice and dose follow stage-aware rules. When available, AI adds a grounded coaching note.</p>
      </section>
    </div>
    {error && <div role="alert" className="nl-alert">{error}</div>}
    {notice && <div role="status" className="nl-status">{notice}</div>}
    {plan && <section className="nl-plan-card"><div className="nl-section-heading"><div><span className="nl-eyebrow">YOUR PLAN · {plan.minutes} MINUTES</span>
      <h2>{plan.focus[0].toUpperCase() + plan.focus.slice(1)} session</h2></div>
      <span className="nl-plan-stage">{plan.stage} · {plan.explanation_source === "openrouter" ? "AI note" : "grounded guide"}</span></div>
      <p>{plan.explanation}</p>
      <div className="nl-plan-exercises">{plan.exercises.map((row, index) => <article key={row.exercise.id}>
        <span>{String(index + 1).padStart(2, "0")}</span><div><strong>{row.exercise.name}</strong>
          <small>{row.sets} sets · {row.reps} · {row.rest_seconds}s rest</small>
          <p>{row.exercise.instructions}</p></div>
        <a href={row.exercise.source_url} target="_blank" rel="noreferrer">ACE guide ↗</a>
      </article>)}</div>
      <button className="nl-button nl-button-primary" disabled={busy || completedPlanId === plan.id}
        onClick={() => void completeWorkout()}>{completedPlanId === plan.id ? "Session recorded" : "I completed this session"}</button>
    </section>}
    <div className="nl-section-heading"><div><span className="nl-eyebrow">EXERCISE LIBRARY</span>
      <h2>{focus[0].toUpperCase() + focus.slice(1)} movements</h2></div></div>
    <div className="nl-exercise-grid">{exercises.map(item => <article className="nl-exercise-card" key={item.id}>
      <span className="nl-eyebrow">{item.difficulty} · {item.equipment}</span><h3>{item.name}</h3>
      <p>{item.instructions}</p><a href={item.source_url} target="_blank" rel="noreferrer">How to do it · ACE ↗</a>
    </article>)}</div>
    {!exercises.length && <div className="nl-empty">No movements in this category yet.</div>}
    <Pager page={page} hasNext={hasNext} onChange={setPage} label="exercises" />
    <div className="nl-section-heading"><div><span className="nl-eyebrow">YOUR RECORD</span><h2>Completed workouts</h2></div></div>
    {sessions.length ? <div className="nl-history-list">{sessions.map(session => <article className="nl-history-row" key={session.id}>
      <span className="nl-history-icon">↗</span><div><strong>{session.focus} · {session.stage}</strong>
        <small>{session.exercise_names.join(" · ")}</small></div><span className="nl-history-kcal">{session.duration_min} min</span>
    </article>)}</div> : <div className="nl-empty">Completed sessions will appear here after you confirm one.</div>}
    <Pager page={historyPage} hasNext={historyHasNext} onChange={setHistoryPage} label="workout history" />
    <p className="nl-reward-note">For general fitness only. If you have pain, injury or a medical restriction, adapt the plan with a qualified professional.</p>
  </>;
}
