import type {
  CommunityPostCreate, CommunityPostRead, DailySummary, DecisionCreate, DecisionRead, GoalRead, GoalUpdate,
  MeRead, MealLogCreate, MealLogRead, MenuItemRead, ProfileRead,
  ProfileUpdate, RecommendationJobRead, RecommendationRequest, RecommendationRunRead, VenueRead,
} from "./schema";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}/api/v1${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body.error?.message ?? "Request failed");
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function json(method: string, body: unknown): RequestInit {
  return { method, body: JSON.stringify(body) };
}

export const api = {
  me: () => request<MeRead>("/me"),
  updateProfile: (body: ProfileUpdate) => request<ProfileRead>("/me/profile", json("PATCH", body)),
  goals: () => request<GoalRead>("/me/goals"),
  updateGoals: (body: GoalUpdate) => request<GoalRead>("/me/goals", json("PUT", body)),
  venues: () => request<VenueRead[]>("/venues"),
  menuItems: () => request<MenuItemRead[]>("/menu-items"),
  recommendations: (body: RecommendationRequest) =>
    request<RecommendationRunRead>("/recommendations/meals", json("POST", body)),
  startRecommendationJob: (body: RecommendationRequest) =>
    request<RecommendationJobRead>("/recommendations/jobs", json("POST", body)),
  recommendationJob: (id: string) =>
    request<RecommendationJobRead>(`/recommendations/jobs/${encodeURIComponent(id)}`),
  decide: (body: DecisionCreate) => request<DecisionRead>("/decisions", json("POST", body)),
  decisions: () => request<DecisionRead[]>("/me/decisions"),
  logMeal: (body: MealLogCreate) => request<MealLogRead>("/meal-logs", json("POST", body)),
  mealLogs: () => request<MealLogRead[]>("/me/meal-logs"),
  summary: () => request<DailySummary>("/me/daily-summary"),
  communityPosts: () => request<CommunityPostRead[]>("/community/posts"),
  shareMeal: (body: CommunityPostCreate) => request<CommunityPostRead>("/community/posts", json("POST", body)),
  deletePost: (id: string) => request<void>(`/community/posts/${encodeURIComponent(id)}`, { method: "DELETE" }),
};
