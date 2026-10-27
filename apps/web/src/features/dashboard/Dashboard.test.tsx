import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { DailySummary, DecisionRead, MenuItemRead } from "@nourishloop/api-client/schema";
import Dashboard from "./Dashboard";

const apiMock = vi.hoisted(() => ({
  me: vi.fn(), venues: vi.fn(), menuItems: vi.fn(), decisions: vi.fn(), summary: vi.fn(),
  startRecommendationJob: vi.fn(), recommendationJob: vi.fn(),
  decide: vi.fn(), logMeal: vi.fn(), mealLogs: vi.fn(),
  communityPosts: vi.fn(), shareMeal: vi.fn(), deletePost: vi.fn(),
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

beforeEach(() => {
  vi.clearAllMocks();
  plans = [];
  logs = [];
  posts = [];
  summary = { date: "2026-10-24", timezone: "Asia/Hong_Kong", meal_count: 0,
    totals: { calories_kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 } };
  apiMock.me.mockResolvedValue({ id: "demo-student",
    profile: { user_id: "demo-student", display_name: "Demo Student", dietary_preferences: [], allergies: [] },
    goal: { user_id: "demo-student", goal: "eat_healthier", daily_calorie_target: 1900 } });
  apiMock.venues.mockResolvedValue([{ id: "venue-1", name: "Garden Counter (demo)",
    campus_area: "fictional", is_demo: true }]);
  apiMock.menuItems.mockResolvedValue([meal]);
  apiMock.decisions.mockImplementation(async () => plans);
  apiMock.summary.mockImplementation(async () => summary);
  apiMock.mealLogs.mockImplementation(async () => logs);
  apiMock.communityPosts.mockImplementation(async () => posts);
  const run = { id: "run-1", meal_slot: "lunch",
    scoring_version: "rules-v1", recommendations: [{ id: "recommendation-1", rank: 1,
      score: 0.8, explanation: "Fits your approximate meal budget.",
      confidence: "low", confidence_reason: "Demo estimate", menu_item: meal }] };
  apiMock.startRecommendationJob.mockResolvedValue({ id: "job-1", status: "pending", attempts: 0 });
  apiMock.recommendationJob.mockResolvedValue({ id: "job-1", status: "completed", attempts: 1, run });
  apiMock.decide.mockImplementation(async () => {
    const plan: DecisionRead = { id: "decision-1", status: "planned",
      created_at: "2026-10-24T12:00:00Z", menu_item: meal };
    plans = [plan];
    return plan;
  });
  apiMock.logMeal.mockImplementation(async () => {
    plans = [{ ...plans[0], status: "confirmed" }];
    summary = { ...summary, meal_count: 1,
      totals: { calories_kcal: 470, protein_g: 18, carbs_g: 56, fat_g: 19 } };
    const log = { id: "log-1", decision_id: "decision-1", servings: 1,
      consumed_at: "2026-10-24T12:30:00Z", nutrition: summary.totals, menu_item: meal };
    logs = [log];
    return log;
  });
  apiMock.shareMeal.mockImplementation(async ({ meal_log_id, caption }) => {
    const post = { id: "post-1", meal_log_id, caption, author_display_name: "Demo Student",
      created_at: "2026-10-24T12:45:00Z", meal: logs[0] };
    posts = [post];
    return post;
  });
});

afterEach(cleanup);

describe("Dashboard meal flow", () => {
  it("counts a meal only after explicit confirmation", async () => {
    render(<Dashboard />);
    expect(await screen.findByText("Chickpea salad")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Find my lunch" }));
    expect(await screen.findByText("Recommended for you")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Plan this meal" }));
    expect(await screen.findByRole("button", { name: "I ate this meal" })).toBeTruthy();
    expect(screen.getByText("0", { selector: "div" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "I ate this meal" }));
    await waitFor(() => expect(apiMock.logMeal).toHaveBeenCalledWith({
      decision_id: "decision-1", servings: 1,
    }));
    expect(await screen.findByText("470", { selector: "div" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "I ate this meal" })).toBeNull();
  });

  it("shares a confirmed meal only after the user submits a caption", async () => {
    render(<Dashboard />);
    expect(await screen.findByText("Chickpea salad")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Share meal" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Plan this meal" }));
    fireEvent.click(await screen.findByRole("button", { name: "I ate this meal" }));
    const share = await screen.findByRole("button", { name: "Share meal" });
    expect(apiMock.shareMeal).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Confirmed meal to share"), { target: { value: "log-1" } });
    fireEvent.change(screen.getByLabelText("Community caption"), { target: { value: "Loved this lunch" } });
    fireEvent.click(share);
    await waitFor(() => expect(apiMock.shareMeal).toHaveBeenCalledWith({
      meal_log_id: "log-1", caption: "Loved this lunch",
    }));
    expect(await screen.findByText("Loved this lunch")).toBeTruthy();
  });
});
