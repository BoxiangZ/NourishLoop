import type { MeRead, PlanProgressRead } from "@nourishloop/api-client/schema";

const GOALS: Record<MeRead["goal"]["goal"], string> = {
  eat_healthier: "Eat healthier",
  reduce_body_fat: "Reduce body fat",
  build_muscle: "Build muscle",
};
const monthDay = new Intl.DateTimeFormat("en-HK", { day: "numeric", month: "short", timeZone: "UTC" });

export default function PlanProgressCard({ progress, goal, onEditGoal }: {
  progress: PlanProgressRead | null;
  goal?: MeRead["goal"]["goal"];
  onEditGoal: () => void;
}) {
  const current = progress?.weeks.at(-1);
  return <section className="nl-plan-progress" aria-label="Four-week plan progress">
    <div className="nl-plan-progress-header">
      <h2>Four-week progress</h2>
      {goal && <p>{GOALS[goal]} <button type="button" className="nl-text-link" onClick={onEditGoal}>Edit goal</button></p>}
    </div>
    {progress && current ? <>
      <div className="nl-plan-progress-metrics">
        <div><strong>{current.meal_days}{progress.meal_days_target !== null && ` / ${progress.meal_days_target}`}</strong>
          <span>days with a meal logged this week</span></div>
        <div><strong>{current.training_days} / {progress.training_days_target}</strong>
          <span>training days toward this week’s goal</span></div>
      </div>
      <div className="nl-progress-weeks">{progress.weeks.map(week => {
        const title = week.starts_on === current.starts_on ? "This week" : monthDay.format(new Date(week.starts_on));
        return <div className="nl-progress-week" key={week.starts_on} data-current={week.starts_on === current.starts_on}>
          <strong>{title}</strong>
          <div><progress max={7} value={week.meal_days} aria-label={`${title}: days with a meal logged`} />
            <span>{week.meal_days} meal {week.meal_days === 1 ? "day" : "days"}</span></div>
          <div><progress max={7} value={week.training_days} aria-label={`${title}: training days`} />
            <span>{week.training_days} training {week.training_days === 1 ? "day" : "days"}</span></div>
        </div>;
      })}</div>
    </> : <p role="status">Loading plan progress…</p>}
  </section>;
}
