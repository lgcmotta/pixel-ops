import { useState } from "react";

export function DesktopMonitorPanel({ value, onChange }: { value: { borderless?: boolean; monitor?: number | null }; onChange: (value: { borderless?: boolean; monitor?: number | null }) => void }) {
  const [monitors, setMonitors] = useState<Array<{ index: number; width: number; height: number }>>([]);
  const [error, setError] = useState("");
  async function scan() {
    try {
      const response = await fetch("/api/monitors");
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error);
      setMonitors(payload); setError("");
    } catch { setError("Could not list monitors. Enable the Lian Li secondary-screen mode and retry."); }
  }
  return <div className="field field-wide">
    <span>Desktop monitor · restart required</span>
    <label><input type="checkbox" checked={Boolean(value.borderless)} onChange={event => onChange({ ...value, borderless: event.target.checked })} /> Borderless display</label>
    <select value={value.monitor ?? "auto"} onChange={event => onChange({ ...value, monitor: event.target.value === "auto" ? null : Number(event.target.value) })}>
      <option value="auto">Auto: unique monitor matching output resolution</option>
      {value.monitor != null && !monitors.some(item => item.index === value.monitor) && <option value={value.monitor}>Saved monitor {value.monitor}</option>}
      {monitors.map(item => <option key={item.index} value={item.index}>Monitor {item.index}: {item.width} × {item.height}</option>)}
    </select>
    <button className="secondary-button" onClick={() => void scan()}>Detect monitors</button>
    {error && <span role="alert">{error}</span>}
  </div>;
}
