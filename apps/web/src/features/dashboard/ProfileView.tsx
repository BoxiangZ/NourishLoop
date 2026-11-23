"use client";

import { useEffect, useState } from "react";
import { api } from "@nourishloop/api-client";
import type {
  GoalUpdate, MeRead, ProfileUpdate, WorkoutProfileUpdate,
} from "@nourishloop/api-client/schema";
import WorkoutProfileFields from "./WorkoutProfileFields";

type Props = {
  me: MeRead;
  busy: boolean;
  onAction: (action: () => Promise<unknown>) => Promise<boolean>;
  onMealSettingsSaved: () => void;
  onTrainingSettingsSaved: () => void;
};

const preferences = [
  ["vegan", "Vegan"], ["vegetarian", "Vegetarian"],
  ["high_protein", "High protein"], ["high_fibre", "High fibre"],
] as const;
const allergens = [
  ["soy", "Soy"], ["wheat", "Wheat"], ["egg", "Egg"], ["fish", "Fish"],
] as const;
const personalNumbers = [
  { key: "age", label: "Age (years)", min: 1, max: 120, step: 1 },
  { key: "height_cm", label: "Height (cm)", min: 30, max: 275, step: "any" },
  { key: "weight_kg", label: "Current weight (kg)", min: 2, max: 700, step: "any" },
  { key: "target_weight_kg", label: "Target weight (kg)", min: 2, max: 700, step: "any" },
] as const;

function optionalNumber(form: FormData, name: string): number | null {
  const value = form.get(name);
  return typeof value === "string" && value !== "" ? Number(value) : null;
}

