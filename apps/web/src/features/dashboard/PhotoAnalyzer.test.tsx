import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import PhotoAnalyzer from "./PhotoAnalyzer";

const apiMock = vi.hoisted(() => ({
  analyzePhoto: vi.fn(), recordPhotoMeal: vi.fn(), nutritionFoods: vi.fn(),
  estimatePhotoNutrition: vi.fn(), autoEstimatePhotoNutrition: vi.fn(),
}));
vi.mock("@nourishloop/api-client", () => ({ api: apiMock }));

function mockPreviewUrl() {
  vi.stubGlobal("URL", class extends URL {
    static createObjectURL = vi.fn(() => "blob:preview");
    static revokeObjectURL = vi.fn();
  });
}

afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.clearAllMocks(); });

describe("food photo recognition", () => {
  it("shows food and nutrition after one Recognize click, then saves only if asked", async () => {
    vi.stubGlobal("createImageBitmap", vi.fn(async () => ({ width: 800, height: 600, close: vi.fn() })));
    mockPreviewUrl();
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({
      fillStyle: "white", fillRect: vi.fn(), drawImage: vi.fn(),
    } as unknown as CanvasRenderingContext2D);
    vi.spyOn(HTMLCanvasElement.prototype, "toDataURL").mockReturnValue("data:image/jpeg;base64,YWJj");
    apiMock.analyzePhoto.mockResolvedValue({ model: "vision-model", requires_review: false,
      foods: [{ name: "Rice", preparation: "cooked", quantity_from_notes: null,
        estimated_grams: 150, portion_basis: "visual_estimate" }],
      review_questions: ["How much did you eat?"],
    });
    apiMock.recordPhotoMeal.mockResolvedValue({ id: "photo-1" });
    apiMock.nutritionFoods.mockResolvedValue([{ fdc_id: 168878,
      description: "Rice, white, cooked", data_type: "SR Legacy", calories_kcal: 130,
      protein_g: 2.7, carbs_g: 28.2, fat_g: 0.3,
      source_url: "https://fdc.nal.usda.gov/food-search/?query=168878" }]);
    const estimate = {
      nutrition: { calories_kcal: 195, protein_g: 4.1, carbs_g: 42.3, fat_g: 0.5 },
      items: [{ name: "Rice", fdc_id: 168878, source_description: "Rice, white, cooked",
        source_url: "https://fdc.nal.usda.gov/food-search/?query=168878", grams: 150,
        portion_basis: "visual_estimate",
        calories_kcal: 195, protein_g: 4.1, carbs_g: 42.3, fat_g: 0.5 }],
      uncertainty_note: "Approximate total",
    };
    apiMock.autoEstimatePhotoNutrition.mockResolvedValue({ estimate,
      selections: [{ food_index: 0, fdc_id: 168878, grams: 150, portion_basis: "visual_estimate" }],
      matches: [{ food_index: 0, match: { fdc_id: 168878, description: "Rice, white, cooked",
        data_type: "SR Legacy", calories_kcal: 130, protein_g: 2.7, carbs_g: 28.2,
        fat_g: 0.3, source_url: "https://fdc.nal.usda.gov/food-search/?query=168878" } }],
      unresolved: [],
    });
    const onConfirmed = vi.fn(async () => {});
    render(<PhotoAnalyzer onConfirmed={onConfirmed} />);
    const file = new File(["fake bytes"], "lunch.png", { type: "image/png" });
    fireEvent.change(screen.getByLabelText("Food photo"), { target: { files: [file] } });
    expect(apiMock.analyzePhoto).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Recognize food" }));
    await waitFor(() => expect(apiMock.analyzePhoto).toHaveBeenCalledWith({
      image_base64: "YWJj", mime_type: "image/jpeg", notes: "",
    }));
    await waitFor(() => expect(apiMock.autoEstimatePhotoNutrition).toHaveBeenCalled());
    expect(await screen.findByText("Approx. 195 kcal")).toBeTruthy();
    expect(screen.queryByLabelText("Food 1 grams")).toBeNull();
    expect(apiMock.recordPhotoMeal).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Save result to History" }));
    await waitFor(() => expect(apiMock.recordPhotoMeal).toHaveBeenCalledWith({
      foods: [{ name: "Rice", preparation: "cooked", quantity_from_notes: null,
        estimated_grams: 150, portion_basis: "visual_estimate" }],
      notes: "", model: "vision-model",
      nutrition_selections: [{ food_index: 0, fdc_id: 168878, grams: 150,
        portion_basis: "visual_estimate" }],
    }));
    expect(onConfirmed).toHaveBeenCalledOnce();
  });

  it("rejects unsupported and oversized files before upload", () => {
    mockPreviewUrl();
    render(<PhotoAnalyzer onConfirmed={async () => {}} />);
    fireEvent.change(screen.getByLabelText("Food photo"), { target: {
      files: [new File(["text"], "notes.txt", { type: "text/plain" })],
    } });
    expect(screen.getByRole("alert").textContent).toContain("JPEG, PNG or WebP");
    expect(apiMock.analyzePhoto).not.toHaveBeenCalled();
    expect(screen.getByRole<HTMLButtonElement>("button", { name: "Recognize food" }).disabled).toBe(true);
  });

  it("shows sourced nutrition for matched foods after Recognize even when another ingredient is unresolved", async () => {
    vi.stubGlobal("createImageBitmap", vi.fn(async () => ({ width: 800, height: 600, close: vi.fn() })));
    mockPreviewUrl();
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({
      fillStyle: "white", fillRect: vi.fn(), drawImage: vi.fn(),
    } as unknown as CanvasRenderingContext2D);
    vi.spyOn(HTMLCanvasElement.prototype, "toDataURL").mockReturnValue("data:image/jpeg;base64,YWJj");
    apiMock.analyzePhoto.mockResolvedValue({ model: "vision-model", requires_review: false,
      foods: [
        { name: "Egg", preparation: "fried", estimated_grams: 50, portion_basis: "visual_estimate" },
        { name: "Sauce", preparation: null, estimated_grams: 30, portion_basis: "visual_estimate" },
      ], review_questions: [],
    });
    apiMock.autoEstimatePhotoNutrition.mockResolvedValue({ estimate: null,
      partial_estimate: { nutrition: { calories_kcal: 98, protein_g: 6.8, carbs_g: 0.4, fat_g: 7.4 },
        items: [{ name: "Egg", fdc_id: 173423, source_description: "Egg, whole, cooked, fried",
          source_url: "https://fdc.nal.usda.gov/food-search/?query=173423", grams: 50,
          portion_basis: "visual_estimate" }], uncertainty_note: "Approximate total" },
      selections: [{ food_index: 0, fdc_id: 173423, grams: 50, portion_basis: "visual_estimate" }],
      matches: [], unresolved: ["Sauce: No reliable USDA match"],
    });
    render(<PhotoAnalyzer onConfirmed={async () => {}} />);
    fireEvent.change(screen.getByLabelText("Food photo"), { target: {
      files: [new File(["fake bytes"], "lunch.png", { type: "image/png" })],
    } });
    fireEvent.click(screen.getByRole("button", { name: "Recognize food" }));
    expect(await screen.findByText("Matched foods only · approx. 98 kcal")).toBeTruthy();
    expect(screen.getByText(/Sauce: No reliable USDA match/)).toBeTruthy();
    apiMock.recordPhotoMeal.mockResolvedValue({ id: "partial-photo" });
    fireEvent.click(screen.getByRole("button", { name: "Save partial estimate to History" }));
    await waitFor(() => expect(apiMock.recordPhotoMeal).toHaveBeenCalledWith({
      foods: [
        { name: "Egg", preparation: "fried", quantity_from_notes: null,
          estimated_grams: 50, portion_basis: "visual_estimate" },
        { name: "Sauce", preparation: null, quantity_from_notes: null,
          estimated_grams: 30, portion_basis: "visual_estimate" },
      ],
      notes: "", model: "vision-model",
      nutrition_selections: [{ food_index: 0, fdc_id: 173423, grams: 50,
        portion_basis: "visual_estimate" }],
    }));
  });

  it("lets the user supply only an unclear portion after automatic matching", async () => {
    vi.stubGlobal("createImageBitmap", vi.fn(async () => ({ width: 800, height: 600, close: vi.fn() })));
    mockPreviewUrl();
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({
      fillStyle: "white", fillRect: vi.fn(), drawImage: vi.fn(),
    } as unknown as CanvasRenderingContext2D);
    vi.spyOn(HTMLCanvasElement.prototype, "toDataURL").mockReturnValue("data:image/jpeg;base64,YWJj");
    const source = { fdc_id: 168878, description: "Rice, white, cooked", data_type: "SR Legacy",
      calories_kcal: 130, protein_g: 2.7, carbs_g: 28.2, fat_g: 0.3,
      source_url: "https://fdc.nal.usda.gov/food-search/?query=168878" };
    apiMock.analyzePhoto.mockResolvedValue({ model: "vision-model", requires_review: false,
      foods: [{ name: "Rice, white, cooked", preparation: null, quantity_from_notes: null,
        estimated_grams: null, portion_basis: "unknown" }], review_questions: [],
    });
    apiMock.autoEstimatePhotoNutrition.mockResolvedValue({ estimate: null, selections: [],
      matches: [{ food_index: 0, match: source, reason: "Portion weight unclear" }],
      unresolved: ["Rice: Portion weight unclear"],
    });
    apiMock.estimatePhotoNutrition.mockResolvedValue({ nutrition: {
      calories_kcal: 195, protein_g: 4.1, carbs_g: 42.3, fat_g: 0.5,
    }, items: [], uncertainty_note: "Approximate total" });
    render(<PhotoAnalyzer onConfirmed={async () => {}} />);
    fireEvent.change(screen.getByLabelText("Take food photo"), { target: {
      files: [new File(["fake bytes"], "lunch.png", { type: "image/png" })],
    } });
    fireEvent.click(screen.getByRole("button", { name: "Recognize food" }));
    expect(await screen.findByText(/Portion weight unclear/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Adjust foods and portions" }));
    expect((screen.getByLabelText("USDA match 1") as HTMLSelectElement).value).toBe("168878");
    fireEvent.change(screen.getByLabelText("Food 1 grams"), { target: { value: "150" } });
    fireEvent.click(screen.getByRole("button", { name: "Recalculate nutrition" }));
    await waitFor(() => expect(apiMock.estimatePhotoNutrition).toHaveBeenCalledWith({
      foods: [{ name: "Rice, white, cooked", preparation: null, quantity_from_notes: null,
        estimated_grams: null, portion_basis: "unknown" }],
      nutrition_selections: [{ food_index: 0, fdc_id: 168878, grams: 150,
        portion_basis: "user_adjusted" }],
    }));
  });
});
