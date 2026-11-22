"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@nourishloop/api-client";
import type {
  CommunityPostRead, CommunityReportRead, DailySummary, DecisionRead, MeRead,
  MealLogRead, MenuItemRead, RecommendationRunRead, RewardOverviewRead, VenueRead,
  PhotoMealRead, WorkoutSessionRead,
} from "@nourishloop/api-client/schema";
import AppShell, { type Screen } from "./AppShell";
import CommunitySection from "./CommunitySection";
import DailyCoachReport from "./DailyCoachReport";
import FoodCard from "./FoodCard";
import Pager from "./Pager";
import PlacesSection from "./PlacesSection";
import PhotoAnalyzer from "./PhotoAnalyzer";
import MealCheckinCard from "./MealCheckinCard";
import ProfileView from "./ProfileView";
import RewardsSection from "./RewardsSection";
import TodaySection from "./TodaySection";
import WorkoutSection from "./WorkoutSection";
import { hongKongDate } from "./hongKongDate";

const MENU_SIZE = 4;
const LIST_SIZE = 5;
const COMMUNITY_SIZE = 4;
type Filter = "all" | "vegan" | "high_protein" | "under_50";
type FoodMode = "explore" | "recommend";
type BrowseMode = "meals" | "places";

function routeFromUrl(): { screen: Screen; foodMode: FoodMode } {
  const value = new URLSearchParams(window.location.search).get("page");
  switch (value) {
    case "discover": return { screen: "food", foodMode: "explore" };
    case "for-you": return { screen: "food", foodMode: "recommend" };
    case "workouts": return { screen: "workouts", foodMode: "explore" };
    case "history": return { screen: "history", foodMode: "explore" };
    case "community": return { screen: "community", foodMode: "explore" };
    case "rewards": return { screen: "rewards", foodMode: "explore" };
    case "profile": return { screen: "profile", foodMode: "explore" };
    default: return { screen: "today", foodMode: "explore" };
  }
}

function weekDays(date: string): string[] {
  const anchor = new Date(`${date}T12:00:00Z`);
  const offset = (anchor.getUTCDay() + 6) % 7;
  return Array.from({ length: 7 }, (_, index) => {
    const day = new Date(anchor);
    day.setUTCDate(anchor.getUTCDate() - offset + index);
    return day.toISOString().slice(0, 10);
  });
}

