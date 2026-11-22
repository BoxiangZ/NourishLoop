import { describe, expect, it } from "vitest";
import { todayFocus } from "./todayFocus";

describe("todayFocus", () => {
  it("uses factual states without nutrition claims", () => {
    expect(todayFocus({ mealCount: 0, workoutMinutes: 0 })).toEqual({
      headline: "No meals are logged yet today.",
      action: "food",
    });
    expect(todayFocus({ mealCount: 2, workoutMinutes: 0 })).toEqual({
      headline: "Meals are logged; movement is still open.",
      action: "workouts",
    });
    expect(todayFocus({ mealCount: 0, workoutMinutes: 30 })).toEqual({
      headline: "Movement is logged; your next meal is still open.",
      action: "food",
    });
    expect(todayFocus({ mealCount: 2, workoutMinutes: 30 })).toEqual({
      headline: "You have checked in with food and movement today.",
      action: "history",
    });
  });
});
