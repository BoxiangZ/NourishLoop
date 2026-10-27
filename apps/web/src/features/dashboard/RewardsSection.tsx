"use client";

import { api } from "@nourishloop/api-client";
import type { RewardOverviewRead } from "@nourishloop/api-client/schema";

type Props = {
  overview: RewardOverviewRead | null;
  busy: boolean;
  onAction: (action: () => Promise<unknown>) => Promise<boolean>;
};

export default function RewardsSection({ overview, busy, onAction }: Props) {
  return <section className="mt-10 rounded-2xl bg-white p-6 shadow-sm">
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div><h2 className="text-2xl font-bold">Habits & rewards</h2>
        <p className="mt-2 text-sm text-slate-600">Daily habits build weekly progress. Credits come from confirmed actions.</p></div>
      <div className="rounded-full bg-lime-100 px-5 py-2 font-bold text-emerald-900">
        {overview?.balance ?? 0} demo credits
      </div>
    </div>
    {overview && <p className="mt-4 rounded-lg bg-lime-50 p-3 text-sm text-emerald-900">Suggested next step: {overview.suggested_next_step}</p>}
    <div className="mt-5 grid gap-4 sm:grid-cols-2">{overview?.habits.map(habit =>
      <article key={habit.id} className="rounded-xl border border-slate-200 p-4">
        <h3 className="font-bold">{habit.title}</h3>
        <p className="mt-1 text-sm text-slate-600">{habit.description}</p>
        <p className="mt-3 text-xs font-semibold text-emerald-800">
          {habit.completed_today ? "Done today" : "Not yet today"} · {habit.streak_days} day streak · +{habit.points} once per day
        </p>
        <div className="mt-3 h-2 rounded-full bg-slate-100" role="progressbar"
          aria-label={habit.title + " weekly progress"}
          aria-valuenow={Math.min(habit.completed_this_week, habit.weekly_target)}
          aria-valuemin={0} aria-valuemax={habit.weekly_target}>
          <div className="h-2 rounded-full bg-lime-500"
            style={{ width: Math.min(100, habit.completed_this_week / habit.weekly_target * 100) + "%" }} />
        </div>
        <p className="mt-1 text-xs text-slate-500">Weekly challenge: {habit.completed_this_week}/{habit.weekly_target} days</p>
      </article>)}</div>
    <h3 className="mt-7 text-lg font-bold">Redeem a demo badge</h3>
    <div className="mt-3 grid gap-3 sm:grid-cols-2">{overview?.rewards.map(reward =>
      <div key={reward.id} className="rounded-xl bg-emerald-50 p-4">
        <strong>{reward.title}</strong>
        <p className="mt-1 text-sm text-slate-600">{reward.description}</p>
        <button disabled={busy || reward.redeemed || (overview.balance < reward.cost)}
          onClick={() => void onAction(() => api.redeemReward(reward.id))}
          className="mt-3 rounded-full bg-emerald-800 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">
          {reward.redeemed ? "Redeemed" : "Redeem " + reward.cost + " credits"}
        </button>
      </div>)}</div>
    <p className="mt-5 text-xs text-slate-500">Demo credits and badges have no cash value. Removing a shared post reverses its credits.</p>
  </section>;
}
