"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@nourishloop/api-client";
import type {
  CommunityPostRead, CommunityReportRead, DailySummary, DecisionRead, MeRead,
  MealLogRead, MenuItemRead, RecommendationRunRead, RewardOverviewRead, VenueRead,
  PhotoMealRead, PlanProgressRead, WorkoutPlanRead,
} from "@nourishloop/api-client/schema";
import AppShell, { type Screen } from "./AppShell";
import CommunitySection from "./CommunitySection";
import FoodCard from "./FoodCard";
import Pager from "./Pager";
import PlacesSection from "./PlacesSection";
import PublishedMenus from "./PublishedMenus";
import PhotoAnalyzer from "./PhotoAnalyzer";
import PlanProgressCard from "./PlanProgressCard";
import MealCheckinCard from "./MealCheckinCard";
import ProfileView from "./ProfileView";
import RewardsSection from "./RewardsSection";
import WorkoutSection from "./WorkoutSection";
import WorkoutHistory from "./WorkoutHistory";
import WorkoutPlanCard from "./WorkoutPlanCard";
import useAutomaticSuggestion from "./useAutomaticSuggestion";

const MENU_SIZE = 4;
const LIST_SIZE = 5;
const COMMUNITY_SIZE = 4;
const SCREENS: Screen[] = ["discover", "workouts", "for-you", "history", "community", "rewards", "profile"];
type Filter = "all" | "vegan" | "high_protein" | "under_50";

function screenFromUrl(): Screen {
  const value = new URLSearchParams(window.location.search).get("page");
  return SCREENS.find(screen => screen === value) ?? "for-you";
}

