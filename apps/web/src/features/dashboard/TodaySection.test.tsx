import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import TodaySection from "./TodaySection";

describe("TodaySection", () => {
  it("shows the loading state before a summary arrives", () => {
    render(
      <TodaySection
        mealCount={0}
        workoutMinutes={0}
        loading
        hasSummary={false}
        onNavigate={vi.fn()}
        onAction={vi.fn()}
      />,
    );

    expect(screen.getByText("Checking today’s food and movement…")).toBeTruthy();
    expect(screen.queryByText("No meals are logged yet today.")).toBeNull();
  });

  it("renders one factual focus and routes its primary and secondary actions", () => {
    const onNavigate = vi.fn();
    const onAction = vi.fn();
    render(
      <TodaySection
        mealCount={0}
        workoutMinutes={0}
        loading={false}
        hasSummary
        onNavigate={onNavigate}
        onAction={onAction}
      />,
    );

    expect(screen.getByText("No meals are logged yet today.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Find a meal" }));
    expect(onAction).toHaveBeenCalledWith("food");
    fireEvent.click(screen.getByRole("button", { name: "Food" }));
    expect(onNavigate).toHaveBeenCalledWith("food");
    fireEvent.click(screen.getByRole("button", { name: "Move" }));
    expect(onNavigate).toHaveBeenCalledWith("workouts");
  });
});
