import type {
  CommunityCommentCreate, CommunityCommentRead, CommunityPostCreate, CommunityPostRead,
  CommunityReportCreate, CommunityReportRead, CommunityReportResolve, DailySummary,
  DecisionCreate, DecisionRead, ExerciseRead, ExternalNoteRead, GoalRead, GoalUpdate,
  MeRead, MealLogCreate, MealLogRead, MenuItemRead, ProfileRead,
  PhotoAnalysisRead, PhotoAnalysisRequest, PhotoMealCreate, PhotoMealRead,
  PhotoAutoEstimateRequest, PhotoAutoEstimateRead,
  NutritionFoodRead, PhotoNutritionEstimateRead, PhotoNutritionEstimateRequest,
  ProfileUpdate, RecommendationJobRead, RecommendationRequest, RecommendationRunRead,
  RedemptionRead, RewardOverviewRead, VenueRead, WorkoutPlanRead,
  WorkoutProfileRead, WorkoutProfileUpdate, WorkoutRecommendRequest,
  WorkoutSessionCreate, WorkoutSessionRead,
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

async function uploadPhotoReview(file: File, notes: string): Promise<PhotoMealRead> {
  const form = new FormData();
  form.append("photo", file);
  form.append("notes", notes);
  const response = await fetch(`${baseUrl}/api/v1/photo-meals/reviews`, {
    method: "POST", body: form,
    headers: demoUserId ? { "X-Demo-User-Id": demoUserId } : {},
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body.error?.message ?? "Photo upload failed");
  }
  return response.json() as Promise<PhotoMealRead>;
}

export const api = {
  setDemoUserId: (id: string) => { demoUserId = id; },
  me: () => request<MeRead>("/me"),
  updateProfile: (body: ProfileUpdate) => request<ProfileRead>("/me/profile", json("PATCH", body)),
  goals: () => request<GoalRead>("/me/goals"),
  updateGoals: (body: GoalUpdate) => request<GoalRead>("/me/goals", json("PUT", body)),
  venues: (options: { limit?: number; offset?: number; scope?: "demo" | "hkust" | "lohas"; q?: string } = {}) => {
    const params = new URLSearchParams();
    if (options.limit !== undefined) params.set("limit", String(options.limit));
    if (options.offset !== undefined) params.set("offset", String(options.offset));
    if (options.scope) params.set("scope", options.scope);
    if (options.q) params.set("q", options.q);
    return request<VenueRead[]>(`/venues?${params}`);
  },
  externalNotes: (scope: "hkust" | "lohas") =>
    request<ExternalNoteRead[]>(`/external-notes?scope=${scope}`),
  menuItems: (options: {
    limit?: number; offset?: number; q?: string; tag?: string; maxPriceHkd?: number;
  } = {}) => {
    const params = new URLSearchParams();
    if (options.limit !== undefined) params.set("limit", String(options.limit));
    if (options.offset !== undefined) params.set("offset", String(options.offset));
    if (options.q) params.set("q", options.q);
    if (options.tag) params.set("tag", options.tag);
    if (options.maxPriceHkd !== undefined) params.set("max_price_hkd", String(options.maxPriceHkd));
    return request<MenuItemRead[]>(`/menu-items?${params}`);
  },
  recommendations: (body: RecommendationRequest) =>
    request<RecommendationRunRead>("/recommendations/meals", json("POST", body)),
  startRecommendationJob: (body: RecommendationRequest) =>
    request<RecommendationJobRead>("/recommendations/jobs", json("POST", body)),
  recommendationJob: (id: string) =>
    request<RecommendationJobRead>(`/recommendations/jobs/${encodeURIComponent(id)}`),
  decide: (body: DecisionCreate) => request<DecisionRead>("/decisions", json("POST", body)),
  decisions: (limit = 20, offset = 0) =>
    request<DecisionRead[]>(`/me/decisions?limit=${limit}&offset=${offset}`),
  logMeal: (body: MealLogCreate) => request<MealLogRead>("/meal-logs", json("POST", body)),
  mealLogs: (limit = 20, offset = 0) =>
    request<MealLogRead[]>(`/me/meal-logs?limit=${limit}&offset=${offset}`),
  analyzePhoto: (body: PhotoAnalysisRequest) =>
    request<PhotoAnalysisRead>("/meals/analyze-photo", json("POST", body)),
  autoEstimatePhotoNutrition: (body: PhotoAutoEstimateRequest) =>
    request<PhotoAutoEstimateRead>("/photo-meals/auto-estimate", json("POST", body)),
  recordPhotoMeal: (body: PhotoMealCreate) =>
    request<PhotoMealRead>("/photo-meals", json("POST", body)),
  photoMeals: (limit = 20, offset = 0) =>
    request<PhotoMealRead[]>(`/me/photo-meals?limit=${limit}&offset=${offset}`),
  startPhotoReview: uploadPhotoReview,
  photoReview: (id: string) => request<PhotoMealRead>(`/photo-meals/${encodeURIComponent(id)}`),
  retryPhotoReview: (id: string) => request<PhotoMealRead>(`/photo-meals/${encodeURIComponent(id)}/retry`, { method: "POST" }),
  deletePhotoReview: (id: string) => request<void>(`/photo-meals/${encodeURIComponent(id)}`, { method: "DELETE" }),
  nutritionFoods: (q: string, limit = 6) =>
    request<NutritionFoodRead[]>(`/nutrition-foods?q=${encodeURIComponent(q)}&limit=${limit}`),
  estimatePhotoNutrition: (body: PhotoNutritionEstimateRequest) =>
    request<PhotoNutritionEstimateRead>("/photo-meals/estimate", json("POST", body)),
  summary: (date?: string) => request<DailySummary>(
    `/me/daily-summary${date ? `?date=${encodeURIComponent(date)}` : ""}`
  ),
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
  rewardOverview: (transactionLimit = 20, transactionOffset = 0) =>
    request<RewardOverviewRead>(`/rewards/overview?transaction_limit=${transactionLimit}&transaction_offset=${transactionOffset}`),
  redeemReward: (id: string) =>
    request<RedemptionRead>(`/rewards/${encodeURIComponent(id)}/redeem`, { method: "POST" }),
  exercises: (options: { limit?: number; offset?: number; muscleGroup?: string; equipment?: string; q?: string } = {}) => {
    const params = new URLSearchParams();
    if (options.limit !== undefined) params.set("limit", String(options.limit));
    if (options.offset !== undefined) params.set("offset", String(options.offset));
    if (options.muscleGroup) params.set("muscle_group", options.muscleGroup);
    if (options.equipment) params.set("equipment", options.equipment);
    if (options.q) params.set("q", options.q);
    return request<ExerciseRead[]>(`/exercises?${params}`);
  },
  workoutProfile: () => request<WorkoutProfileRead>("/me/workout-profile"),
  updateWorkoutProfile: (body: WorkoutProfileUpdate) =>
    request<WorkoutProfileRead>("/me/workout-profile", json("PUT", body)),
  recommendWorkout: (body: WorkoutRecommendRequest) =>
    request<WorkoutPlanRead>("/workouts/recommend", json("POST", body)),
  completeWorkout: (body: WorkoutSessionCreate) =>
    request<WorkoutSessionRead>("/workouts/sessions", json("POST", body)),
  workoutSessions: (limit = 20, offset = 0) =>
    request<WorkoutSessionRead[]>(`/me/workout-sessions?limit=${limit}&offset=${offset}`),
};
