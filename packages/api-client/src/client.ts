import type {
  CommunityCommentCreate, CommunityCommentRead, CommunityPostCreate, CommunityPostRead,
  CommunityReportCreate, CommunityReportRead, CommunityReportResolve, DailySummary,
  DecisionCreate, DecisionRead, GoalRead, GoalUpdate,
  MeRead, MealLogCreate, MealLogRead, MenuItemRead, ProfileRead,
  ProfileUpdate, RecommendationJobRead, RecommendationRequest, RecommendationRunRead,
  RedemptionRead, RewardOverviewRead, VenueRead,
} from "./schema";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
let demoUserId: string | null = null;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}/api/v1${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(demoUserId ? { "X-Demo-User-Id": demoUserId } : {}),
      ...init?.headers,
    },
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
  setDemoUserId: (id: string) => { demoUserId = id; },
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
  communityPosts: (limit = 20, offset = 0) =>
    request<CommunityPostRead[]>(`/community/posts?limit=${limit}&offset=${offset}`),
  sharedMealLogIds: () => request<string[]>("/community/me/shared-meal-log-ids"),
  shareMeal: (body: CommunityPostCreate) => request<CommunityPostRead>("/community/posts", json("POST", body)),
  deletePost: (id: string) => request<void>(`/community/posts/${encodeURIComponent(id)}`, { method: "DELETE" }),
  comment: (postId: string, body: CommunityCommentCreate) =>
    request<CommunityCommentRead>(`/community/posts/${encodeURIComponent(postId)}/comments`, json("POST", body)),
  deleteComment: (id: string) => request<void>(`/community/comments/${encodeURIComponent(id)}`, { method: "DELETE" }),
  likePost: (id: string) => request<CommunityPostRead>(`/community/posts/${encodeURIComponent(id)}/like`, { method: "PUT" }),
  unlikePost: (id: string) => request<CommunityPostRead>(`/community/posts/${encodeURIComponent(id)}/like`, { method: "DELETE" }),
  reportPost: (id: string, body: CommunityReportCreate) =>
    request<CommunityReportRead>(`/community/posts/${encodeURIComponent(id)}/reports`, json("POST", body)),
  pendingReports: () => request<CommunityReportRead[]>("/community/reports/pending"),
  resolveReport: (id: string, body: CommunityReportResolve) =>
    request<CommunityReportRead>(`/community/reports/${encodeURIComponent(id)}/resolve`, json("POST", body)),
  rewardOverview: () => request<RewardOverviewRead>("/rewards/overview"),
  redeemReward: (id: string) =>
    request<RedemptionRead>(`/rewards/${encodeURIComponent(id)}/redeem`, { method: "POST" }),
};