async function loadMealSuggestion(signal: AbortSignal): Promise<RecommendationRunRead> {
  const queued = await api.startRecommendationJob({ meal_slot: "lunch", limit: 3 });
  for (let attempt = 0; attempt < 30; attempt++) {
    signal.throwIfAborted();
    const job = await api.recommendationJob(queued.id);
    if (job.status === "completed" && job.run) return job.run;
    if (job.status === "failed") throw new Error(job.error ?? "Could not find a meal suggestion.");
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  throw new Error("The meal suggestion is taking longer than expected.");
}

const hkDay = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Hong_Kong", dateStyle: "short" });

async function loadWorkoutSuggestion(signal: AbortSignal): Promise<WorkoutPlanRead | null> {
  const [latest] = await api.workoutSessions(1);
  if (latest && hkDay.format(new Date(latest.completed_at)) === hkDay.format(new Date())) return null;
  signal.throwIfAborted();
  return api.recommendWorkout({});
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
  const [screen, setScreen] = useState<Screen>("for-you");
  const [discoverMode, setDiscoverMode] = useState<"food" | "places" | "menus">("food");
  const [menuVenue, setMenuVenue] = useState<VenueRead | null>(null);
  const [photoMode, setPhotoMode] = useState<"instant" | "background">("instant");
  const [me, setMe] = useState<MeRead | null>(null);
  const [venues, setVenues] = useState<VenueRead[]>([]);
  const [menu, setMenu] = useState<MenuItemRead[]>([]);
  const [menuPage, setMenuPage] = useState(0);
  const [menuHasNext, setMenuHasNext] = useState(false);
  const [searchDraft, setSearchDraft] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [decisions, setDecisions] = useState<DecisionRead[]>([]);
  const [historyPage, setHistoryPage] = useState(0);
  const [historyHasNext, setHistoryHasNext] = useState(false);
  const [historyMode, setHistoryMode] = useState<"decisions" | "meals" | "photos" | "workouts">("decisions");
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
  const [planProgress, setPlanProgress] = useState<PlanProgressRead | null>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const refreshGeneration = useRef(0);
  const suggestionKey = me && planProgress ? `${me.id}:${planProgress.today}` : undefined;
  const mealKey = suggestionKey && planProgress ? `${suggestionKey}:${planProgress.recent_meal_count}` : undefined;
  const plannedMeal = planProgress?.planned_meal;
  const meal = useAutomaticSuggestion(mealKey, screen === "for-you" && !plannedMeal, loadMealSuggestion);
  const workout = useAutomaticSuggestion(
    suggestionKey, screen === "for-you" || screen === "workouts", loadWorkoutSuggestion,
  );

  const navigate = useCallback((next: Screen) => {
    setScreen(next);
    const url = new URL(window.location.href);
    if (next === "for-you") url.searchParams.delete("page");
    else url.searchParams.set("page", next);
    window.history.pushState({ page: next }, "", url);
    window.scrollTo({ top: 0, behavior: "instant" });
  }, []);

  useEffect(() => {
    setScreen(screenFromUrl());
    const onPop = () => setScreen(screenFromUrl());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const refresh = useCallback(async () => {
    const generation = ++refreshGeneration.current;
    const tag = filter === "vegan" || filter === "high_protein" ? filter : undefined;
    const maxPriceHkd = filter === "under_50" ? 50 : undefined;
    const [person, places, items, plans, totals, logs, pagedLogs, feed, progress, sharedIds, photoRecords, plan] = await Promise.all([
      api.me(), api.venues(), api.menuItems({
        limit: MENU_SIZE + 1, offset: menuPage * MENU_SIZE, q: search, tag, maxPriceHkd,
      }),
      api.decisions(LIST_SIZE + 1, historyPage * LIST_SIZE), api.summary(selectedDate ?? undefined),
      api.mealLogs(100), api.mealLogs(LIST_SIZE + 1, logPage * LIST_SIZE),
      api.communityPosts(COMMUNITY_SIZE + 1, communityPage * COMMUNITY_SIZE),
      api.rewardOverview(LIST_SIZE + 1, ledgerPage * LIST_SIZE), api.sharedMealLogIds(),
      api.photoMeals(LIST_SIZE + 1, photoPage * LIST_SIZE), api.planProgress(),
    ]);
    if (generation !== refreshGeneration.current) return;
    setMe(person); setVenues(places);
    setMenu(items.slice(0, MENU_SIZE)); setMenuHasNext(items.length > MENU_SIZE);
    setDecisions(plans.slice(0, LIST_SIZE)); setHistoryHasNext(plans.length > LIST_SIZE);
    setSummary(totals); setMealLogs(logs);
    setPlanProgress(plan);
    setHistoryLogs(pagedLogs.slice(0, LIST_SIZE)); setLogHasNext(pagedLogs.length > LIST_SIZE);
    setPosts(feed.slice(0, COMMUNITY_SIZE)); setCommunityHasNext(feed.length > COMMUNITY_SIZE);
    setRewards({ ...progress, transactions: progress.transactions.slice(0, LIST_SIZE) });
    setLedgerHasNext(progress.transactions.length > LIST_SIZE);
    setSharedMealLogIds(sharedIds);
    setPhotoMeals(photoRecords.slice(0, LIST_SIZE)); setPhotoHasNext(photoRecords.length > LIST_SIZE);
    const pendingReports = person.is_moderator ? await api.pendingReports() : [];
    if (generation === refreshGeneration.current) setReports(pendingReports);
  }, [communityPage, filter, historyPage, ledgerPage, logPage, menuPage, photoPage, search, selectedDate]);

  useEffect(() => { refresh().catch((cause: Error) => setError(cause.message)); }, [refresh]);

  useEffect(() => {
    const today = planProgress?.today;
    if (!today) return;
    const afterDateChange = () => {
      if (hkDay.format(new Date()) !== hkDay.format(new Date(`${today}T12:00:00Z`))) {
        void refresh().catch((cause: Error) => setError(cause.message));
      }
    };
    window.addEventListener("focus", afterDateChange);
    return () => window.removeEventListener("focus", afterDateChange);
  }, [planProgress?.today, refresh]);

  useEffect(() => {
    if (screen !== "history" || historyMode !== "photos" ||
        !photoMeals.some(record => record.review_status === "pending" || record.review_status === "processing")) return;
    const timer = window.setInterval(() => { void refresh().catch(() => {}); }, 3000);
    return () => window.clearInterval(timer);
  }, [screen, historyMode, photoMeals, refresh]);

  async function act(action: () => Promise<unknown>): Promise<boolean> {
    setBusy(true); setError(null);
    try { await action(); await refresh(); return true; }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Something went wrong"); return false; }
    finally { setBusy(false); }
  }

  async function planMeal(item: MenuItemRead, recommendationId?: string) {
    const okay = await act(() => api.decide({ menu_item_id: item.id, recommendation_id: recommendationId ?? null }));
    if (okay && screen !== "for-you") navigate("for-you");
  }

  async function confirmMeal(id: string) {
    await act(() => api.logMeal({ decision_id: id, servings: 1 }));
  }

  const venueName = (id: string) => venues.find(venue => venue.id === id)?.name ?? "Campus kitchen";
  const [topMeal, ...otherMeals] = meal.result?.value?.recommendations ?? [];
  const mealContext = meal.result?.value?.history_context;
  const mealCard = (choice: NonNullable<typeof topMeal>, featured = false) =>
    <FoodCard key={choice.id} item={choice.menu_item} venue={venueName(choice.menu_item.venue_id)}
      recommendation={choice} featured={featured} busy={busy}
      onPlan={() => void planMeal(choice.menu_item, choice.id)} />;
  const workoutStatus = !workout.result ? <p role="status">Preparing your workout…</p> :
    workout.result.error ? <div role="alert" className="nl-alert">
      {workout.result.error} <button className="nl-text-link" onClick={workout.refresh}>Retry workout</button>
    </div> : workout.result.value === null ? <p className="nl-empty">You already recorded a workout today.</p> : null;

  const followProgress = <PlanProgressCard progress={planProgress} goal={me?.goal.goal}
    onEditGoal={() => navigate("profile")} />;

  return <AppShell screen={screen} me={me} onNavigate={navigate}>
    {error && <div role="alert" className="nl-alert">{error}</div>}

    {screen === "discover" && <>
      <div className="nl-page-intro">
        <h1>Discover food<span className="nl-orange-dot">.</span></h1>
        <p>Browse local menus or add a meal photo to your history.</p></div>
      <div className="nl-discover-tabs" role="tablist" aria-label="Discover category">
        <button role="tab" aria-selected={discoverMode === "menus"} onClick={() => {
          setMenuVenue(null); setDiscoverMode("menus");
        }}>Real menus</button>
        <button role="tab" aria-selected={discoverMode === "food"} onClick={() => setDiscoverMode("food")}>Log a meal</button>
        <button role="tab" aria-selected={discoverMode === "places"} onClick={() => setDiscoverMode("places")}>Real places</button>
        <button role="tab" aria-selected={false} onClick={() => navigate("workouts")}>Workouts</button>
      </div>
      {discoverMode === "menus" ? <PublishedMenus key={menuVenue?.id} venue={menuVenue} /> :
        discoverMode === "places" ? <PlacesSection onViewMenu={place => {
          setMenuVenue(place); setDiscoverMode("menus");
        }} /> : <>
      <div className="nl-discover-tabs" role="tablist" aria-label="Photo check-in mode">
        <button role="tab" aria-selected={photoMode === "instant"} onClick={() => setPhotoMode("instant")}>Instant nutrition</button>
        <button role="tab" aria-selected={photoMode === "background"} onClick={() => setPhotoMode("background")}>Background AI review</button>
      </div>
      {photoMode === "instant" ? <PhotoAnalyzer key={me?.id} onConfirmed={async () => {
        setPhotoPage(0); setHistoryMode("photos"); await refresh(); navigate("history");
      }} /> : <MealCheckinCard key={me?.id} onCompleted={refresh} />}
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
          <button className="nl-text-link" onClick={() => navigate("for-you")}>See my plan →</button></div>
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
      </>}
    </>}

    {screen === "workouts" && me && <WorkoutSection key={me.id}
      automaticPlan={workout.result?.value} automaticStatus={workoutStatus}
      onViewHistory={() => { setHistoryMode("workouts"); navigate("history"); }}
      onProfileSaved={workout.refresh} onCompleted={async () => { workout.refresh(); await refresh(); }} />}

    {screen === "for-you" && <>
      <div className="nl-page-intro"><h1>My plan<span className="nl-orange-dot">.</span></h1>
        <p>Build a routine around your goal. Your confirmed meals and workouts inform what comes next.</p></div>
      {followProgress}
      <div className="nl-section-heading"><h2>Today’s plan</h2>
        <button className="nl-text-link" onClick={() => navigate("history")}>Progress &amp; history →</button></div>
      <section aria-label="Meal plan">
        <div className="nl-recommend-action"><div><h3>{plannedMeal ? "Meal planned" : "Next meal suggestion"}</h3>
          <p>Fictional campus menu with estimated nutrition.</p></div>
          <div className="nl-place-links">
            <button className="nl-text-link" onClick={() => {
              setDiscoverMode("food"); setPhotoMode("instant"); navigate("discover");
            }}>Log a meal photo</button>
            <button className="nl-text-link" onClick={() => {
              setMenuVenue(null); setDiscoverMode("menus"); navigate("discover");
            }}>Browse nearby menus</button>
          </div></div>
        {!!planProgress?.meals_today && <p className="nl-plan-outcome" role="status">
          {planProgress.meals_today} {planProgress.meals_today === 1 ? "meal" : "meals"} confirmed today.
        </p>}
        {plannedMeal ? <article className="nl-history-row">
          <span className="nl-history-icon" aria-hidden="true">◒</span>
          <div><strong>{plannedMeal.menu_item.name}</strong><small>Confirm this meal after you eat it.</small></div>
          <button className="nl-button nl-button-primary" disabled={busy}
            onClick={() => void confirmMeal(plannedMeal.id)}>I ate this meal</button>
        </article> : !meal.result ? <p role="status">Finding a meal for you…</p> :
          meal.result.error ? <div role="alert" className="nl-alert">{meal.result.error}{" "}
            <button className="nl-text-link" onClick={meal.refresh}>Retry meal suggestion</button></div> :
          topMeal ? <>
            {mealContext && <div className="nl-history-context">
              <strong>How your history shaped this</strong>
              <p>{mealContext.confirmed_meals === 0 ? "Your goal and preferences guide this first set of suggestions."
                : `In the last 7 days, you confirmed ${mealContext.confirmed_meals} ${mealContext.confirmed_meals === 1 ? "meal" : "meals"} over ${mealContext.meal_days} ${mealContext.meal_days === 1 ? "day" : "days"}.`}</p>
              {mealContext.repeated_dishes.length > 0 && <p>
                You logged {mealContext.repeated_dishes.join(", ")} on multiple days. The ranking gives other eligible dishes a boost for variety.
              </p>}
            </div>}
            <div className="nl-food-grid">{mealCard(topMeal, true)}</div>
          </> :
          <div className="nl-empty">No meals on the demo menu match your saved dietary requirements and budget.</div>}
        {!plannedMeal && otherMeals.length > 0 && <details className="nl-suggestion-options">
          <summary>See other meal options</summary><div className="nl-food-grid">{otherMeals.map(choice => mealCard(choice))}</div>
        </details>}
      </section>
      <section aria-label="Workout suggestion">
        <div className="nl-recommend-action"><div><h3>Today’s workout</h3><p>Training history helps choose the next focus.</p></div></div>
        {workoutStatus}
        {workout.result?.value && <WorkoutPlanCard plan={workout.result.value} compact>
          <button className="nl-button nl-button-primary" onClick={() => navigate("workouts")}>View workout plan</button>
        </WorkoutPlanCard>}
        {!workout.result?.value && <button className="nl-text-link" onClick={() => navigate("workouts")}>Open workouts</button>}
      </section>
    </>}

    {screen === "history" && <>
      <div className="nl-page-intro">
        <h1>Progress &amp; history<span className="nl-orange-dot">.</span></h1>
        <p>See the meals and workouts that shaped your plan.</p>
        <button className="nl-text-link" onClick={() => navigate("for-you")}>See today’s plan →</button></div>
      {followProgress}
      <section className="nl-summary-card nl-daily-progress"><div className="nl-summary-top"><div><span className="nl-eyebrow">DAILY MEAL SUMMARY</span>
        <h2>{summary ? new Date(`${summary.date}T12:00:00Z`).toLocaleDateString("en", { month: "long", year: "numeric", timeZone: "UTC" }) : "Your week"}</h2></div>
        {selectedDate && <button className="nl-text-link" onClick={() => setSelectedDate(null)}>Today</button>}</div>
        {summary && <div className="nl-week">{weekDays(summary.date).map(day =>
          <button key={day} data-active={day === summary.date} onClick={() => setSelectedDate(day)}
            aria-label={`Show summary for ${day}`}><small>{new Date(`${day}T12:00:00Z`).toLocaleDateString("en", { weekday: "short", timeZone: "UTC" })}</small>
            <strong>{Number(day.slice(-2))}</strong></button>)}</div>}
        <div className="nl-summary-stats"><div><strong>{summary?.meal_count ?? 0}</strong><span>confirmed meals</span></div>
          <div><strong>{summary?.totals.calories_kcal ?? 0}</strong><span>estimated kcal</span></div>
          <div><strong>{summary?.totals.protein_g ?? 0}g</strong><span>estimated protein</span></div></div>
        <p className="nl-summary-foot">Totals include recorded menu estimates and photo meals with confirmed USDA matches and grams. Unestimated meals add no nutrition values.</p>
      </section>
      <div className="nl-section-heading"><h2>Activity records</h2></div>
      <div className="nl-segmented" role="tablist" aria-label="History type">
        <button role="tab" aria-selected={historyMode === "decisions"} onClick={() => setHistoryMode("decisions")}>Meal plans</button>
        <button role="tab" aria-selected={historyMode === "meals"} onClick={() => setHistoryMode("meals")}>Menu meals</button>
        <button role="tab" aria-selected={historyMode === "photos"} onClick={() => setHistoryMode("photos")}>Photo meals</button>
        <button role="tab" aria-selected={historyMode === "workouts"} onClick={() => setHistoryMode("workouts")}>Training</button>
      </div>
      {historyMode === "decisions" ? <>
        <div className="nl-history-list">{decisions.length ? decisions.map(decision =>
          <article key={decision.id} className="nl-history-row"><span className="nl-history-icon">◒</span>
            <div><strong>{decision.menu_item.name}</strong><small>{venueName(decision.menu_item.venue_id)} · {new Date(decision.created_at).toLocaleDateString()}</small></div>
            <span className={`nl-status-pill ${decision.status}`}>{decision.status}</span>
            {decision.status === "planned" && <button className="nl-button nl-button-primary" disabled={busy}
              onClick={() => void confirmMeal(decision.id)}>I ate this meal</button>}</article>) :
              <div className="nl-empty">No plans yet. Explore food and save one you like.</div>}</div>
        <Pager page={historyPage} hasNext={historyHasNext} onChange={setHistoryPage} label="decisions" />
      </> : historyMode === "meals" ? <>
        <div className="nl-history-list">{historyLogs.length ? historyLogs.map(log =>
          <article key={log.id} className="nl-history-row"><span className="nl-history-icon">✓</span>
            <div><strong>{log.menu_item.name}</strong><small>{new Date(log.consumed_at).toLocaleDateString()} · {log.servings} serving</small></div>
            <span className="nl-history-kcal">≈ {log.nutrition.calories_kcal} kcal</span></article>) :
              <div className="nl-empty">Confirmed meals will appear here after you log them.</div>}</div>
        <Pager page={logPage} hasNext={logHasNext} onChange={setLogPage} label="meal logs" />
      </> : historyMode === "workouts" ? <WorkoutHistory key={me?.id} /> : <>
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
              onClick={() => { setDiscoverMode("food"); setPhotoMode("instant"); navigate("discover"); }}>Re-upload photo</button>}</article>) :
            <div className="nl-empty">No photo meals yet. Recognize one from Discover, then confirm what you ate.</div>}</div>
        <Pager page={photoPage} hasNext={photoHasNext} onChange={setPhotoPage} label="photo meals" />
      </>}
    </>}

    {screen === "community" && <CommunitySection key={me?.id} posts={posts} mealLogs={mealLogs}
      sharedMealLogIds={sharedMealLogIds} reports={reports} isModerator={me?.is_moderator ?? false}
      busy={busy} onAction={act} page={communityPage} hasNext={communityHasNext} onPageChange={setCommunityPage} />}
    {screen === "rewards" && <RewardsSection overview={rewards} busy={busy} onAction={act}
      onNavigate={navigate} ledgerPage={ledgerPage} ledgerHasNext={ledgerHasNext} onLedgerPageChange={setLedgerPage} />}
    {screen === "profile" && (me ? <ProfileView key={me.id} me={me} busy={busy} onAction={act}
      onMealSettingsSaved={meal.refresh} onTrainingSettingsSaved={workout.refresh} /> :
      <p role="status">Loading profile…</p>)}
    <footer className="nl-footer">Fictional campus menu · Illustrative nutrition estimates · Demo credits have no cash value</footer>
  </AppShell>;
}
