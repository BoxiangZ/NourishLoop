import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { DailySummary, DecisionRead, MenuItemRead } from "@nourishloop/api-client/schema";
import Dashboard from "./Dashboard";

const apiMock = vi.hoisted(() => ({
  setDemoUserId: vi.fn(), me: vi.fn(), updateProfile: vi.fn(), updateGoals: vi.fn(),
  venues: vi.fn(), menuItems: vi.fn(), decisions: vi.fn(), summary: vi.fn(),
  startRecommendationJob: vi.fn(), recommendationJob: vi.fn(),
  decide: vi.fn(), logMeal: vi.fn(), mealLogs: vi.fn(),
  analyzePhoto: vi.fn(), recordPhotoMeal: vi.fn(), photoMeals: vi.fn(),
  communityPosts: vi.fn(), shareMeal: vi.fn(), deletePost: vi.fn(),
  comment: vi.fn(), deleteComment: vi.fn(), likePost: vi.fn(), unlikePost: vi.fn(),
  reportPost: vi.fn(), pendingReports: vi.fn(), resolveReport: vi.fn(),
  rewardOverview: vi.fn(), redeemReward: vi.fn(), sharedMealLogIds: vi.fn(),
  externalNotes: vi.fn(), exercises: vi.fn(), workoutProfile: vi.fn(),
  updateWorkoutProfile: vi.fn(), recommendWorkout: vi.fn(), completeWorkout: vi.fn(),
  workoutSessions: vi.fn(), dailyCoachReport: vi.fn(),
}));
vi.mock("@nourishloop/api-client", () => ({ api: apiMock }));

const meal: MenuItemRead = {
  id: "meal-1", venue_id: "venue-1", name: "Chickpea salad",
  description: "Chickpeas and greens", category: "salad", tags: ["vegan"],
  allergen_tags: [], price_hkd: 49, available: true,
  source_label: "NourishLoop fictional demo data", observed_at: null,
  nutrition: { calories_kcal: 470, protein_g: 18, carbs_g: 56, fat_g: 19,
    basis: "per_serving", provenance: "illustrative_estimate", uncertainty_note: "Demo estimate" },
};

let plans: DecisionRead[];
let summary: DailySummary;
let logs: Array<Record<string, unknown>>;
let posts: Array<Record<string, unknown>>;
let reports: Array<Record<string, unknown>>;
let credits: number;
let redeemed: boolean;
let demoUserId: string;

function mainNav() {
  return within(screen.getByRole("navigation", { name: "Main navigation" }));
}

function foodMode() {
  return within(screen.getByRole("tablist", { name: "Food mode" }));
}

function openBrowseDetails() {
  fireEvent.click(screen.getByText("Browse all meals and places"));
}

