export type TodayFocusAction = "food" | "workouts" | "history";

export function todayFocus({
  mealCount,
  workoutMinutes,
}: {
  mealCount: number;
  workoutMinutes: number;
}): { headline: string; action: TodayFocusAction } {
  if (mealCount > 0 && workoutMinutes > 0) {
    return {
      headline: "You have checked in with food and movement today.",
      action: "history",
    };
  }
  if (mealCount > 0) {
    return {
      headline: "Meals are logged; movement is still open.",
      action: "workouts",
    };
  }
  if (workoutMinutes > 0) {
    return {
      headline: "Movement is logged; your next meal is still open.",
      action: "food",
    };
  }
  return {
    headline: "No meals are logged yet today.",
    action: "food",
  };
}
