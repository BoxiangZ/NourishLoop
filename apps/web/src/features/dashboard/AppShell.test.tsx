import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AppShell from "./AppShell";

describe("AppShell navigation", () => {
  it("renders five health destinations and separates utilities", () => {
    render(
      <AppShell
        screen="today"
        me={null}
        busy={false}
        rewardBalance={1240}
        onNavigate={vi.fn()}
        onSwitchUser={vi.fn()}
      >
        <div>content</div>
      </AppShell>,
    );

    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    expect(nav.textContent).toContain("Today");
    expect(nav.textContent).toContain("Food");
    expect(nav.textContent).toContain("Move");
    expect(nav.textContent).toContain("Progress");
    expect(nav.textContent).toContain("Community");
    expect(screen.getByRole("button", { name: "Open rewards store" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open profile" })).toBeTruthy();
  });
});