export default function Dashboard() {
  const [screen, setScreen] = useState<Screen>("today");
  const [foodMode, setFoodMode] = useState<FoodMode>("explore");
  const [browseMode, setBrowseMode] = useState<BrowseMode>("meals");
  const [photoMode, setPhotoMode] = useState<"instant" | "background">("instant");
  const [me, setMe] = useState<MeRead | null>(null);
  const [venues, setVenues] = useState<VenueRead[]>([]);
  const [menu, setMenu] = useState<MenuItemRead[]>([]);
  const [menuPage, setMenuPage] = useState(0);
  const [menuHasNext, setMenuHasNext] = useState(false);
  const [searchDraft, setSearchDraft] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [run, setRun] = useState<RecommendationRunRead | null>(null);
  const [decisions, setDecisions] = useState<DecisionRead[]>([]);
  const [historyPage, setHistoryPage] = useState(0);
  const [historyHasNext, setHistoryHasNext] = useState(false);
  const [historyMode, setHistoryMode] = useState<"decisions" | "meals" | "photos">("decisions");
  const [mealLogs, setMealLogs] = useState<MealLogRead[]>([]);
  const [historyLogs, setHistoryLogs] = useState<MealLogRead[]>([]);
  const [logPage, setLogPage] = useState(0);
  const [logHasNext, setLogHasNext] = useState(false);
  const [photoMeals, setPhotoMeals] = useState<PhotoMealRead[]>([]);
  const [photoPage, setPhotoPage] = useState(0);
  const [photoHasNext, setPhotoHasNext] = useState(false);
  const [sharedMealLogIds, setSharedMealLogIds] = useState<string[]>([]);
  const [posts, setPosts] = useState<CommunityPostRead[]>([]);
  const [communityPage, setCommunityPage] = useState(0);
  const [communityHasNext, setCommunityHasNext] = useState(false);
  const [reports, setReports] = useState<CommunityReportRead[]>([]);
  const [rewards, setRewards] = useState<RewardOverviewRead | null>(null);
  const [ledgerPage, setLedgerPage] = useState(0);
  const [ledgerHasNext, setLedgerHasNext] = useState(false);
  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [workoutSessions, setWorkoutSessions] = useState<WorkoutSessionRead[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dailyRequestId = useRef(0);

  const navigate = useCallback((next: Screen) => {
    setScreen(next);
    const url = new URL(window.location.href);
    if (next === "food") setFoodMode("explore");
    if (next === "today") {
      setSummary(null);
      setWorkoutSessions([]);
      url.searchParams.delete("page");
    }
    else if (next === "food") url.searchParams.set("page", "discover");
    else url.searchParams.set("page", next);
    window.history.pushState({ page: next }, "", url);
    window.scrollTo({ top: 0, behavior: "instant" });
  }, []);

  useEffect(() => {
    const applyRoute = () => {
      const route = routeFromUrl();
      setScreen(route.screen);
      setFoodMode(route.foodMode);
    };
    applyRoute();
    const onPop = applyRoute;
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const refresh = useCallback(async () => {
    const tag = filter === "vegan" || filter === "high_protein" ? filter : undefined;
    const maxPriceHkd = filter === "under_50" ? 50 : undefined;
    const [person, places, items, plans, logs, pagedLogs, feed, progress, sharedIds, photoRecords] = await Promise.all([
      api.me(), api.venues(), api.menuItems({
        limit: MENU_SIZE + 1, offset: menuPage * MENU_SIZE, q: search, tag, maxPriceHkd,
      }),
      api.decisions(LIST_SIZE + 1, historyPage * LIST_SIZE),
      api.mealLogs(100), api.mealLogs(LIST_SIZE + 1, logPage * LIST_SIZE),
      api.communityPosts(COMMUNITY_SIZE + 1, communityPage * COMMUNITY_SIZE),
      api.rewardOverview(LIST_SIZE + 1, ledgerPage * LIST_SIZE), api.sharedMealLogIds(),
      api.photoMeals(LIST_SIZE + 1, photoPage * LIST_SIZE),
    ]);
    setMe(person); setVenues(places);
    setMenu(items.slice(0, MENU_SIZE)); setMenuHasNext(items.length > MENU_SIZE);
    setDecisions(plans.slice(0, LIST_SIZE)); setHistoryHasNext(plans.length > LIST_SIZE);
    setMealLogs(logs);
    setHistoryLogs(pagedLogs.slice(0, LIST_SIZE)); setLogHasNext(pagedLogs.length > LIST_SIZE);
    setPosts(feed.slice(0, COMMUNITY_SIZE)); setCommunityHasNext(feed.length > COMMUNITY_SIZE);
    setRewards({ ...progress, transactions: progress.transactions.slice(0, LIST_SIZE) });
    setLedgerHasNext(progress.transactions.length > LIST_SIZE);
    setSharedMealLogIds(sharedIds);
    setPhotoMeals(photoRecords.slice(0, LIST_SIZE)); setPhotoHasNext(photoRecords.length > LIST_SIZE);
    setReports(person.is_moderator ? await api.pendingReports() : []);
  }, [communityPage, filter, historyPage, ledgerPage, logPage, menuPage, photoPage, search]);

  useEffect(() => { refresh().catch((cause: Error) => setError(cause.message)); }, [refresh]);

  const loadDaily = useCallback(async () => {
    if (screen !== "today" && screen !== "history") return;
    const requestId = ++dailyRequestId.current;
    try {
      const [nextSummary, nextSessions] = await Promise.all([
        api.summary(screen === "today" ? undefined : selectedDate ?? undefined),
        api.workoutSessions(100, 0),
      ]);
      if (requestId !== dailyRequestId.current) return;
      setSummary(nextSummary);
      setWorkoutSessions(nextSessions);
    } catch (cause) {
      if (requestId !== dailyRequestId.current) return;
      setError(cause instanceof Error ? cause.message : "Something went wrong");
    }
  }, [screen, selectedDate]);

  useEffect(() => { void loadDaily(); }, [loadDaily]);

  useEffect(() => {
    if (screen !== "history" || historyMode !== "photos" ||
        !photoMeals.some(record => record.review_status === "pending" || record.review_status === "processing")) return;
    const timer = window.setInterval(() => { void refresh().catch(() => {}); }, 3000);
    return () => window.clearInterval(timer);
  }, [screen, historyMode, photoMeals, refresh]);

  async function act(action: () => Promise<unknown>): Promise<boolean> {
    setBusy(true); setError(null);
    try { await action(); await refresh(); await loadDaily(); return true; }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Something went wrong"); return false; }
    finally { setBusy(false); }
  }

  async function switchDemoUser(id: string) {
    if (busy || id === me?.id) return;
    await act(async () => {
      api.setDemoUserId(id); setRun(null); setJobStatus("");
      setHistoryPage(0); setLogPage(0); setCommunityPage(0); setLedgerPage(0);
    });
  }

  async function findLunch() {
    setBusy(true); setError(null); setJobStatus("Preparing your suggestions…");
    try {
      const queued = await api.startRecommendationJob({ meal_slot: "lunch", limit: 3 });
      for (let attempt = 0; attempt < 30; attempt++) {
        const job = await api.recommendationJob(queued.id);
        setJobStatus(job.status === "claimed" ? "Looking at your options…" : `Recommendation ${job.status}`);
        if (job.status === "completed" && job.run) {
          setRun(job.run); setJobStatus(""); await refresh(); return;
        }
        if (job.status === "failed") throw new Error(`Recommendation failed: ${job.error ?? "worker error"}`);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      throw new Error("Recommendation is still processing. Check the worker and try again.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Something went wrong");
      setJobStatus("");
    } finally { setBusy(false); }
  }

  async function planMeal(item: MenuItemRead, recommendationId?: string) {
    const okay = await act(() => api.decide({ menu_item_id: item.id, recommendation_id: recommendationId ?? null }));
    if (okay) { setHistoryMode("decisions"); setHistoryPage(0); navigate("history"); }
  }

  function switchFoodMode(mode: FoodMode) {
    setFoodMode(mode);
    const url = new URL(window.location.href);
    url.searchParams.set("page", mode === "recommend" ? "for-you" : "discover");
    window.history.pushState({ page: "food" }, "", url);
  }

  const venueName = (id: string) => venues.find(venue => venue.id === id)?.name ?? "Campus kitchen";
  const summaryDate = summary?.date ?? hongKongDate(new Date());
  const summaryWorkoutSessions = workoutSessions.filter(session => hongKongDate(session.completed_at) === summaryDate);
  const todayWorkoutMinutes = summaryWorkoutSessions.reduce((total, session) => total + session.duration_min, 0);
  const summaryWorkoutCount = summaryWorkoutSessions.length;
  const progressPeriod = selectedDate ? "for this day" : "today";

  return <AppShell screen={screen} me={me} busy={busy} rewardBalance={rewards?.balance ?? 0}
    onNavigate={navigate} onSwitchUser={switchDemoUser}>
    {error && <div role="alert" className="nl-alert">{error}</div>}

    {screen === "today" && <TodaySection mealCount={summary?.meal_count ?? 0}
      workoutMinutes={todayWorkoutMinutes} onNavigate={navigate} onAction={navigate} />}

    {screen === "food" && <>
      <div className="nl-discover-tabs" role="tablist" aria-label="Food mode">
        <button role="tab" aria-selected={foodMode === "explore"} onClick={() => switchFoodMode("explore")}>Explore</button>
        <button role="tab" aria-selected={foodMode === "recommend"} onClick={() => switchFoodMode("recommend")}>For you</button>
      </div>
      {foodMode === "recommend" ? <>
        <div className="nl-page-intro"><span className="nl-eyebrow">FOR YOU / DECIDE</span>
          <h1>A good option for right now<span className="nl-orange-dot">.</span></h1>
          <p>Suggestions use your saved goal, preferences and the available demo menu.</p></div>
        <div className="nl-context"><span>YOUR CONTEXT</span><strong>{me?.goal.goal.replaceAll("_", " ") ?? "Your goal"}</strong>
          <p>Lunch · Fictional campus options · Nutrition is estimated</p>
          <button className="nl-text-link" onClick={() => navigate("profile")}>Change your context →</button></div>
        <div className="nl-recommend-action"><div><h2>Suggested for you</h2><p>Your choice, always. You can plan a meal or keep exploring.</p></div>
          <button className="nl-button nl-button-primary" disabled={busy || !me} onClick={() => void findLunch()}>
            {busy ? "Finding options…" : run ? "Refresh suggestions" : "Find my lunch"}</button></div>
        {jobStatus && <div role="status" className="nl-status">{jobStatus}</div>}
        {run ? run.recommendations.length ? <div className="nl-food-grid">{run.recommendations.map((choice, index) =>
          <FoodCard key={choice.id} item={choice.menu_item} venue={venueName(choice.menu_item.venue_id)}
            recommendation={choice} featured={index === 0} busy={busy}
            onPlan={() => void planMeal(choice.menu_item, choice.id)} />)}</div> :
          <div className="nl-empty">No meals meet your saved dietary restrictions. Check your profile and try again.</div> :
          <div className="nl-placeholder-card"><span className="nl-placeholder-spark">✦</span>
            <h3>A recommendation with a reason.</h3><p>Tap “Find my lunch” to see a ranked meal and why it fits your current context.</p></div>}
        <div className="nl-assurance"><span>✦</span><div><strong>Your call, always</strong><p>Suggestions help you decide. Only meals you confirm count toward your intake and habits.</p></div></div>
        <button className="nl-button nl-button-soft" onClick={() => navigate("workouts")}>Explore a workout suggestion →</button>
      </> : <>
        <div className="nl-page-intro"><span className="nl-eyebrow">FOOD / EXPLORE</span>
          <h1>Find your lunch<span className="nl-orange-dot">.</span></h1>
          <p>Campus choices, made a little easier. Explore real places and keep track of the meals you choose.</p></div>
        <div className="nl-discover-tabs" role="tablist" aria-label="Discover category">
          <button role="tab" aria-selected={browseMode === "meals"} onClick={() => setBrowseMode("meals")}>Meals</button>
          <button role="tab" aria-selected={browseMode === "places"} onClick={() => setBrowseMode("places")}>Real places</button>
        </div>
        {browseMode === "places" ? <PlacesSection /> : <>
          <div className="nl-discover-tabs" role="tablist" aria-label="Photo check-in mode">
            <button role="tab" aria-selected={photoMode === "instant"} onClick={() => setPhotoMode("instant")}>Instant nutrition</button>
            <button role="tab" aria-selected={photoMode === "background"} onClick={() => setPhotoMode("background")}>Background AI review</button>
          </div>
          {photoMode === "instant" ? <PhotoAnalyzer key={me?.id} onConfirmed={async () => {
            setPhotoPage(0); setHistoryMode("photos"); await refresh(); navigate("history");
          }} /> : <MealCheckinCard key={me?.id} onCompleted={refresh} />}
          <details className="nl-progressive">
            <summary>Browse all meals and places</summary>
            <div className="nl-progressive-body">
              <p className="nl-directory-note">These six example meals are fictional and support the recommendation and logging flow. Browse Real places for sourced restaurant listings.</p>
              <form className="nl-search" onSubmit={event => { event.preventDefault(); setMenuPage(0); setSearch(searchDraft.trim()); }}>
                <span aria-hidden="true">⌕</span>
                <input aria-label="Search food or places" placeholder="Search food or places" value={searchDraft}
                  onChange={event => setSearchDraft(event.target.value)} />
                <button type="submit">Search</button>
              </form>
              <div className="nl-filter-row" aria-label="Food filters">
                {([ ["all", "All meals"], ["vegan", "Vegan"], ["high_protein", "High protein"], ["under_50", "Under HK$50"] ] as const).map(([id, label]) =>
                  <button key={id} className="nl-chip" data-active={filter === id} onClick={() => { setFilter(id); setMenuPage(0); }}>{label}</button>)}
              </div>
              <div className="nl-section-heading"><div><span className="nl-eyebrow">AROUND CAMPUS</span><h2>Food worth a look</h2></div>
                <button className="nl-text-link" onClick={() => switchFoodMode("recommend")}>Get a suggestion →</button></div>
              {menu.length ? <div className="nl-food-grid">{menu.map((item, index) =>
                <FoodCard key={item.id} item={item} venue={venueName(item.venue_id)} featured={index === 0 && menuPage === 0}
                  busy={busy} onPlan={() => void planMeal(item)} />)}</div> :
                <div className="nl-empty">No meals match this search. Try another food or filter.</div>}
              <Pager page={menuPage} hasNext={menuHasNext} onChange={setMenuPage} label="food" />
              <div className="nl-discover-community"><div><span className="nl-eyebrow">FROM THE COMMUNITY</span>
                <h2>What students are sharing</h2><p>Meals and tips from other students, in their own words.</p></div>
                <button className="nl-button nl-button-soft" onClick={() => navigate("community")}>Browse posts →</button></div>
              {posts[0] && <button className="nl-preview-post" onClick={() => navigate("community")}>
                <span className="nl-mini-avatar">{posts[0].author_display_name.slice(0, 1)}</span>
                <span><strong>{posts[0].author_display_name}</strong><small>{posts[0].caption}</small></span><b aria-hidden="true">→</b>
              </button>}
            </div>
          </details>
        </>}
      </>}
    </>}

    {screen === "workouts" && <WorkoutSection key={me?.id} onCompleted={refresh} />}

    {screen === "history" && <>
      <div className="nl-page-intro"><span className="nl-eyebrow">HISTORY / REMEMBER</span>
        <h1>Your choices, in one place<span className="nl-orange-dot">.</span></h1>
        <p>A lasting record of plans and meals you actually confirmed.</p></div>
      <section className="nl-summary-card"><div className="nl-summary-top"><div><span className="nl-eyebrow">THIS WEEK</span>
        <h2>{summary ? new Date(`${summary.date}T12:00:00Z`).toLocaleDateString("en", { month: "long", year: "numeric", timeZone: "UTC" }) : "Your week"}</h2></div>
        {selectedDate && <button className="nl-text-link" onClick={() => setSelectedDate(null)}>Today</button>}</div>
        {summary && <div className="nl-week">{weekDays(summary.date).map(day =>
          <button key={day} data-active={day === summary.date} onClick={() => setSelectedDate(day)}
            aria-label={`Show summary for ${day}`}><small>{new Date(`${day}T12:00:00Z`).toLocaleDateString("en", { weekday: "short", timeZone: "UTC" })}</small>
            <strong>{Number(day.slice(-2))}</strong></button>)}</div>}
        <p className="nl-summary-sentence">{summary?.meal_count ?? 0} confirmed meal{(summary?.meal_count ?? 0) === 1 ? "" : "s"} and {summaryWorkoutCount} completed workout{summaryWorkoutCount === 1 ? "" : "s"} {progressPeriod}.</p>
        <p className="nl-summary-foot">Totals include recorded menu estimates and photo meals with confirmed USDA matches and grams. Unestimated meals add no nutrition values.</p>
      </section>
      <DailyCoachReport key={me?.id} />
      <div className="nl-section-heading"><div><span className="nl-eyebrow">YOUR RECORD</span><h2>Saved choices</h2></div></div>
      <div className="nl-segmented" role="tablist" aria-label="History type">
        <button role="tab" aria-selected={historyMode === "decisions"} onClick={() => setHistoryMode("decisions")}>Decisions</button>
        <button role="tab" aria-selected={historyMode === "meals"} onClick={() => setHistoryMode("meals")}>Menu meals</button>
        <button role="tab" aria-selected={historyMode === "photos"} onClick={() => setHistoryMode("photos")}>Photo meals</button>
      </div>
      {historyMode === "decisions" ? <>
        <div className="nl-history-list">{decisions.length ? decisions.map(decision =>
          <article key={decision.id} className="nl-history-row"><span className="nl-history-icon">◒</span>
            <div><strong>{decision.menu_item.name}</strong><small>{venueName(decision.menu_item.venue_id)} · {new Date(decision.created_at).toLocaleDateString()}</small></div>
            <span className={`nl-status-pill ${decision.status}`}>{decision.status}</span>
            {decision.status === "planned" && <button className="nl-button nl-button-primary" disabled={busy}
              onClick={() => void act(() => api.logMeal({ decision_id: decision.id, servings: 1 }))}>I ate this meal</button>}</article>) :
              <div className="nl-empty">No plans yet. Explore food and save one you like.</div>}</div>
        <Pager page={historyPage} hasNext={historyHasNext} onChange={setHistoryPage} label="decisions" />
      </> : historyMode === "meals" ? <>
        <div className="nl-history-list">{historyLogs.length ? historyLogs.map(log =>
          <article key={log.id} className="nl-history-row"><span className="nl-history-icon">✓</span>
            <div><strong>{log.menu_item.name}</strong><small>{new Date(log.consumed_at).toLocaleDateString()} · {log.servings} serving</small></div>
            <span className="nl-history-kcal">≈ {log.nutrition.calories_kcal} kcal</span></article>) :
              <div className="nl-empty">Confirmed meals will appear here after you log them.</div>}</div>
        <Pager page={logPage} hasNext={logHasNext} onChange={setLogPage} label="meal logs" />
      </> : <>
        <div className="nl-history-list">{photoMeals.length ? photoMeals.map(record =>
          <article key={record.id} className="nl-history-row"><span className="nl-history-icon">◒</span>
            <div><strong>{record.foods.length ? record.foods.map(food => food.name).join(", ") : "Photo review"}</strong>
              <small>{new Date(record.consumed_at).toLocaleDateString()} · Photo meal record</small>
              {record.notes && <small>{record.notes}</small>}
              {record.review_status === "pending" || record.review_status === "processing" ? <small>AI review in progress. This meal is not counted yet.</small> : null}
              {record.review_status === "failed" && <small>{record.review_error ?? "Photo review failed"}</small>}
              {record.review_status !== "failed" && record.review_status !== "pending" && record.review_status !== "processing" && record.nutrition_status === "none" && <small>{record.ai_review?.estimated_nutrition
                ? "USDA match unavailable; AI visual nutrition is shown below."
                : "This older record has no nutrition result. Its original photo was not stored; re-upload it to estimate nutrition."}</small>}
              {record.nutrition && <div className="nl-photo-history-nutrition">
              {record.nutrition_status === "partial" && <small>Matched foods only · excluded ingredients are not counted</small>}
              <small>Protein {record.nutrition.protein_g} g · Carbs {record.nutrition.carbs_g} g · Fat {record.nutrition.fat_g} g</small>
              {(record.nutrition_items ?? []).map(item => <a key={item.fdc_id + item.name} href={item.source_url} target="_blank" rel="noreferrer">
                {item.name}: {item.grams} g · USDA {item.fdc_id} ↗</a>)}
              {(record.unresolved_foods?.length ?? 0) > 0 && record.nutrition_status === "partial" &&
                <small>Not counted: {(record.unresolved_foods ?? []).join(", ")}</small>}
              </div>}</div>
            {record.ai_review?.estimated_nutrition && <div className="nl-photo-history-nutrition">
              <small>AI visual estimate: ≈ {record.ai_review.estimated_nutrition.calories_kcal} kcal</small>
              <small>Protein {record.ai_review.estimated_nutrition.protein_g} g · Carbs {record.ai_review.estimated_nutrition.carbs_g} g · Fat {record.ai_review.estimated_nutrition.fat_g} g</small>
              <small>Unverified; not included in daily totals</small></div>}
            <span className="nl-status-pill">{record.review_status === "pending" || record.review_status === "processing" ? record.review_status : record.review_status === "failed" ? "Review failed" : record.nutrition
              ? `${record.nutrition_status === "partial" ? "Partial · " : "≈ "}${record.nutrition.calories_kcal} kcal`
              : record.ai_review?.estimated_nutrition ? `AI ≈ ${record.ai_review.estimated_nutrition.calories_kcal} kcal` : "No nutrition estimate"}</span>
            {record.review_status === "failed" && (record.review_attempts ?? 0) < 3 && <button className="nl-button nl-button-soft" onClick={() => void act(() => api.retryPhotoReview(record.id))}>Retry review</button>}
            {(record.review_status === "failed" || record.review_status === "pending") && <button className="nl-text-link" onClick={() => void act(() => api.deletePhotoReview(record.id))}>Remove photo</button>}
            {record.review_status === "not_requested" && record.nutrition_status === "none" && !record.ai_review?.estimated_nutrition && <button className="nl-button nl-button-soft"
              onClick={() => { setBrowseMode("meals"); setPhotoMode("instant"); navigate("food"); }}>Re-upload photo</button>}</article>) :
            <div className="nl-empty">No photo meals yet. Recognize one from Discover, then confirm what you ate.</div>}</div>
        <Pager page={photoPage} hasNext={photoHasNext} onChange={setPhotoPage} label="photo meals" />
      </>}
      <div className="nl-assurance"><span>↗</span><div><strong>Your tree is growing</strong>
        <p>Confirmed choices build your habit progress. Planned meals stay separate from what you ate.</p></div></div>
    </>}

    {screen === "community" && <CommunitySection key={me?.id} posts={posts} mealLogs={mealLogs}
      sharedMealLogIds={sharedMealLogIds} reports={reports} isModerator={me?.is_moderator ?? false}
      busy={busy} onAction={act} page={communityPage} hasNext={communityHasNext} onPageChange={setCommunityPage} />}
    {screen === "rewards" && <RewardsSection overview={rewards} busy={busy} onAction={act}
      onNavigate={navigate} ledgerPage={ledgerPage} ledgerHasNext={ledgerHasNext} onLedgerPageChange={setLedgerPage} />}
    {screen === "profile" && <ProfileView me={me} busy={busy} onAction={async action => {
      const okay = await act(action);
      if (okay) setRun(null);
      return okay;
    }} />}
    <footer className="nl-footer">Fictional campus menu · Illustrative nutrition estimates · Demo credits have no cash value</footer>
  </AppShell>;
}
