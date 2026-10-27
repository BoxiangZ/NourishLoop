"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@nourishloop/api-client";
import type {
  CommunityPostRead, CommunityReportRead, DailySummary, DecisionRead, MeRead,
  MealLogRead, MenuItemRead, RecommendationRunRead, RewardOverviewRead, VenueRead,
} from "@nourishloop/api-client/schema";
import CommunitySection from "./CommunitySection";
import RewardsSection from "./RewardsSection";

export default function Dashboard() {
  const [me, setMe] = useState<MeRead | null>(null);
  const [venues, setVenues] = useState<VenueRead[]>([]);
  const [menu, setMenu] = useState<MenuItemRead[]>([]);
  const [run, setRun] = useState<RecommendationRunRead | null>(null);
  const [decisions, setDecisions] = useState<DecisionRead[]>([]);
  const [mealLogs, setMealLogs] = useState<MealLogRead[]>([]);
  const [sharedMealLogIds, setSharedMealLogIds] = useState<string[]>([]);
  const [posts, setPosts] = useState<CommunityPostRead[]>([]);
  const [reports, setReports] = useState<CommunityReportRead[]>([]);
  const [rewards, setRewards] = useState<RewardOverviewRead | null>(null);
  const [feedLimit, setFeedLimit] = useState(20);
  const [jobStatus, setJobStatus] = useState("");
  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [person, places, items, plans, totals, logs, feed, progress, sharedIds] = await Promise.all([
      api.me(), api.venues(), api.menuItems(), api.decisions(), api.summary(),
      api.mealLogs(), api.communityPosts(feedLimit), api.rewardOverview(), api.sharedMealLogIds(),
    ]);
    setMe(person); setVenues(places); setMenu(items); setDecisions(plans); setSummary(totals);
    setMealLogs(logs); setPosts(feed); setRewards(progress); setSharedMealLogIds(sharedIds);
    setReports(person.is_moderator ? await api.pendingReports() : []);
  }, [feedLimit]);

  useEffect(() => { refresh().catch((e: Error) => setError(e.message)); }, [refresh]);

  async function act(action: () => Promise<unknown>): Promise<boolean> {
    setBusy(true); setError(null);
    try { await action(); await refresh(); return true; }
    catch (e) { setError(e instanceof Error ? e.message : "Something went wrong"); return false; }
    finally { setBusy(false); }
  }

  function loadMorePosts() {
    setFeedLimit(current => current + 20);
  }

  async function switchDemoUser(id: string) {
    if (busy || id === me?.id) return;
    await act(async () => {
      api.setDemoUserId(id);
      setRun(null);
      setJobStatus("");
    });
  }

  async function findLunch() {
    setBusy(true); setError(null); setJobStatus("Recommendation queued");
    try {
      const queued = await api.startRecommendationJob({ meal_slot: "lunch", limit: 3 });
      for (let attempt = 0; attempt < 30; attempt++) {
        const job = await api.recommendationJob(queued.id);
        setJobStatus(`Recommendation ${job.status} · attempt ${job.attempts}`);
        if (job.status === "completed" && job.run) {
          setRun(job.run);
          await refresh();
          return;
        }
        if (job.status === "failed") throw new Error(`Recommendation failed: ${job.error ?? "worker error"}`);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      throw new Error("Recommendation is still processing. Check the worker and try again.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally { setBusy(false); }
  }

  const venueName = (id: string) => venues.find(v => v.id === id)?.name ?? "Campus kitchen";

  return <main className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
    <header className="mb-10 flex flex-wrap items-center justify-between gap-4">
      <div><div className="text-2xl font-black tracking-tight text-emerald-800">NourishLoop</div>
        <p className="text-sm text-slate-500">Discover · Decide · Act · Track · Reward · Improve</p></div>
      <div className="flex flex-wrap items-center gap-3">
        {me && ["demo-student", "demo-peer"].includes(me.id) &&
          <label className="text-xs font-semibold text-slate-700">Demo account{" "}
            <select aria-label="Demo account" value={me.id} disabled={busy}
              onChange={event => void switchDemoUser(event.target.value)}
              className="ml-1 rounded-lg border border-slate-300 bg-white px-2 py-2 text-xs">
              <option value="demo-student">Demo Student · moderator</option>
              <option value="demo-peer">Community Peer</option>
            </select>
          </label>}
        <span className="rounded-full bg-amber-100 px-4 py-2 text-xs font-semibold text-amber-900">Fictional demo menu · estimated nutrition</span>
      </div>
    </header>

    <section className="rounded-3xl bg-emerald-900 p-7 text-white shadow-lg sm:p-10">
      <p className="text-sm uppercase tracking-[0.25em] text-emerald-200">Today’s lunch, made simpler</p>
      <h1 className="mt-3 max-w-2xl text-3xl font-semibold leading-tight sm:text-5xl">Choose a meal that fits your day.</h1>
      <p className="mt-4 max-w-2xl text-emerald-100">{me ? `${me.profile.display_name} · Goal: ${me.goal.goal.replaceAll("_", " ")}` : "Loading your demo profile…"}</p>
      <button disabled={busy || !me} onClick={findLunch}
        className="mt-7 rounded-full bg-lime-300 px-6 py-3 font-semibold text-emerald-950 hover:bg-lime-200 disabled:opacity-50">
        {busy ? "Working…" : "Find my lunch"}
      </button>
      {jobStatus && <p role="status" className="mt-3 text-sm text-emerald-100">{jobStatus}</p>}
    </section>
    <CommunitySection key={me?.id} posts={posts} mealLogs={mealLogs} sharedMealLogIds={sharedMealLogIds} reports={reports}
      isModerator={me?.is_moderator ?? false} busy={busy} onAction={act} onLoadMore={loadMorePosts} />
    <RewardsSection overview={rewards} busy={busy} onAction={act} />

    {error && <div role="alert" className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</div>}

    <section className="mt-10 grid gap-8 lg:grid-cols-[1.7fr_1fr]">
      <div>
        <div className="mb-4 flex items-end justify-between"><h2 className="text-2xl font-bold">{run ? "Recommended for you" : "Explore the demo menu"}</h2><span className="text-sm text-slate-500">{menu.length} meals</span></div>
        {menu.length === 0 && <p className="rounded-2xl bg-white p-5 text-sm text-slate-600">No demo meals are available yet. Load the seed data and refresh.</p>}
        {run && run.recommendations.length === 0 && <p className="rounded-2xl bg-white p-5 text-sm text-slate-600">No meals meet your dietary restrictions. Review your profile or try again later.</p>}
        <div className="grid gap-4 sm:grid-cols-2">
          {(run ? run.recommendations.map(r => ({ item: r.menu_item, recommendation: r })) : menu.map(item => ({ item, recommendation: null }))).map(({ item, recommendation }) =>
            <article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="mb-3 flex items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">{venueName(item.venue_id)}</p><h3 className="mt-1 text-lg font-bold">{item.name}</h3></div><span className="whitespace-nowrap rounded-full bg-emerald-50 px-3 py-1 text-xs text-emerald-800">≈ {item.nutrition.calories_kcal} kcal</span></div>
              <p className="text-sm text-slate-600">{item.description}</p>
              <p className="mt-3 text-xs text-slate-500">{item.nutrition.protein_g} g protein · HK${item.price_hkd} · {item.nutrition.provenance.replaceAll("_", " ")}</p>
              {recommendation && <div className="mt-4 border-l-2 border-lime-400 pl-3 text-sm text-slate-700"><p>{recommendation.explanation}</p><p className="mt-2 text-xs text-slate-500">Evidence confidence: {recommendation.confidence}. {recommendation.confidence_reason}</p></div>}
              <button disabled={busy} onClick={() => act(() => api.decide({ menu_item_id: item.id, recommendation_id: recommendation?.id ?? null }))}
                className="mt-5 rounded-full border border-emerald-700 px-4 py-2 text-sm font-semibold text-emerald-800 hover:bg-emerald-50 disabled:opacity-50">Plan this meal</button>
            </article>) }
        </div>
      </div>
      <aside className="space-y-5">
        <div className="rounded-2xl bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Today’s confirmed intake</h2>
          <div className="mt-4 text-4xl font-black text-emerald-800">{summary?.totals.calories_kcal ?? 0}<span className="ml-2 text-base font-medium text-slate-500">kcal</span></div>
          <p className="mt-2 text-sm text-slate-500">{summary?.meal_count ?? 0} confirmed meals · planned meals are excluded</p>
          <p className="mt-4 text-sm">Protein {summary?.totals.protein_g ?? 0} g · Carbs {summary?.totals.carbs_g ?? 0} g · Fat {summary?.totals.fat_g ?? 0} g</p>
        </div>
        <div className="rounded-2xl bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Your meal plans</h2>
          {decisions.length === 0 ? <p className="mt-3 text-sm text-slate-500">Choose a meal to make a plan.</p> :
            <ul className="mt-4 space-y-4">{decisions.map(decision => <li key={decision.id} className="border-t border-slate-100 pt-4">
              <div className="flex items-center justify-between gap-3"><strong className="text-sm">{decision.menu_item.name}</strong><span className="text-xs capitalize text-slate-500">{decision.status}</span></div>
              {decision.status === "planned" && <button disabled={busy} onClick={() => act(() => api.logMeal({ decision_id: decision.id, servings: 1 }))}
                className="mt-3 rounded-full bg-emerald-700 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-800 disabled:opacity-50">I ate this meal</button>}
            </li>)}</ul>}
        </div>
      </aside>
    </section>
    <footer className="mt-12 border-t border-slate-200 pt-5 text-xs text-slate-500">Demo data only. Nutrition figures are illustrative and not verified restaurant information.</footer>
  </main>;
}
