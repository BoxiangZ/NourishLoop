"use client";

import { useRef, useState } from "react";
import { api } from "@nourishloop/api-client";
import type { DailyCoachReport as DailyCoachReportData } from "@nourishloop/api-client/schema";

type ReportState = "idle" | "generating" | "ready" | "error";

function errorMessage(cause: unknown): string {
  return cause instanceof Error && cause.message
    ? cause.message
    : "The daily coach report could not be generated.";
}

export default function DailyCoachReport() {
  const [state, setState] = useState<ReportState>("idle");
  const [report, setReport] = useState<DailyCoachReportData | null>(null);
  const [error, setError] = useState("");
  const requestInFlight = useRef(false);

  async function generateReport() {
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    setState("generating");
    setReport(null);
    setError("");
    try {
      setReport(await api.dailyCoachReport());
      setState("ready");
    } catch (cause) {
      setError(errorMessage(cause));
      setState("error");
    } finally {
      requestInFlight.current = false;
    }
  }

  return <section className="nl-daily-report" aria-labelledby="daily-coach-report-title">
    <div className="nl-daily-report-heading">
      <div>
        <span className="nl-eyebrow">DAILY COACH REPORT</span>
        <h2 id="daily-coach-report-title">{report?.headline ?? "A progress report, on your terms."}</h2>
      </div>
      {state === "idle" && <button className="nl-button nl-button-primary" onClick={() => void generateReport()}>
        Generate daily coach report
      </button>}
      {state === "error" && <button className="nl-button nl-button-primary" onClick={() => void generateReport()}>
        Retry daily coach report
      </button>}
    </div>

    {state === "idle" && <p className="nl-daily-report-intro">
      Generate a reflection from your recorded meals and activity. It stays only on this screen.
    </p>}
    {state === "generating" && <div className="nl-daily-report-status" role="status">
      <button className="nl-button nl-button-primary" disabled>Generating report…</button>
      <p>Looking across your recorded day.</p>
    </div>}
    {state === "error" && <div className="nl-alert" role="alert">{error}</div>}
    {state === "ready" && report && <>
      <div className="nl-daily-report-insights">
        <article><span>Nutrition</span><p>{report.nutrition_insight}</p></article>
        <article><span>Activity</span><p>{report.activity_insight}</p></article>
      </div>
      <div className="nl-daily-report-sections">
        <section><h3>Next actions</h3><ul>{report.next_actions.map((action, index) =>
          <li key={index}>{action}</li>)}</ul></section>
        <section><h3>Limitations</h3><ul>{report.limitations.map((limitation, index) =>
          <li key={index}>{limitation}</li>)}</ul></section>
      </div>
      <p className="nl-daily-report-note">This report is a coaching suggestion based on recorded data, not medical advice.</p>
    </>}
  </section>;
}
