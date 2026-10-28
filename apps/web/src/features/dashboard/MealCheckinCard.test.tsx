import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import MealCheckinCard from "./MealCheckinCard";

const apiMock = vi.hoisted(() => ({
  startPhotoReview: vi.fn(), photoReview: vi.fn(), retryPhotoReview: vi.fn(), deletePhotoReview: vi.fn(),
}));
vi.mock("@nourishloop/api-client", () => ({ api: apiMock }));

afterEach(() => { cleanup(); vi.clearAllMocks(); vi.unstubAllGlobals(); });

it("uploads one photo and shows its queued review without manual food entry", async () => {
  vi.stubGlobal("URL", class extends URL {
    static createObjectURL = vi.fn(() => "blob:meal-preview");
    static revokeObjectURL = vi.fn();
  });
  apiMock.startPhotoReview.mockResolvedValue({
    id: "photo-1", review_status: "pending", review_attempts: 0,
    foods: [], nutrition_status: "none", unresolved_foods: [],
  });
  const file = new File(["photo"], "lunch.jpg", { type: "image/jpeg" });
  render(<MealCheckinCard onCompleted={async () => {}} />);
  fireEvent.change(screen.getByLabelText("Check-in photo"), { target: { files: [file] } });
  fireEvent.click(screen.getByRole("button", { name: "Check in this meal" }));
  await waitFor(() => expect(apiMock.startPhotoReview).toHaveBeenCalledWith(file, ""));
  expect(await screen.findByText("Review in progress")).toBeTruthy();
  expect(screen.queryByText("grams")).toBeNull();
});