beforeEach(() => {
  vi.clearAllMocks();
  window.history.replaceState({}, "", "/");
  Object.defineProperty(window, "scrollTo", { value: vi.fn(), configurable: true });
  plans = []; logs = []; posts = []; reports = [];
  credits = 0; redeemed = false; demoUserId = "demo-student";
  summary = { date: "2026-10-24", timezone: "Asia/Hong_Kong", meal_count: 0,
    totals: { calories_kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 } };
  apiMock.setDemoUserId.mockImplementation((id: string) => { demoUserId = id; });
  apiMock.me.mockImplementation(async () => ({
    id: demoUserId, is_moderator: demoUserId === "demo-student",
    profile: { user_id: demoUserId,
      display_name: demoUserId === "demo-student" ? "Demo Student" : "Community Peer",
      dietary_preferences: [], allergies: [] },
    goal: { user_id: demoUserId, goal: "eat_healthier", daily_calorie_target: 1900 },
  }));
  apiMock.venues.mockResolvedValue([{ id: "venue-1", name: "Garden Counter (demo)",
    campus_area: "fictional", is_demo: true, scope: "demo", source_url: null, source_checked_at: null }]);
  apiMock.externalNotes.mockResolvedValue([]);
  const exercise = { id: "exercise-1", name: "Seated row", muscle_group: "back",
    equipment: "machine", difficulty: "beginner", instructions: "Pull with control.",
    source_url: "https://www.acefitness.org/resources/everyone/exercise-library/168/seated-row/" };
  apiMock.exercises.mockResolvedValue([exercise]);
  apiMock.workoutProfile.mockResolvedValue({ user_id: "demo-student", stage: "beginner",
    equipment: ["machine", "bodyweight"], days_per_week: 2 });
  apiMock.updateWorkoutProfile.mockImplementation(async (body) => ({ user_id: demoUserId, ...body }));
  apiMock.recommendWorkout.mockResolvedValue({ id: "plan-1", requested_focus: "back", focus: "back",
    stage: "beginner", minutes: 30, explanation: "This back session fits your beginner stage.",
    explanation_source: "rules", created_at: "2026-10-24T12:00:00Z",
    exercises: [{ exercise, sets: 2, reps: "8–12 controlled reps", rest_seconds: 90 }] });
  apiMock.completeWorkout.mockImplementation(async () => { credits += 5; return { id: "session-1" }; });
  apiMock.workoutSessions.mockResolvedValue([]);
  apiMock.menuItems.mockResolvedValue([meal]);
  apiMock.decisions.mockImplementation(async () => plans);
  apiMock.summary.mockImplementation(async () => summary);
  apiMock.mealLogs.mockImplementation(async () => logs);
  apiMock.photoMeals.mockResolvedValue([]);
  apiMock.dailyCoachReport.mockResolvedValue({
    headline: "A steady day.",
    nutrition_insight: "Two meals are recorded.",
    activity_insight: "One workout is completed.",
    next_actions: ["Choose a balanced dinner."],
    limitations: ["Nutrition values are estimates."],
  });
  apiMock.communityPosts.mockImplementation(async () => posts.map(post => ({
    ...post, is_mine: post.author_id ? post.author_id === demoUserId : post.is_mine,
  })));
  apiMock.pendingReports.mockImplementation(async () => reports);
  apiMock.sharedMealLogIds.mockImplementation(async () => posts.map(post => post.meal_log_id));
  apiMock.rewardOverview.mockImplementation(async () => ({
    balance: credits, suggested_next_step: "Confirm a meal you actually ate.",
    habits: [{ id: "confirm_meal", title: "Log a confirmed meal", description: "Confirm a meal you ate",
      points: 5, completed_today: credits >= 5, streak_days: credits >= 5 ? 1 : 0,
      completed_this_week: credits >= 5 ? 1 : 0, weekly_target: 3 }],
    rewards: [{ id: "starter_badge", title: "Starter badge", description: "Demo badge",
      cost: 5, redeemed }], transactions: [],
  }));
  const run = { id: "run-1", meal_slot: "lunch", scoring_version: "rules-v1",
    recommendations: [{ id: "recommendation-1", rank: 1, score: 0.8,
      explanation: "Fits your approximate meal budget.", confidence: "low",
      confidence_reason: "Demo estimate", menu_item: meal }] };
  apiMock.startRecommendationJob.mockResolvedValue({ id: "job-1", status: "pending", attempts: 0 });
  apiMock.recommendationJob.mockResolvedValue({ id: "job-1", status: "completed", attempts: 1, run });
  apiMock.decide.mockImplementation(async () => {
    const plan: DecisionRead = { id: "decision-1", status: "planned",
      created_at: "2026-10-24T12:00:00Z", menu_item: meal };
    plans = [plan]; return plan;
  });
  apiMock.logMeal.mockImplementation(async () => {
    plans = [{ ...plans[0], status: "confirmed" }];
    summary = { ...summary, meal_count: 1,
      totals: { calories_kcal: 470, protein_g: 18, carbs_g: 56, fat_g: 19 } };
    const log = { id: "log-1", decision_id: "decision-1", servings: 1,
      consumed_at: "2026-10-24T12:30:00Z", nutrition: summary.totals, menu_item: meal };
    logs = [log]; credits += 5; return log;
  });
  apiMock.shareMeal.mockImplementation(async ({ meal_log_id, caption }) => {
    const post = { id: "post-1", author_id: demoUserId, meal_log_id, caption,
      author_display_name: "Demo Student", created_at: "2026-10-24T12:45:00Z",
      meal: logs[0], like_count: 0, liked_by_me: false, is_mine: true, comments: [] };
    posts = [post]; credits += 3; return post;
  });
  apiMock.redeemReward.mockImplementation(async () => {
    credits -= 5; redeemed = true;
    return { id: "redemption-1", reward_id: "starter_badge", cost: 5, balance: credits };
  });
  apiMock.reportPost.mockImplementation(async (id: string, body: { reason: string }) => {
    const report = { id: "report-1", post_id: id, post_caption: "Loved this lunch",
      post_author: "Demo Student", reason: body.reason, detail: null, status: "pending",
      created_at: "2026-10-24T12:50:00Z" };
    reports = [report]; return report;
  });
  apiMock.resolveReport.mockImplementation(async (_id: string, body: { action: string }) => {
    reports = []; if (body.action === "remove") posts = [];
    return { status: body.action === "remove" ? "removed" : "dismissed" };
  });
});

