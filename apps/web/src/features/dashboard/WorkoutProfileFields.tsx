import type { WorkoutProfileUpdate } from "@nourishloop/api-client/schema";

const EQUIPMENT = [
  ["bodyweight", "Bodyweight"], ["machine", "Machines"],
  ["dumbbell", "Dumbbells"], ["cable", "Cable machine"],
] as const;

export default function WorkoutProfileFields({ value, onChange }: {
  value: WorkoutProfileUpdate;
  onChange: (value: WorkoutProfileUpdate) => void;
}) {
  return <>
    <div className="nl-profile-fields">
      <label className="nl-field-label">Training experience
        <select aria-label="Workout stage" value={value.stage}
          onChange={event => onChange({
            ...value, stage: event.target.value as WorkoutProfileUpdate["stage"],
          })}>
          <option value="beginner">Beginner · building consistency</option>
          <option value="intermediate">Intermediate · regular training</option>
          <option value="advanced">Advanced · experienced</option>
        </select>
      </label>
      <label className="nl-field-label">Training days per week
        <select aria-label="Workout days per week" value={value.days_per_week}
          onChange={event => onChange({ ...value, days_per_week: Number(event.target.value) })}>
          {[1, 2, 3, 4, 5, 6].map(day => <option value={day} key={day}>{day}</option>)}
        </select>
      </label>
    </div>
    <h3>Equipment you can use</h3>
    <div className="nl-option-grid">{EQUIPMENT.map(([item, label]) =>
      <label className="nl-check-option" key={item}>
        <input type="checkbox" checked={value.equipment.includes(item)}
          onChange={event => onChange({
            ...value,
            equipment: event.target.checked ? [...value.equipment, item]
              : value.equipment.filter(equipment => equipment !== item),
          })} />
        {label}
      </label>)}</div>
  </>;
}
