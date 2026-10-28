"use client";

import { useEffect, useState } from "react";
import { api } from "@nourishloop/api-client";
import type { GoalUpdate, MeRead, ProfileUpdate } from "@nourishloop/api-client/schema";

type Props = {
  me: MeRead | null;
  busy: boolean;
  onAction: (action: () => Promise<unknown>) => Promise<boolean>;
};

const preferences = [
  ["vegan", "Vegan"], ["vegetarian", "Vegetarian"],
  ["high_protein", "High protein"], ["high_fibre", "High fibre"],
] as const;
const allergens = [
  ["soy", "Soy"], ["wheat", "Wheat"], ["egg", "Egg"], ["fish", "Fish"],
] as const;

export default function ProfileView({ me, busy, onAction }: Props) {
  const [name, setName] = useState("");
  const [prefs, setPrefs] = useState<NonNullable<ProfileUpdate["dietary_preferences"]>>([]);
  const [allergyList, setAllergyList] = useState<NonNullable<ProfileUpdate["allergies"]>>([]);
  const [goal, setGoal] = useState<GoalUpdate["goal"]>("eat_healthier");
  const [target, setTarget] = useState("");

  useEffect(() => {
    if (!me) return;
    setName(me.profile.display_name);
    setPrefs(me.profile.dietary_preferences ?? []);
    setAllergyList(me.profile.allergies ?? []);
    setGoal(me.goal.goal);
    setTarget(me.goal.daily_calorie_target?.toString() ?? "");
  }, [me]);

  function toggle<T extends string>(values: T[], item: T, setter: (next: T[]) => void) {
    setter(values.includes(item) ? values.filter(value => value !== item) : [...values, item]);
  }

  return <>
    <div className="nl-page-intro"><span className="nl-eyebrow">PROFILE / YOUR CONTEXT</span>
      <h1>Make it yours<span className="nl-orange-dot">.</span></h1>
      <p>Your preferences shape recommendations. You can change them whenever you need.</p></div>
    <div className="nl-profile-head"><span className="nl-profile-avatar">{name.slice(0, 1).toUpperCase() || "N"}</span>
      <div><h2>{me?.profile.display_name ?? "Your profile"}</h2>
        <p>{me?.is_moderator ? "Demo Student · Community moderator" : "Community Peer"} · Local demo account</p></div></div>
    <form className="nl-profile-card" onSubmit={event => {
      event.preventDefault();
      void onAction(() => api.updateProfile({
        display_name: name.trim(), dietary_preferences: prefs, allergies: allergyList,
      }));
    }}>
      <span className="nl-eyebrow">FOOD PREFERENCES</span><h2>What works for you?</h2>
      <label className="nl-field-label">Display name
        <input aria-label="Display name" required maxLength={80} value={name}
          onChange={event => setName(event.target.value)} /></label>
      <h3>Dietary preferences</h3>
      <div className="nl-option-grid">{preferences.map(([value, label]) =>
        <label key={value} className="nl-check-option"><input type="checkbox" checked={prefs.includes(value)}
          onChange={() => toggle(prefs, value, setPrefs)} />{label}</label>)}</div>
      <h3>Allergies to avoid</h3>
      <div className="nl-option-grid">{allergens.map(([value, label]) =>
        <label key={value} className="nl-check-option"><input type="checkbox" checked={allergyList.includes(value)}
          onChange={() => toggle(allergyList, value, setAllergyList)} />{label}</label>)}</div>
      <button className="nl-button nl-button-primary" disabled={busy || !name.trim()}>Save preferences</button>
    </form>
    <form className="nl-profile-card" onSubmit={event => {
      event.preventDefault();
      void onAction(() => api.updateGoals({
        goal, daily_calorie_target: target ? Number(target) : null,
      }));
    }}>
      <span className="nl-eyebrow">YOUR GOAL</span><h2>What are you working toward?</h2>
      <label className="nl-field-label">Main goal
        <select aria-label="Main goal" value={goal}
          onChange={event => setGoal(event.target.value as GoalUpdate["goal"])}>
          <option value="eat_healthier">Eat healthier</option>
          <option value="reduce_body_fat">Reduce body fat</option>
          <option value="build_muscle">Build muscle</option>
        </select></label>
      <label className="nl-field-label">Optional daily calorie target
        <input aria-label="Daily calorie target" type="number" min="1000" max="5000" step="50"
          value={target} onChange={event => setTarget(event.target.value)} placeholder="Leave blank to skip" /></label>
      <p className="nl-field-help">Nutrition figures in this demo are estimates, not verified restaurant data.</p>
      <button className="nl-button nl-button-primary" disabled={busy}>Save goal</button>
    </form>
  </>;
}
