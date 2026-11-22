import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import AppShell from "./AppShell";
import FloatingCoach from "./FloatingCoach";

const apiMock = vi.hoisted(() => ({ askAssistant: vi.fn() }));
vi.mock("@nourishloop/api-client", () => ({ api: apiMock }));

type RecognitionResultEvent = {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
};

type RecognitionErrorEvent = {
  error: string;
};

type RecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: RecognitionResultEvent) => void) | null;
  onerror: ((event: RecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

function openCoach() {
  fireEvent.click(screen.getByRole("button", { name: "Open daily coach" }));
}

function memoryStorage(): Storage {
  const values = new Map<string, string>();
  return {
    get length() { return values.size; },
    clear: vi.fn(() => values.clear()),
    getItem: vi.fn((key: string) => values.get(key) ?? null),
    key: vi.fn((index: number) => Array.from(values.keys())[index] ?? null),
    removeItem: vi.fn((key: string) => { values.delete(key); }),
    setItem: vi.fn((key: string, value: string) => { values.set(key, value); }),
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("sessionStorage", memoryStorage());
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("FloatingCoach", () => {
  it("opens with the default greeting, focuses the input, and replaces it with one answer", async () => {
    apiMock.askAssistant.mockResolvedValue({ answer: "Choose a balanced dinner." });
    render(<FloatingCoach />);

    openCoach();
    expect(screen.getByText("Ask me about today’s meals or movement.")).toBeTruthy();
    const input = screen.getByLabelText("Ask the daily coach");
    expect(document.activeElement).toBe(input);

    fireEvent.change(input, { target: { value: "  What should I eat for dinner?  " } });
    fireEvent.click(screen.getByRole("button", { name: "Send question" }));

    await waitFor(() => expect(apiMock.askAssistant).toHaveBeenCalledWith(
      "What should I eat for dinner?",
    ));
    expect(await screen.findByText("Choose a balanced dinner.")).toBeTruthy();
    expect(screen.queryByText("Ask me about today’s meals or movement.")).toBeNull();
  });

  it("starts a new independent exchange without repeating the old answer", async () => {
    apiMock.askAssistant
      .mockResolvedValueOnce({ answer: "First answer." })
      .mockResolvedValueOnce({ answer: "Second answer." });
    render(<FloatingCoach />);

    openCoach();
    fireEvent.change(screen.getByLabelText("Ask the daily coach"), {
      target: { value: "First question?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send question" }));
    await screen.findByText("First answer.");

    fireEvent.click(screen.getByRole("button", { name: "Ask another question" }));
    expect(screen.getByText("Ask me about today’s meals or movement.")).toBeTruthy();
    const nextInput = screen.getByLabelText("Ask the daily coach");
    expect((nextInput as HTMLInputElement).value).toBe("");
    fireEvent.change(nextInput, { target: { value: "Second question?" } });
    fireEvent.click(screen.getByRole("button", { name: "Send question" }));
    await screen.findByText("Second answer.");

    expect(apiMock.askAssistant).toHaveBeenLastCalledWith("Second question?");
    expect(apiMock.askAssistant).toHaveBeenCalledTimes(2);
    expect(screen.queryByText("First answer.")).toBeNull();
  });

  it("submits once while a question is in flight", async () => {
    let resolveAnswer!: (value: { answer: string }) => void;
    apiMock.askAssistant.mockReturnValue(new Promise(resolve => { resolveAnswer = resolve; }));
    render(<FloatingCoach />);

    openCoach();
    fireEvent.change(screen.getByLabelText("Ask the daily coach"), {
      target: { value: "Can I have a snack?" },
    });
    const submit = screen.getByRole("button", { name: "Send question" });
    fireEvent.click(submit);
    fireEvent.click(submit);

    expect(apiMock.askAssistant).toHaveBeenCalledTimes(1);
    expect((submit as HTMLButtonElement).disabled).toBe(true);
    await act(async () => resolveAnswer({ answer: "Yes, choose something satisfying." }));
    expect(await screen.findByText("Yes, choose something satisfying.")).toBeTruthy();
  });

  it("does not submit a blank or whitespace-only question", () => {
    render(<FloatingCoach />);

    openCoach();
    fireEvent.change(screen.getByLabelText("Ask the daily coach"), {
      target: { value: "   " },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send question" }));

    expect(apiMock.askAssistant).not.toHaveBeenCalled();
  });

  it("closes on Escape and restores focus to the ring", () => {
    render(<FloatingCoach />);
    const opener = screen.getByRole("button", { name: "Open daily coach" });

    openCoach();
    fireEvent.keyDown(window, { key: "Escape" });

    expect(screen.queryByLabelText("Ask the daily coach")).toBeNull();
    expect(document.activeElement).toBe(opener);
  });

  it("wraps Tab forward from the last dialog control without reaching background content", () => {
    render(<AppShell screen="today" me={null} busy={false} rewardBalance={0}
      onNavigate={() => {}} onSwitchUser={() => {}}>
      <button type="button">Background action</button>
    </AppShell>);

    openCoach();
    const input = screen.getByLabelText("Ask the daily coach");
    const close = screen.getByRole("button", { name: "Close daily coach" });
    fireEvent.keyDown(input, { key: "Tab" });

    expect(document.activeElement).toBe(close);
    expect(document.activeElement).not.toBe(screen.getByRole("button", { name: "Background action" }));
  });

  it("wraps Shift+Tab backward from the first dialog control", () => {
    render(<AppShell screen="today" me={null} busy={false} rewardBalance={0}
      onNavigate={() => {}} onSwitchUser={() => {}}>
      <button type="button">Background action</button>
    </AppShell>);

    openCoach();
    const input = screen.getByLabelText("Ask the daily coach");
    const close = screen.getByRole("button", { name: "Close daily coach" });
    close.focus();
    fireEvent.keyDown(close, { key: "Tab", shiftKey: true });

    expect(document.activeElement).toBe(input);
    expect(document.activeElement).not.toBe(screen.getByRole("button", { name: "Background action" }));
  });

  it("moves focus to Ask another question when the focused form is replaced by an answer", async () => {
    apiMock.askAssistant.mockResolvedValue({ answer: "Take a short walk after lunch." });
    render(<FloatingCoach />);

    openCoach();
    fireEvent.change(screen.getByLabelText("Ask the daily coach"), {
      target: { value: "What should I do after lunch?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send question" }));

    const another = await screen.findByRole("button", { name: "Ask another question" });
    expect(document.activeElement).toBe(another);
  });

  it("closes when the blurred backdrop is clicked", () => {
    render(<FloatingCoach />);

    openCoach();
    fireEvent.click(screen.getByTestId("coach-backdrop"));

    expect(screen.queryByLabelText("Ask the daily coach")).toBeNull();
  });

  it("renders model output as plain text", async () => {
    apiMock.askAssistant.mockResolvedValue({
      answer: "<strong>Plain guidance</strong> & more",
    });
    render(<FloatingCoach />);

    openCoach();
    fireEvent.change(screen.getByLabelText("Ask the daily coach"), {
      target: { value: "What is today's advice?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send question" }));

    const answer = await screen.findByText("<strong>Plain guidance</strong> & more");
    expect(answer.querySelector("strong")).toBeNull();
  });

  it("keeps exchanges out of browser storage and cookies", async () => {
    apiMock.askAssistant.mockResolvedValue({ answer: "A temporary answer." });
    render(<FloatingCoach />);

    openCoach();
    fireEvent.change(screen.getByLabelText("Ask the daily coach"), {
      target: { value: "A private question?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send question" }));
    await screen.findByText("A temporary answer.");

    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
    expect(document.cookie).toBe("");
  });

  it("shows a non-destructive error while preserving text input after failure", async () => {
    apiMock.askAssistant.mockRejectedValue(new Error("Coach is taking a break."));
    render(<FloatingCoach />);

    openCoach();
    fireEvent.change(screen.getByLabelText("Ask the daily coach"), {
      target: { value: "Can you help?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send question" }));

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByText("Coach is taking a break.")).toBeTruthy();
    expect(screen.getByLabelText("Ask the daily coach")).toBeTruthy();
  });

  it("uses a text fallback when speech recognition is unavailable", () => {
    render(<FloatingCoach />);

    openCoach();
    expect(screen.getByLabelText("Ask the daily coach")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Start voice question" })).toBeNull();
  });

  it("places an editable speech transcript in the text field without submitting", async () => {
    const recognitions: RecognitionLike[] = [];
    class MockSpeechRecognition implements RecognitionLike {
      continuous = false;
      interimResults = false;
      lang = "";
      onresult: RecognitionLike["onresult"] = null;
      onerror: RecognitionLike["onerror"] = null;
      onend: RecognitionLike["onend"] = null;
      start = vi.fn();
      stop = vi.fn();

      constructor() {
        recognitions.push(this);
      }
    }
    vi.stubGlobal("SpeechRecognition", MockSpeechRecognition);
    render(<FloatingCoach />);

    openCoach();
    fireEvent.click(await screen.findByRole("button", { name: "Start voice question" }));
    const recognition = recognitions[0];
    expect(recognition.start).toHaveBeenCalledTimes(1);
    act(() => recognition.onresult?.({
      results: [[{ transcript: "voice question" }]],
    }));

    const input = screen.getByLabelText("Ask the daily coach") as HTMLInputElement;
    expect(input.value).toBe("voice question");
    fireEvent.change(input, { target: { value: "edited voice question" } });
    expect(input.value).toBe("edited voice question");
    expect(apiMock.askAssistant).not.toHaveBeenCalled();
  });

  it("keeps text input usable when speech permission is denied", async () => {
    const recognitions: RecognitionLike[] = [];
    class MockSpeechRecognition implements RecognitionLike {
      continuous = false;
      interimResults = false;
      lang = "";
      onresult: RecognitionLike["onresult"] = null;
      onerror: RecognitionLike["onerror"] = null;
      onend: RecognitionLike["onend"] = null;
      start = vi.fn();
      stop = vi.fn();

      constructor() {
        recognitions.push(this);
      }
    }
    vi.stubGlobal("SpeechRecognition", MockSpeechRecognition);
    render(<FloatingCoach />);

    openCoach();
    fireEvent.click(await screen.findByRole("button", { name: "Start voice question" }));
    const recognition = recognitions[0];
    act(() => recognition.onerror?.({ error: "not-allowed" }));

    expect(screen.getByRole("status").textContent).toContain("You can type your question instead.");
    expect(screen.getByLabelText("Ask the daily coach")).toBeTruthy();
  });
});

it("mounts FloatingCoach once globally through AppShell", () => {
  render(<AppShell screen="today" me={null} busy={false} rewardBalance={0}
    onNavigate={() => {}} onSwitchUser={() => {}}><div>Workspace</div></AppShell>);

  expect(screen.getAllByRole("button", { name: "Open daily coach" })).toHaveLength(1);
});
