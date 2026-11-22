import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "@nourishloop/api-client";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

function response(body: unknown) {
  return {
    ok: true,
    status: 200,
    json: vi.fn(async () => body),
  } as unknown as Response;
}

describe("assistant API client methods", () => {
  it("posts a question to the assistant endpoint", async () => {
    const fetchMock = vi.fn(async () => response({ answer: "Choose dinner." }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.askAssistant("What should I eat?")).resolves.toEqual({
      answer: "Choose dinner.",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/v1\/assistant\/ask$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question: "What should I eat?" }),
      }),
    );
  });

  it("requests the daily coach report without a request body", async () => {
    const report = {
      headline: "A steady day",
      nutrition_insight: "Meals were balanced.",
      activity_insight: "Movement was moderate.",
      next_actions: ["Add vegetables at dinner."],
      limitations: ["Nutrition is estimated."],
    };
    const fetchMock = vi.fn<(
      input: RequestInfo | URL,
      init?: RequestInit,
    ) => Promise<Response>>(async () => response(report));
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.dailyCoachReport()).resolves.toEqual(report);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/v1\/assistant\/daily-report$/);
    expect(init).toMatchObject({ method: "POST" });
    expect(init).not.toHaveProperty("body");
  });
});
