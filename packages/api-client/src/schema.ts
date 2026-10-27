// Generated from FastAPI OpenAPI. Run: python -m scripts.generate_api_types

export type CommunityPostCreate = { "meal_log_id": string; "caption": string; };
export type CommunityPostRead = { "id": string; "author_display_name": string; "meal_log_id": string; "caption": string; "created_at": string; "meal": MealLogRead; };
export type DailySummary = { "date": string; "timezone"?: string; "meal_count": number; "totals": NutritionTotals; };
export type DecisionCreate = { "menu_item_id": string; "recommendation_id"?: string | null; };
export type DecisionRead = { "id": string; "status": "planned" | "confirmed"; "created_at": string; "menu_item": MenuItemRead; };
export type ErrorBody = { "code": string; "message": string; };
export type ErrorResponse = { "error": ErrorBody; };
export type FeedbackCreate = { "helpful": boolean; "comment"?: string | null; };
export type GoalRead = { "goal": "eat_healthier" | "reduce_body_fat" | "build_muscle"; "daily_calorie_target"?: number | null; "user_id": string; };
export type GoalUpdate = { "goal": "eat_healthier" | "reduce_body_fat" | "build_muscle"; "daily_calorie_target"?: number | null; };
export type MeRead = { "id": string; "profile": ProfileRead; "goal": GoalRead; };
export type MealLogCreate = { "decision_id": string; "servings"?: number; };
export type MealLogRead = { "id": string; "decision_id": string; "servings": number; "consumed_at": string; "nutrition": NutritionTotals; "menu_item": MenuItemRead; };
export type MenuItemRead = { "id": string; "venue_id": string; "name": string; "description": string; "category": string; "tags": Array<string>; "allergen_tags": Array<string>; "price_hkd": number | null; "available": boolean; "source_label": string; "observed_at": string | null; "nutrition": NutritionRead; };
export type NutritionRead = { "calories_kcal": number; "protein_g": number; "carbs_g": number; "fat_g": number; "basis": string; "provenance": string; "uncertainty_note": string; };
export type NutritionTotals = { "calories_kcal"?: number; "protein_g"?: number; "carbs_g"?: number; "fat_g"?: number; };
export type ProfileRead = { "display_name": string; "dietary_preferences"?: Array<"vegan" | "vegetarian" | "high_protein" | "high_fibre">; "allergies"?: Array<"soy" | "wheat" | "egg" | "fish">; "user_id": string; };
export type ProfileUpdate = { "display_name": string; "dietary_preferences"?: Array<"vegan" | "vegetarian" | "high_protein" | "high_fibre">; "allergies"?: Array<"soy" | "wheat" | "egg" | "fish">; };
export type RecommendationJobRead = { "id": string; "status": "pending" | "claimed" | "completed" | "failed"; "attempts": number; "provider": "deterministic" | "openrouter"; "error": string | null; "created_at": string; "completed_at": string | null; "run": RecommendationRunRead | null; };
export type RecommendationRead = { "id": string; "rank": number; "score": number; "explanation": string; "confidence": "low" | "medium" | "high"; "confidence_reason": string; "menu_item": MenuItemRead; };
export type RecommendationRequest = { "meal_slot"?: "breakfast" | "lunch" | "dinner"; "limit"?: number; };
export type RecommendationRunRead = { "id": string; "scoring_version": string; "meal_slot": string; "recommendations": Array<RecommendationRead>; };
export type VenueRead = { "id": string; "name": string; "campus_area": string; "is_demo": boolean; };
