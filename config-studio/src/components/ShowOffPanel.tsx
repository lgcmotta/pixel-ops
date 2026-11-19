export type ShowOffConfig = { enabled?: boolean; run_id?: string; owner?: string; repositories?: string[] };

export function ShowOffPanel({ value, onChange }: { value: ShowOffConfig; onChange: (value: ShowOffConfig) => void }) {
  return <div className="field field-wide">
    <span>Demo / Show off · recording mode</span>
    <label><input type="checkbox" checked={Boolean(value.enabled)} onChange={event => onChange({ ...value, enabled: event.target.checked, run_id: crypto.randomUUID() })} /> Enable Show off mode</label>
    <button className="secondary-button" onClick={() => onChange({ ...value, enabled: true, run_id: crypto.randomUUID() })}>Start / restart loop</button>
    <small>Save JSON to start or restart. Kraken shows temperatures for 5 seconds, then a five-minute Standup countdown. The first simulated PR arrives 5 seconds later. Further PRs rotate through sample repositories after each capture, with an 8-second countdown pause between them.</small>
    <small>The meeting shows “Starting now” briefly, then temperatures return for 10 seconds. The loop restarts automatically while enabled; the next 5-second intro gives 15 uninterrupted seconds of temperatures between countdowns. Battles finish fully before the loop can move on.</small>
    <small>Real meetings and work activity are hidden. Only PRs owned by an explicitly configured demo account may appear alongside the simulated PR. Demo captures stay out of your saved history. Screen rotation is paused while recording.</small>
    <small>To finish, uncheck Show off mode and Save JSON. Normal calendar and PR coverage returns.</small>
  </div>;
}