afterEach(cleanup);

describe("NourishLoop app pages", () => {
  it("defaults to the Today focus and remaps legacy food URLs", async () => {
    render(<Dashboard />);
    expect(await screen.findByText("No meals are logged yet today.")).toBeTruthy();

    cleanup();
    window.history.replaceState({}, "", "/?page=discover");
    render(<Dashboard />);
    expect(await screen.findByText("Find your lunch")).toBeTruthy();

    cleanup();
    window.history.replaceState({}, "", "/?page=for-you");
    render(<Dashboard />);
    expect(await screen.findByText("A good option for right now")).toBeTruthy();
  });

  it("refreshes Today when switching demo users", async () => {
    apiMock.summary.mockImplementation(async () => ({
      date: new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Hong_Kong" }),
      timezone: "Asia/Hong_Kong",
      meal_count: demoUserId === "demo-peer" ? 2 : 0,
      totals: { calories_kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 },
    }));
    apiMock.workoutSessions.mockResolvedValue([]);

    render(<Dashboard />);
    expect(await screen.findByText("No meals are logged yet today.")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Demo account"), { target: { value: "demo-peer" } });
    expect(await screen.findByText("Meals are logged; movement is still open.")).toBeTruthy();
  });

  it("loads summary and workout sessions once on Today", async () => {
    render(<Dashboard />);
    expect(await screen.findByText("No meals are logged yet today.")).toBeTruthy();
    expect(apiMock.summary).toHaveBeenCalledTimes(1);
    expect(apiMock.workoutSessions).toHaveBeenCalledTimes(1);
  });

  it("uses the selected summary date for Progress workout counts", async () => {
    const todayHK = new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Hong_Kong" });
    const anchor = new Date(`${todayHK}T12:00:00Z`);
    const selected = new Date(anchor);
    selected.setUTCDate(anchor.getUTCDate() + 1);
    const selectedKey = selected.toISOString().slice(0, 10);

    apiMock.summary.mockImplementation(async (date?: string) => ({
      date: date ?? todayHK,
      timezone: "Asia/Hong_Kong",
      meal_count: 1,
      totals: { calories_kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 },
    }));
    apiMock.workoutSessions.mockResolvedValue([
      { id: "old", plan_id: "plan-1", focus: "back", stage: "beginner", duration_min: 30,
        exercise_names: ["Seated row"], completed_at: `${selectedKey}T02:00:00Z` },
      { id: "now", plan_id: "plan-1", focus: "back", stage: "beginner", duration_min: 60,
        exercise_names: ["Seated row"], completed_at: new Date().toISOString() },
    ]);

    render(<Dashboard />);
    fireEvent.click(mainNav().getByRole("button", { name: "Progress" }));
    expect(await screen.findByText("1 confirmed meal and 1 completed workout today.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: `Show summary for ${selectedKey}` }));
    expect(await screen.findByText("1 confirmed meal and 1 completed workout for this day.")).toBeTruthy();
  });

  it("loads current-day data when navigating from a selected Progress date to Today", async () => {
    const todayHK = new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Hong_Kong" });
    const anchor = new Date(`${todayHK}T12:00:00Z`);
    const selected = new Date(anchor);
    selected.setUTCDate(anchor.getUTCDate() + 1);
    const selectedKey = selected.toISOString().slice(0, 10);

    apiMock.summary.mockImplementation(async (date?: string) => ({
      date: date ?? todayHK,
      timezone: "Asia/Hong_Kong",
      meal_count: date ? 1 : 0,
      totals: { calories_kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 },
    }));
    apiMock.workoutSessions.mockResolvedValue([
      { id: "past", plan_id: "plan-1", focus: "back", stage: "beginner", duration_min: 60,
        exercise_names: ["Seated row"], completed_at: `${selectedKey}T02:00:00Z` },
      { id: "today", plan_id: "plan-1", focus: "back", stage: "beginner", duration_min: 30,
        exercise_names: ["Seated row"], completed_at: new Date().toISOString() },
    ]);

    render(<Dashboard />);
    fireEvent.click(mainNav().getByRole("button", { name: "Progress" }));
    fireEvent.click(await screen.findByRole("button", { name: `Show summary for ${selectedKey}` }));
    expect(await screen.findByText("1 confirmed meal and 1 completed workout for this day.")).toBeTruthy();

    fireEvent.click(mainNav().getByRole("button", { name: "Today" }));
    expect(await screen.findByText("Movement is logged; your next meal is still open.")).toBeTruthy();
    expect(apiMock.summary).toHaveBeenLastCalledWith(undefined);
  });

  it("shows the daily coach report only after navigating to Progress", async () => {
    render(<Dashboard />);

    expect(screen.queryByRole("button", { name: "Generate daily coach report" })).toBeNull();
    fireEvent.click(mainNav().getByRole("button", { name: "Progress" }));
    expect(await screen.findByRole("button", { name: "Generate daily coach report" })).toBeTruthy();
    fireEvent.click(mainNav().getByRole("button", { name: "Food" }));
    expect(screen.queryByRole("button", { name: "Generate daily coach report" })).toBeNull();
  });

  it("shows saved AI calories and macros in photo History when USDA has no match", async () => {
    apiMock.photoMeals.mockResolvedValue([{ id: "photo-ai",
      foods: [{ name: "Rice and tofu" }], notes: "", model: "vision-model",
      consumed_at: "2026-10-28T12:00:00Z", nutrition: null,
      nutrition_status: "none", unresolved_foods: ["No reliable USDA match"],
      review_status: "not_requested", ai_review: { is_food: true,
        detected_foods: ["Rice and tofu"], confidence: 0.55,
        estimated_nutrition: { calories_kcal: 470, protein_g: 18, carbs_g: 60, fat_g: 16 },
        summary: "Rice and tofu", assumptions: ["Portion estimated"], suggestions: [],
      },
    }]);
    render(<Dashboard />);
    fireEvent.click(mainNav().getByRole("button", { name: "Progress" }));
    fireEvent.click(await screen.findByRole("tab", { name: "Photo meals" }));
    expect(await screen.findByText("AI ≈ 470 kcal")).toBeTruthy();
    expect(screen.getByText(/Protein 18 g · Carbs 60 g · Fat 16 g/)).toBeTruthy();
  });

  it("keeps a saved partial photo nutrition estimate visible in History", async () => {
    apiMock.photoMeals.mockResolvedValue([{ id: "photo-partial",
      foods: [{ name: "Egg", preparation: "fried" }, { name: "Sauce" }],
      notes: "", model: "vision-model", consumed_at: "2026-10-28T12:00:00Z",
      nutrition: { calories_kcal: 98, protein_g: 6.8, carbs_g: 0.4, fat_g: 7.4 },
      nutrition_status: "partial", unresolved_foods: ["Sauce"],
      nutrition_items: [{ name: "Egg", fdc_id: 173423, source_description: "Egg, whole, cooked, fried",
        source_url: "https://fdc.nal.usda.gov/food-search/?query=173423", grams: 50,
        portion_basis: "visual_estimate" }],
    }]);
    render(<Dashboard />);
    fireEvent.click(mainNav().getByRole("button", { name: "Progress" }));
    fireEvent.click(await screen.findByRole("tab", { name: "Photo meals" }));
    expect(await screen.findByText("Partial · 98 kcal")).toBeTruthy();
    expect(screen.getByText(/Not counted: Sauce/)).toBeTruthy();
    expect(screen.getByText(/Protein 6.8 g · Carbs 0.4 g · Fat 7.4 g/)).toBeTruthy();
  });

  it("searches and pages food using API offsets", async () => {
    apiMock.menuItems.mockImplementation(async (options: { offset?: number }) =>
      options.offset === 4 ? [{ ...meal, id: "meal-5", name: "Fifth meal" }] :
        Array.from({ length: 5 }, (_, index) => ({
          ...meal, id: `meal-${index + 1}`, name: index ? `Meal ${index + 1}` : meal.name,
        })));
    render(<Dashboard />);
    fireEvent.click(mainNav().getByRole("button", { name: "Food" }));
    openBrowseDetails();
    expect(await screen.findByText("Chickpea salad")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Next food page" }));
    await waitFor(() => expect(apiMock.menuItems).toHaveBeenCalledWith(expect.objectContaining({ offset: 4 })));
    expect(await screen.findByText("Fifth meal")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Vegan" }));
    await waitFor(() => expect(apiMock.menuItems).toHaveBeenCalledWith(expect.objectContaining({ tag: "vegan" })));
    fireEvent.change(screen.getByLabelText("Search food or places"), { target: { value: "salad" } });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() => expect(apiMock.menuItems).toHaveBeenCalledWith(expect.objectContaining({ q: "salad" })));
  });

  it("separates planning, confirmation and reward redemption", async () => {
    render(<Dashboard />);
    fireEvent.click(mainNav().getByRole("button", { name: "Food" }));
    openBrowseDetails();
    expect(await screen.findByText("Chickpea salad")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Plan this meal/ }));
    expect(await screen.findByRole("button", { name: "I ate this meal" })).toBeTruthy();
    expect(summary.meal_count).toBe(0);
    fireEvent.click(screen.getByRole("button", { name: "I ate this meal" }));
    await waitFor(() => expect(apiMock.logMeal).toHaveBeenCalledWith({
      decision_id: "decision-1", servings: 1,
    }));
    fireEvent.click(screen.getByRole("button", { name: "Open rewards store" }));
    expect(await screen.findByText("5")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Redeem 5 credits" }));
    await waitFor(() => expect(apiMock.redeemReward).toHaveBeenCalledWith("starter_badge"));
    expect(await screen.findByRole("button", { name: "Redeemed" })).toBeTruthy();
  });

  it("shows an asynchronous suggestion and shares a confirmed meal", async () => {
    render(<Dashboard />);
    fireEvent.click(mainNav().getByRole("button", { name: "Food" }));
    fireEvent.click(foodMode().getByRole("tab", { name: "For you" }));
    await waitFor(() => expect((screen.getByRole("button", { name: "Find my lunch" }) as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(screen.getByRole("button", { name: "Find my lunch" }));
    expect(await screen.findByText("Fits your approximate meal budget.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Plan this meal/ }));
    fireEvent.click(await screen.findByRole("button", { name: "I ate this meal" }));
    fireEvent.click(mainNav().getByRole("button", { name: "Community" }));
    fireEvent.change(await screen.findByLabelText("Confirmed meal to share"), { target: { value: "log-1" } });
    fireEvent.change(screen.getByLabelText("Community caption"), { target: { value: "Loved this lunch" } });
    fireEvent.click(screen.getByRole("button", { name: "Share meal" }));
    await waitFor(() => expect(apiMock.shareMeal).toHaveBeenCalledWith({
      meal_log_id: "log-1", caption: "Loved this lunch",
    }));
    expect(await screen.findByText("Loved this lunch")).toBeTruthy();
  });

  it("lets the peer report a post and the moderator remove it", async () => {
    apiMock.externalNotes.mockImplementation(async (scope: string) => scope === "hkust" ? [{
      id: "public-note", scope, title: "A linked campus discussion",
      summary: "A paraphrased public opinion.", source_platform: "Reddit",
      source_url: "https://www.reddit.com/r/HKUST/comments/example/", source_checked_at: "2026-10-28",
    }] : []);
    posts = [{ id: "post-1", author_id: "demo-student", meal_log_id: "log-1",
      caption: "Loved this lunch", author_display_name: "Demo Student",
      created_at: "2026-10-24T12:45:00Z", meal: { menu_item: meal,
        nutrition: meal.nutrition }, like_count: 0, liked_by_me: false, comments: [] }];
    render(<Dashboard />);
    fireEvent.click(mainNav().getByRole("button", { name: "Community" }));
    expect(await screen.findByText("Loved this lunch")).toBeTruthy();
    expect(await screen.findByText("A linked campus discussion")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Demo account"), { target: { value: "demo-peer" } });
    fireEvent.click(await screen.findByRole("button", { name: "Report post" }));
    await waitFor(() => expect(apiMock.reportPost).toHaveBeenCalledWith("post-1", { reason: "spam" }));
    fireEvent.change(screen.getByLabelText("Demo account"), { target: { value: "demo-student" } });
    expect(await screen.findByText("Reported for spam")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Remove post" }));
    await waitFor(() => expect(apiMock.resolveReport).toHaveBeenCalledWith("report-1", { action: "remove" }));
    expect(await screen.findByText(/No meals shared on this page/)).toBeTruthy();
  });

  it("pages the credit ledger with server offsets", async () => {
    apiMock.rewardOverview.mockImplementation(async (_limit: number, offset: number) => ({
      balance: 12, suggested_next_step: "Keep going", habits: [], rewards: [],
      transactions: offset === 5
        ? [{ id: "credit-6", amount: 3, reason: "share_meal", created_at: "2026-10-24T12:00:00Z" }]
        : Array.from({ length: 6 }, (_, index) => ({
          id: `credit-${index}`, amount: 5, reason: "confirm_meal", created_at: "2026-10-24T12:00:00Z",
        })),
    }));
    render(<Dashboard />);
    fireEvent.click(screen.getByRole("button", { name: "Open rewards store" }));
    await waitFor(() => expect((screen.getByRole("button", { name: "Next credit history page" }) as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(screen.getByRole("button", { name: "Next credit history page" }));
    await waitFor(() => expect(apiMock.rewardOverview).toHaveBeenCalledWith(6, 5));
    expect(await screen.findByText("Shared a meal")).toBeTruthy();
  });

  it("shows sourced places and switches between HKUST and THE LOHAS", async () => {
    apiMock.venues.mockImplementation(async (options: { scope?: string; q?: string } = {}) =>
      options.scope ? [{ id: options.scope, name: options.scope === "hkust" ? "Can.teen II" : "Genki Sushi",
        campus_area: options.scope === "hkust" ? "LG1" : "L4", is_demo: false,
        scope: options.scope, source_url: "https://example.org/official", source_checked_at: "2026-10-28" }] : []);
    apiMock.externalNotes.mockResolvedValue([{ id: "note-1", scope: "hkust",
      title: "Student discussion", summary: "A linked public opinion.", source_platform: "Reddit",
      source_url: "https://www.reddit.com/r/HKUST/comments/example/", source_checked_at: "2026-10-28" }]);
    render(<Dashboard />);
    fireEvent.click(mainNav().getByRole("button", { name: "Food" }));
    const tabs = within(screen.getByRole("tablist", { name: "Discover category" }));
    fireEvent.click(tabs.getByRole("tab", { name: "Real places" }));
    expect(await screen.findByText("Can.teen II")).toBeTruthy();
    expect(await screen.findByText("Student discussion")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /THE LOHAS/ }));
    await waitFor(() => expect(apiMock.venues).toHaveBeenCalledWith(expect.objectContaining({ scope: "lohas" })));
    expect(await screen.findByText("Genki Sushi")).toBeTruthy();
  });

  it("builds and records a stage-aware workout from the exercise library", async () => {
    render(<Dashboard />);
    fireEvent.click(mainNav().getByRole("button", { name: "Move" }));
    fireEvent.click(screen.getByText("Training context"));
    fireEvent.click(screen.getByText("Exercise library"));
    expect(await screen.findByText("Seated row")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Workout stage"), { target: { value: "intermediate" } });
    fireEvent.click(screen.getByRole("button", { name: "Save training context" }));
    await waitFor(() => expect(apiMock.updateWorkoutProfile).toHaveBeenCalledWith(
      expect.objectContaining({ stage: "intermediate" })));
    fireEvent.click(screen.getByRole("button", { name: "Recommend my session" }));
    expect(await screen.findByText("This back session fits your beginner stage.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "I completed this session" }));
    await waitFor(() => expect(apiMock.completeWorkout).toHaveBeenCalledWith({
      plan_id: "plan-1", duration_min: 30,
    }));
    expect(await screen.findByText(/Workout recorded/)).toBeTruthy();
  });
});
