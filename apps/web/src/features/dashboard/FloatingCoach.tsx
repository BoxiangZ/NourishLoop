"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@nourishloop/api-client";

const GREETING = "Ask me about today’s meals or movement.";
const VOICE_UNAVAILABLE = "Voice input is unavailable. You can type your question instead.";
const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

type SpeechRecognitionResultEvent = {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
};

type SpeechRecognitionErrorEvent = {
  error: string;
};

type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionResultEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechWindow = Window & {
  SpeechRecognition?: new () => SpeechRecognitionLike;
  webkitSpeechRecognition?: new () => SpeechRecognitionLike;
};

export default function FloatingCoach() {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [voiceMessage, setVoiceMessage] = useState("");
  const [speechSupported, setSpeechSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const ringRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const anotherRef = useRef<HTMLButtonElement>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const exchangeIdRef = useRef(0);
  const hasOpenedRef = useRef(false);

  const resetExchange = useCallback(() => {
    exchangeIdRef.current += 1;
    setQuestion("");
    setAnswer(null);
    setSubmittedQuestion("");
    setBusy(false);
    setError("");
    setVoiceMessage("");
    setListening(false);
    recognitionRef.current?.stop();
  }, []);

  const closeCoach = useCallback(() => {
    resetExchange();
    setOpen(false);
  }, [resetExchange]);

  useEffect(() => {
    const speechWindow = window as SpeechWindow;
    setSpeechSupported(Boolean(
      speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition,
    ));
    return () => recognitionRef.current?.stop();
  }, []);

  useEffect(() => {
    if (open) {
      hasOpenedRef.current = true;
      if (answer) anotherRef.current?.focus();
      else inputRef.current?.focus();
    }
    else if (hasOpenedRef.current) ringRef.current?.focus();
  }, [open, answer]);

  useEffect(() => {
    if (!open) return;
    const regions = Array.from(
      document.querySelectorAll<HTMLElement>("[data-coach-background]"),
    );
    const previous = regions.map(element => ({
      element,
      inert: element.getAttribute("inert"),
      ariaHidden: element.getAttribute("aria-hidden"),
    }));
    regions.forEach(element => {
      element.setAttribute("inert", "true");
      element.setAttribute("aria-hidden", "true");
    });
    return () => {
      previous.forEach(({ element, inert, ariaHidden }) => {
        if (inert === null) element.removeAttribute("inert");
        else element.setAttribute("inert", inert);
        if (ariaHidden === null) element.removeAttribute("aria-hidden");
        else element.setAttribute("aria-hidden", ariaHidden);
      });
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        closeCoach();
        return;
      }
      if (event.key !== "Tab" || !dialogRef.current) return;

      const focusable = Array.from(
        dialogRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
      );
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (!first || !last) {
        event.preventDefault();
        return;
      }

      const active = document.activeElement;
      const outsideDialog = !dialogRef.current.contains(active);
      if (event.shiftKey && (active === first || outsideDialog)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (active === last || outsideDialog)) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [closeCoach, open]);

  async function ask(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || busy) return;

    const exchangeId = ++exchangeIdRef.current;
    setQuestion("");
    setSubmittedQuestion(trimmed);
    setAnswer(null);
    setError("");
    setVoiceMessage("");
    setBusy(true);
    try {
      const result = await api.askAssistant(trimmed);
      if (exchangeId !== exchangeIdRef.current) return;
      setAnswer(result.answer);
    } catch (cause) {
      if (exchangeId !== exchangeIdRef.current) return;
      setError(cause instanceof Error ? cause.message : "I couldn’t answer that right now. Try again.");
    } finally {
      if (exchangeId === exchangeIdRef.current) setBusy(false);
    }
  }

  function askAnother() {
    resetExchange();
  }

  function startVoiceQuestion() {
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    const speechWindow = window as SpeechWindow;
    const Recognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!Recognition) {
      setSpeechSupported(false);
      setVoiceMessage(VOICE_UNAVAILABLE);
      return;
    }

    setVoiceMessage("");
    const recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognition.onresult = event => {
      const transcript = event.results[0]?.[0]?.transcript?.trim();
      if (!transcript) return;
      setQuestion(transcript);
      window.requestAnimationFrame(() => inputRef.current?.focus());
    };
    recognition.onerror = event => {
      setListening(false);
      setVoiceMessage(event.error === "aborted" ? "Voice input stopped. You can type instead." : VOICE_UNAVAILABLE);
      window.requestAnimationFrame(() => inputRef.current?.focus());
    };
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    try {
      recognition.start();
      setListening(true);
    } catch {
      setVoiceMessage(VOICE_UNAVAILABLE);
      window.requestAnimationFrame(() => inputRef.current?.focus());
    }
  }

  return <>
    <button ref={ringRef} type="button" className="nl-coach-ring"
      aria-label="Open daily coach" onClick={() => setOpen(true)}>
      <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor"
        strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H5l1.7-3.1A7.5 7.5 0 1 1 20 11.5Z" />
        <path d="M8.5 10.5h7M8.5 14h4.5" />
      </svg>
      <span>Coach</span>
    </button>

    {open && <div className="nl-coach-blur" data-testid="coach-backdrop"
      onClick={event => { if (event.target === event.currentTarget) closeCoach(); }}>
      <section ref={dialogRef} className="nl-coach-dialogue" role="dialog" aria-modal="true"
        aria-labelledby="nl-coach-title">
        <div className="nl-coach-heading">
          <div>
            <span className="nl-eyebrow">DAILY COACH</span>
            <h2 id="nl-coach-title">A little guidance for today.</h2>
          </div>
          <button type="button" className="nl-coach-close" aria-label="Close daily coach"
            onClick={closeCoach}>×</button>
        </div>

        <div className="nl-coach-exchange" aria-live="polite">
          {!submittedQuestion && <p className="nl-coach-greeting">{GREETING}</p>}
          {submittedQuestion && <>
            <p className="nl-coach-label">YOUR QUESTION</p>
            <p className="nl-coach-question">{submittedQuestion}</p>
            {busy ? <p className="nl-coach-thinking" role="status">Thinking…</p> :
              answer ? <>
                <p className="nl-coach-label">COACH</p>
                <p className="nl-coach-answer">{answer}</p>
              </> : null}
          </>}
        </div>

        {error && <p className="nl-coach-error" role="alert">{error}</p>}
        {voiceMessage && <p className="nl-coach-voice-message" role="status">{voiceMessage}</p>}

        {answer ? <button ref={anotherRef} type="button" className="nl-button nl-button-soft nl-coach-another"
          onClick={askAnother}>Ask another question</button> :
          <form className="nl-coach-form" onSubmit={ask}>
            <label htmlFor="nl-coach-question">Ask the daily coach</label>
            <div className="nl-coach-input-row">
              <input ref={inputRef} id="nl-coach-question" type="text" maxLength={500}
                value={question} placeholder="What would help you today?"
                onChange={event => { setQuestion(event.target.value); setError(""); }} />
              {speechSupported && <button type="button" className="nl-coach-mic"
                aria-label={listening ? "Stop voice question" : "Start voice question"}
                aria-pressed={listening} onClick={startVoiceQuestion}>
                <svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor"
                  strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <rect x="9" y="3" width="6" height="11" rx="3" />
                  <path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M9 21h6" />
                </svg>
              </button>}
              <button type="submit" className="nl-button nl-button-primary"
                disabled={busy || !question.trim()}>{busy ? "Asking…" : "Send question"}</button>
            </div>
          </form>}
      </section>
    </div>}
  </>;
}
