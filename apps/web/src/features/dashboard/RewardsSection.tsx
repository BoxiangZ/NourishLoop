"use client";

import { api } from "@nourishloop/api-client";
import type { RewardOverviewRead } from "@nourishloop/api-client/schema";
import type { Screen } from "./AppShell";
import Pager from "./Pager";

type Props = {
  overview: RewardOverviewRead | null;
  busy: boolean;
  onAction: (action: () => Promise<unknown>) => Promise<boolean>;
  onNavigate: (screen: Screen) => void;
  ledgerPage: number;
  ledgerHasNext: boolean;
  onLedgerPageChange: (page: number) => void;
};

const reason: Record<string, string> = {
  confirm_meal: "Confirmed a meal",
  share_meal: "Shared a meal",
  complete_workout: "Completed a workout",
  reward_redemption: "Badge redeemed",
  share_retracted: "Share removed",
};

export default function RewardsSection({ overview, busy, onAction, onNavigate,
  ledgerPage, ledgerHasNext, onLedgerPageChange }: Props) {
  return <>
    <div className="nl-page-intro"><span className="nl-eyebrow">REWARDS / KEEP GOING</span>
      <h1>Small steps, real momentum<span className="nl-orange-dot">.</span></h1>
      <p>Build habits from choices you actually make. See your progress and the credits you earned.</p></div>
    <section className="nl-reward-hero">
      <div><span>YOUR BALANCE</span><strong>{overview?.balance ?? 0}</strong><p>demo credits</p></div>
      <div className="nl-reward-orbit" aria-hidden="true"><i>✦</i><b /></div>
    </section>
    {overview && <div className="nl-next-step"><span>✦</span><div><strong>Your next step</strong>
      <p>{overview.suggested_next_step}</p></div></div>}
    <div className="nl-section-heading"><div><span className="nl-eyebrow">THIS WEEK</span><h2>Habits in motion</h2></div></div>
    <div className="nl-habit-grid">{overview?.habits.map(habit =>
      <article key={habit.id} className="nl-habit-card">
        <div className="nl-habit-icon">{habit.id === "confirm_meal" ? "◒" : "✦"}</div>
        <div className="nl-habit-title"><h3>{habit.title}</h3><span>+{habit.points} / day</span></div>
        <p>{habit.description}</p>
        <div className="nl-habit-facts"><span>{habit.completed_today ? "✓ Done today" : "○ Not yet today"}</span>
          <span>{habit.streak_days} day streak</span></div>
        <div className="nl-progress" role="progressbar" aria-label={habit.title + " weekly progress"}
          aria-valuenow={Math.min(habit.completed_this_week, habit.weekly_target)}
          aria-valuemin={0} aria-valuemax={habit.weekly_target}>
          <i style={{ width: Math.min(100, habit.completed_this_week / habit.weekly_target * 100) + "%" }} />
        </div>
        <small>Weekly challenge · {habit.completed_this_week}/{habit.weekly_target} days</small>
      </article>)}</div>
    <div className="nl-reward-links"><button onClick={() => onNavigate("history")}>Confirm a meal →</button>
      <button onClick={() => onNavigate("community")}>Share with Community →</button>
      <button onClick={() => onNavigate("workouts")}>Complete a workout →</button></div>
    <div className="nl-section-heading"><div><span className="nl-eyebrow">THE GOOD STUFF</span>
      <h2>Redeem a badge</h2></div></div>
    <div className="nl-badge-grid">{overview?.rewards.map(reward =>
      <article key={reward.id} className="nl-badge-card"><span className="nl-badge-art">✳</span>
        <div><h3>{reward.title}</h3><p>{reward.description}</p></div>
        <button className="nl-button nl-button-primary" disabled={busy || reward.redeemed || (overview.balance < reward.cost)}
          onClick={() => void onAction(() => api.redeemReward(reward.id))}>
          {reward.redeemed ? "Redeemed" : "Redeem " + reward.cost + " credits"}</button>
      </article>)}</div>
    <div className="nl-section-heading"><div><span className="nl-eyebrow">YOUR ACTIVITY</span>
      <h2>Credit history</h2></div></div>
    {overview?.transactions.length ? <div className="nl-ledger">{overview.transactions.map(row =>
      <div key={row.id}><span>{reason[row.reason] ?? row.reason}<small>{new Date(row.created_at).toLocaleDateString()}</small></span>
        <strong data-positive={row.amount > 0}>{row.amount > 0 ? "+" : ""}{row.amount}</strong></div>)}</div> :
      <div className="nl-empty">Your credit history will appear here after a confirmed action.</div>}
    <Pager page={ledgerPage} hasNext={ledgerHasNext} onChange={onLedgerPageChange} label="credit history" />
    <p className="nl-reward-note">Credits and badges have no cash value. Removing a shared post reverses its credits.</p>
  </>;
}
