import { useEffect, useRef, useState } from "react";

type Result<T> = { value: T; error?: never } | { value?: never; error: string };

export default function useAutomaticSuggestion<T>(
  userId: string | undefined,
  visible: boolean,
  load: (signal: AbortSignal) => Promise<T>,
) {
  const [attempt, setAttempt] = useState(0);
  const [outcome, setOutcome] = useState<{ key: string; result: Result<T> }>();
  const request = useRef<AbortController | null>(null);
  const key = userId ? `${userId}:${attempt}` : null;

  // Reuse the result when moving between tabs. A change of account or settings starts over.
  useEffect(() => () => {
    request.current?.abort();
    request.current = null;
  }, [key]);

  useEffect(() => {
    if (!visible || !key || request.current) return;
    const controller = new AbortController();
    request.current = controller;
    const { signal } = controller;
    void Promise.resolve().then(async () => {
      // A development-mode effect setup can be cleaned up before the request starts.
      if (signal.aborted) return;
      try {
        const value = await load(signal);
        if (!signal.aborted) setOutcome({ key, result: { value } });
      } catch (cause) {
        const error = cause instanceof Error ? cause.message : "Could not load the suggestion.";
        if (!signal.aborted) setOutcome({ key, result: { error } });
      }
    });
  }, [key, load, visible]);

  return {
    result: outcome?.key === key ? outcome?.result : undefined,
    refresh: () => setAttempt(current => current + 1),
  };
}