export default function ProfileView({ me, busy, onAction, onMealSettingsSaved, onTrainingSettingsSaved }: Props) {
  const [name, setName] = useState(me.profile.display_name);
  const [prefs, setPrefs] = useState(me.profile.dietary_preferences ?? []);
  const [allergyList, setAllergyList] = useState(me.profile.allergies ?? []);
  const [activity, setActivity] = useState<NonNullable<ProfileUpdate["activity_level"]> | "">(
    me.profile.activity_level ?? "",
  );
  const [goal, setGoal] = useState(me.goal.goal);
  const [training, setTraining] = useState<WorkoutProfileUpdate | null>(null);
  const [trainingError, setTrainingError] = useState("");
  const [saved, setSaved] = useState<"profile" | "goal" | "training" | null>(null);

  useEffect(() => {
    let active = true;
    api.workoutProfile()
      .then(profile => { if (active) setTraining(profile); })
      .catch((cause: Error) => { if (active) setTrainingError(cause.message); });
    return () => { active = false; };
  }, []);

  function toggle<T extends string>(values: T[], item: T, setter: (next: T[]) => void) {
    setter(values.includes(item) ? values.filter(value => value !== item) : [...values, item]);
  }

  return <>
    <div className="nl-page-intro"><span className="nl-eyebrow">PROFILE / YOUR CONTEXT</span>
      <h1>Make it yours<span className="nl-orange-dot">.</span></h1>
      <p>Manage your personal details, food preferences and training settings.</p></div>
    <div className="nl-profile-head"><span className="nl-profile-avatar">{name.slice(0, 1).toUpperCase() || "N"}</span>
      <h2>{me.profile.display_name}</h2></div>
    <form onSubmit={event => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const profile: ProfileUpdate = {
        display_name: name.trim(),
        age: optionalNumber(data, "age"),
        height_cm: optionalNumber(data, "height_cm"),
        weight_kg: optionalNumber(data, "weight_kg"),
        target_weight_kg: optionalNumber(data, "target_weight_kg"),
        activity_level: activity || null,
        meal_budget_hkd: optionalNumber(data, "meal_budget_hkd"),
        dietary_preferences: prefs,
        allergies: allergyList,
      };
      setSaved(null);
      void onAction(() => api.updateProfile(profile)).then(ok => {
        if (ok) { setSaved("profile"); onMealSettingsSaved(); }
      });
    }}>
      <div className="nl-profile-edit-grid">
        <section className="nl-profile-card" aria-labelledby="personal-details-heading">
          <h2 id="personal-details-heading">Personal details</h2>
          <p className="nl-field-help">Only your display name appears on Community posts. All other fields here are optional.</p>
          <div className="nl-profile-fields">
            <label className="nl-field-label">Display name
              <input required maxLength={80} value={name} onChange={event => setName(event.target.value)} />
            </label>
            <label className="nl-field-label">Daily activity level
              <select value={activity} onChange={event => setActivity(event.target.value as typeof activity)}>
                <option value="">Select an activity level</option>
                <option value="low">Mostly sitting</option>
                <option value="light">Lightly active</option>
                <option value="moderate">Moderately active</option>
                <option value="high">Very active</option>
              </select>
            </label>
            {personalNumbers.map(({ key, label, min, max, step }) =>
              <label key={key} className="nl-field-label">{label}
                <input name={key} type="number" min={min} max={max} step={step} defaultValue={me.profile[key] ?? ""} />
              </label>)}</div>
        </section>
        <section className="nl-profile-card" aria-labelledby="food-preferences-heading">
          <h2 id="food-preferences-heading">Food preferences</h2>
          <label className="nl-field-label">Maximum spend per meal (HKD)
            <input name="meal_budget_hkd" type="number" min="0" max="5000" step="any"
              defaultValue={me.profile.meal_budget_hkd ?? ""} placeholder="No limit" />
          </label>
          <p className="nl-field-help">Your suggested meals stay within this budget.</p>
          <h3>Dietary preferences</h3>
          <div className="nl-option-grid">{preferences.map(([value, label]) =>
            <label key={value} className="nl-check-option"><input type="checkbox" checked={prefs.includes(value)}
              onChange={() => toggle(prefs, value, setPrefs)} />{label}</label>)}</div>
          <h3>Allergies to avoid</h3>
          <div className="nl-option-grid">{allergens.map(([value, label]) =>
            <label key={value} className="nl-check-option"><input type="checkbox" checked={allergyList.includes(value)}
              onChange={() => toggle(allergyList, value, setAllergyList)} />{label}</label>)}</div>
        </section>
      </div>
      <div className="nl-profile-save">
        <button className="nl-button nl-button-primary" disabled={busy || !name.trim()}>Save profile</button>
        {saved === "profile" && <p className="nl-field-help" role="status">Profile saved.</p>}
      </div>
    </form>
    <form className="nl-profile-card" onSubmit={event => {
      event.preventDefault();
      const target = optionalNumber(new FormData(event.currentTarget), "daily_calorie_target");
      setSaved(null);
      void onAction(() => api.updateGoals({ goal, daily_calorie_target: target })).then(ok => {
        if (ok) { setSaved("goal"); onMealSettingsSaved(); }
      });
    }}>
      <h2>Nutrition goal</h2>
      <label className="nl-field-label">Main goal
        <select aria-label="Main goal" value={goal}
          onChange={event => setGoal(event.target.value as GoalUpdate["goal"])}>
          <option value="eat_healthier">Eat healthier</option>
          <option value="reduce_body_fat">Reduce body fat</option>
          <option value="build_muscle">Build muscle</option>
        </select></label>
      <label className="nl-field-label">Daily calorie target (kcal, optional)
        <input name="daily_calorie_target" type="number" min="1000" max="5000" step="any"
          defaultValue={me.goal.daily_calorie_target ?? ""} placeholder="Leave blank to skip" /></label>
      <p className="nl-field-help">The demo uses illustrative nutrition estimates.</p>
      <button className="nl-button nl-button-primary" disabled={busy}>Save goal</button>
      {saved === "goal" && <p className="nl-field-help" role="status">Goal saved.</p>}
    </form>
    <form className="nl-profile-card" onSubmit={event => {
      event.preventDefault();
      if (!training?.equipment.length) return;
      const { stage, equipment, days_per_week } = training;
      setSaved(null);
      void onAction(() => api.updateWorkoutProfile({ stage, equipment, days_per_week })).then(ok => {
        if (ok) { setSaved("training"); onTrainingSettingsSaved(); }
      });
    }}>
      <h2>Training settings</h2>
      {trainingError && <p role="alert" className="nl-alert">{trainingError}</p>}
      {!training && !trainingError && <p role="status">Loading training settings…</p>}
      {training && <>
        <WorkoutProfileFields value={training} onChange={setTraining} />
        <button className="nl-button nl-button-primary" disabled={busy || !training.equipment.length}>
          Save training settings
        </button>
        {saved === "training" && <p className="nl-field-help" role="status">Training settings saved.</p>}
      </>}
    </form>
  </>;
}
