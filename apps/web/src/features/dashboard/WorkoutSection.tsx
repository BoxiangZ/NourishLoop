"use client";

import { useEffect, useState, type ReactNode } from "react";
import { api } from "@nourishloop/api-client";
import type {
  ExerciseRead, GymEquipmentRead, WorkoutPlanRead, WorkoutProfileUpdate,
} from "@nourishloop/api-client/schema";
import Pager from "./Pager";
import WorkoutPlanCard from "./WorkoutPlanCard";
import WorkoutProfileFields from "./WorkoutProfileFields";
import SourcePhoto from "./SourcePhoto";

const FOCI = ["back", "shoulders", "chest", "legs", "core"] as const;
const PAGE_SIZE = 6;
const LG4_PHOTO = {
  url: "https://dst.hkust.edu.hk/sites/default/files/2026-01/1525919867_a6_2_0.jpg",
  source_url: "https://dst.hkust.edu.hk/support-%26-resources/sports-facilities/indoor-sports-facilities",
  alt: "HKUST LG4 Fitness Center",
  credit: "LG4 Fitness Center photo · HKUST DSTO",
};
type Focus = typeof FOCI[number];

export default function WorkoutSection({ automaticPlan, automaticStatus, onProfileSaved, onCompleted, onViewHistory }: {
  automaticPlan?: WorkoutPlanRead | null;
  automaticStatus: ReactNode;
  onProfileSaved: () => void;
  onCompleted: () => Promise<void>;
  onViewHistory: () => void;
}) {
  const [focus, setFocus] = useState<Focus>("back");
  const [page, setPage] = useState(0);
  const [exercises, setExercises] = useState<ExerciseRead[]>([]);
  const [gymEquipment, setGymEquipment] = useState<GymEquipmentRead[] | null>(null);
  const [equipmentError, setEquipmentError] = useState("");
  const [hasNext, setHasNext] = useState(false);
  const [profile, setProfile] = useState<WorkoutProfileUpdate | null>(null);
  const [customPlan, setCustomPlan] = useState<WorkoutPlanRead | null>(null);
  const [completedPlanId, setCompletedPlanId] = useState("");
  const [minutes, setMinutes] = useState(30);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const plan = customPlan ?? automaticPlan;

  useEffect(() => {
    let active = true;
    api.workoutProfile().then(value => { if (active) setProfile(value); })
      .catch((cause: Error) => { if (active) setError(cause.message); });
    api.gymEquipment().then(value => { if (active) setGymEquipment(value); })
      .catch((cause: Error) => { if (active) setEquipmentError(cause.message); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    api.exercises({ muscleGroup: focus, limit: PAGE_SIZE + 1, offset: page * PAGE_SIZE })
      .then(rows => { if (active) { setExercises(rows.slice(0, PAGE_SIZE)); setHasNext(rows.length > PAGE_SIZE); } })
      .catch((cause: Error) => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, [focus, page]);

  async function saveProfile() {
    if (!profile) return;
    setBusy(true); setError(""); setNotice("");
    try {
      setProfile(await api.updateWorkoutProfile({
        stage: profile.stage, equipment: profile.equipment, days_per_week: profile.days_per_week,
      }));
      setCustomPlan(null); onProfileSaved(); setNotice("Training settings saved.");
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
      setCustomPlan(await api.recommendWorkout({ focus, minutes }));
      onProfileSaved();
      setNotice("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not build a plan"); setNotice(""); }
    finally { setBusy(false); }
  }

  async function completeWorkout() {
    if (!plan) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await api.completeWorkout({ plan_id: plan.id, duration_min: plan.minutes });
      setCompletedPlanId(plan.id);
      await onCompleted();
      setNotice("Workout recorded. Your habit progress has been updated.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not record workout"); }
    finally { setBusy(false); }
  }

  return <>
    <div className="nl-page-intro">
      <h1>Today’s workout<span className="nl-orange-dot">.</span></h1>
      <p>Your suggested session uses your saved stage, equipment and recent workouts.</p>
      <button className="nl-text-link" onClick={onViewHistory}>View training history →</button></div>
    {error && <div role="alert" className="nl-alert">{error}</div>}
    {notice && <div role="status" className="nl-status">{notice}</div>}
    {!customPlan && automaticStatus}
    {plan && <WorkoutPlanCard plan={plan}>
      <button className="nl-button nl-button-primary" disabled={busy || completedPlanId === plan.id}
        onClick={() => void completeWorkout()}>{completedPlanId === plan.id ? "Session recorded" : "I completed this session"}</button>
      {customPlan && <button className="nl-button nl-button-soft" disabled={busy}
        onClick={() => setCustomPlan(null)}>Back to today’s suggestion</button>}
    </WorkoutPlanCard>}
    <details className="nl-suggestion-options">
      <summary>Adjust workout</summary>
    <div className="nl-workout-layout">
      <section className="nl-profile-card nl-workout-context">
        <h2>Training settings</h2>
        {profile && <>
          <WorkoutProfileFields value={profile} onChange={setProfile} />
          <button className="nl-button nl-button-soft" disabled={busy || !profile.equipment.length}
            onClick={() => void saveProfile()}>Save training context</button>
        </>}
      </section>
      <section className="nl-workout-suggestion">
        <h2>Choose a focus and duration</h2>
        <div className="nl-filter-row" aria-label="Workout focus">{FOCI.map(item =>
          <button className="nl-chip" key={item} data-active={focus === item}
            onClick={() => { setFocus(item); setPage(0); }}>{item[0].toUpperCase() + item.slice(1)}</button>)}</div>
        <label className="nl-field-label">Time available
          <select aria-label="Workout minutes" value={minutes} onChange={event => setMinutes(Number(event.target.value))}>
            {[20, 30, 45, 60].map(value => <option value={value} key={value}>{value} minutes</option>)}
          </select></label>
        <button className="nl-button nl-button-primary" disabled={busy || !profile || !profile.equipment.length}
          onClick={() => void findWorkout()}>{busy ? "Working…" : "Recommend my session"}</button>
      </section>
    </div>
    </details>
    <details className="nl-suggestion-options">
      <summary>HKUST gym equipment</summary>
      <SourcePhoto photo={LG4_PHOTO} variant="facility" />
      <p className="nl-directory-note">Equipment categories published by HKUST. The listing covers both fitness centers and does not give models or counts by room.</p>
      {equipmentError && <div role="alert" className="nl-alert">{equipmentError}</div>}
      {!gymEquipment && !equipmentError && <p role="status">Loading gym equipment…</p>}
      <div className="nl-exercise-grid">{gymEquipment?.map(item =>
        <article className="nl-exercise-card" key={item.id}>
          <span className="nl-eyebrow">{item.category}</span><h3>{item.name}</h3><p>{item.location}</p>
          <a href={item.source_url} target="_blank" rel="noreferrer">HKUST listing ↗</a>
        </article>)}</div>
    </details>
    <div className="nl-section-heading"><div><span className="nl-eyebrow">EXERCISE LIBRARY</span>
      <h2>{focus[0].toUpperCase() + focus.slice(1)} movements</h2></div></div>
    <div className="nl-exercise-grid">{exercises.map(item => <article className="nl-exercise-card" key={item.id}>
      {item.source_photo && <SourcePhoto photo={item.source_photo} />}
      <span className="nl-eyebrow">{item.difficulty}</span><h3>{item.name}</h3>
      <p><strong>Equipment:</strong> {item.equipment_detail ?? item.equipment}</p>
      <p>{item.instructions}</p><a href={item.source_url} target="_blank" rel="noreferrer">How to do it · ACE ↗</a>
    </article>)}</div>
    {!exercises.length && <div className="nl-empty">No movements in this category yet.</div>}
    <Pager page={page} hasNext={hasNext} onChange={setPage} label="exercises" />
    <p className="nl-reward-note">For general fitness only. If you have pain, injury or a medical restriction, adapt the plan with a qualified professional.</p>
  </>;
}
