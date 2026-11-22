import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import DailyCoachReport from "./DailyCoachReport";

const apiMock = vi.hoisted(() => ({ dailyCoachReport: vi.fn() }));
vi.mock("@nourishloop/api-client", () => ({ api: apiMock }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("DailyCoachReport", () => {
  it("generates one report on demand and disables duplicate clicks while pending", async () => {
    let finishReport: (report: {
      headline: string;
      nutrition_insight: string;
      activity_insight: string;
      next_actions: string[];
      limitations: string[];
    }) => void = () => {};
    apiMock.dailyCoachReport.mockReturnValue(new Promise(resolve => {
      finishReport = resolve;
    }));

    render(<DailyCoachReport />);
    expect(apiMock.dailyCoachReport).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Generate daily coach report" }));

    const pendingButton = screen.getByRole("button", { name: "Generating report…" });
    expect((pendingButton as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(pendingButton);
    expect(apiMock.dailyCoachReport).toHaveBeenCalledTimes(1);

    finishReport({
      headline: "A steady day.",
      nutrition_insight: "Two meals are recorded.",
      activity_insight: "One workout is completed.",
      next_actions: ["Choose a balanced dinner."],
      limitations: ["Nutrition values are estimates."],
    });

    expect(await screen.findByText("A steady day.")).toBeTruthy();
    expect(screen.getByText("Two meals are recorded.")).toBeTruthy();
    expect(screen.getByText("One workout is completed.")).toBeTruthy();
    expect(screen.getByText("Choose a balanced dinner.")).toBeTruthy();
    expect(screen.getByText("Nutrition values are estimates.")).toBeTruthy();
    expect(apiMock.dailyCoachReport).toHaveBeenCalledTimes(1);
  });

  it("renders report values as text instead of markup", async () => {
    apiMock.dailyCoachReport.mockResolvedValue({
      headline: "<img src=x onerror=alert('headline')>",
      nutrition_insight: "<strong>Nutrition</strong>",
      activity_insight: "<script>alert('activity')</script>",
      next_actions: ["<b>Move gently</b>"],
      limitations: ["<em>Estimated data</em>"],
    });

    const { container } = render(<DailyCoachReport />);
    fireEvent.click(screen.getByRole("button", { name: "Generate daily coach report" }));

    expect(await screen.findByText("<img src=x onerror=alert('headline')>")).toBeTruthy();
    expect(screen.getByText("<strong>Nutrition</strong>")).toBeTruthy();
    expect(screen.getByText("<script>alert('activity')</script>")).toBeTruthy();
    expect(screen.getByText("<b>Move gently</b>")).toBeTruthy();
    expect(screen.getByText("<em>Estimated data</em>")).toBeTruthy();
    expect(container.querySelector("img, strong, script, b, em")).toBeNull();
  });

  it("offers one manual retry after failure and does not retry automatically", async () => {
    apiMock.dailyCoachReport
      .mockRejectedValueOnce(new Error("Coach timed out"))
      .mockResolvedValueOnce({
        headline: "Back on track.",
        nutrition_insight: "Your meal record is available.",
        activity_insight: "No workout is recorded.",
        next_actions: ["Plan a gentle walk."],
        limitations: ["Activity data may be incomplete."],
      });

    render(<DailyCoachReport />);
    fireEvent.click(screen.getByRole("button", { name: "Generate daily coach report" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toBe("Coach timed out");
    expect(apiMock.dailyCoachReport).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Retry daily coach report" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Retry daily coach report" }));
    expect(await screen.findByText("Back on track.")).toBeTruthy();
    expect(apiMock.dailyCoachReport).toHaveBeenCalledTimes(2);
  });

  it("clears a generated report when unmounted", async () => {
    apiMock.dailyCoachReport.mockResolvedValue({
      headline: "A temporary report.",
      nutrition_insight: "Nutrition insight.",
      activity_insight: "Activity insight.",
      next_actions: ["Next action."],
      limitations: ["Limitation."],
    });

    const first = render(<DailyCoachReport />);
    fireEvent.click(screen.getByRole("button", { name: "Generate daily coach report" }));
    expect(await screen.findByText("A temporary report.")).toBeTruthy();
    first.unmount();

    render(<DailyCoachReport />);
    expect(screen.getByRole("button", { name: "Generate daily coach report" })).toBeTruthy();
    await waitFor(() => expect(screen.queryByText("A temporary report.")).toBeNull());
    expect(apiMock.dailyCoachReport).toHaveBeenCalledTimes(1);
  });
});
