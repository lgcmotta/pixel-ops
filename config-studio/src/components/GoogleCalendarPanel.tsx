import { useEffect, useState } from "react";

type Calendar = { id: string; label: string; access_role: string; primary: boolean };
type State = { status: string; client_configured?: boolean; auth_url?: string; calendars?: Calendar[] };
async function action(name: string, body?: object): Promise<State> {
  const response = await fetch(`/api/google-calendar/${name}`, { method: body ? "POST" : "GET", headers: body ? { "content-type": "application/json" } : undefined, body: body ? JSON.stringify(body) : undefined });
  const value = await response.json();
  if (!response.ok) throw Error(value.error || "Google Calendar unavailable");
  return value;
}

export default function GoogleCalendarPanel({ selected, onSelect }: { selected: string[]; onSelect: (ids: string[]) => void }) {
  const [state, setState] = useState<State>({ status: "checking" });
  const [calendars, setCalendars] = useState<Calendar[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [clientFilename, setClientFilename] = useState("");
  const [showClientPicker, setShowClientPicker] = useState(false);
  async function run(name: string, body?: object) {
    setBusy(true); setError("");
    try {
      const value = await action(name, body);
      setState(previous => ({ ...previous, ...value }));
      if (value.calendars) setCalendars(value.calendars);
      if (name === "disconnect" || name === "client/import") { setCalendars([]); onSelect([]); }
      return true;
    } catch (reason) { setError(String(reason)); return false; }
    finally { setBusy(false); }
  }
  useEffect(() => { let active = true; action("status").then(value => { if (active) setState(value); }).catch(() => { if (active) setError("Calendar status unavailable"); }); return () => { active = false; }; }, []);
  useEffect(() => {
    if (state.status !== "pending") return;
    let active = true; let running = false;
    const timer = setInterval(async () => {
      if (running) return;
      running = true;
      try {
        let value = await action("login/status");
        if (value.status === "connected") value = await action("calendars");
        if (active) { setState(previous => ({ ...previous, ...value })); if (value.calendars) setCalendars(value.calendars); }
      } catch { if (active) setError("Calendar sign-in failed; check Google client and permissions"); }
      finally { running = false; }
    }, 1500);
    return () => { active = false; clearInterval(timer); };
  }, [state.status]);
  return <section className="field-wide google-calendar-connection">
    <h3>Connect Google Calendar</h3>
    <p>Sign into the Google account that can read the calendars you want to display. Only calendar-list and event read access is requested.</p>
    <p>First create a Google Cloud OAuth <strong>Desktop app</strong> client with Calendar API enabled. For a personal Gmail login, its audience must be External.</p>
    {state.client_configured && <p role="status">{clientFilename ? `Imported ${clientFilename}. ` : "Desktop client is configured. "}Stored locally and ready for Google sign-in. No need to choose the file again.</p>}
    {state.client_configured && !showClientPicker ? <button className="secondary-button" disabled={busy || state.status === "pending"} onClick={() => setShowClientPicker(true)}>Replace Desktop client JSON</button> : <label>{state.client_configured ? "Replace Desktop client JSON (optional)" : "Import downloaded Google client JSON (stored locally)"}
      <input type="file" accept=".json,application/json" disabled={busy || state.status === "pending"} onChange={event => {
        const file = event.target.files?.[0];
        if (file) void file.text().then(async text => {
          if (await run("client/import", { client: JSON.parse(text) })) {
            setClientFilename(file.name);
            setShowClientPicker(false);
          }
        }).catch(() => setError("Select a valid Google Desktop app JSON file"));
      }} />
    </label>}
    <p role="status">{state.status}{state.client_configured ? " · Desktop client configured" : ""}</p>
    <div className="runtime-actions">
      <button className="primary-button" disabled={busy || state.status === "pending" || (!state.client_configured && state.status !== "connected")} onClick={() => void run("login/start", {})}>Sign in with Google</button>
      <button className="secondary-button" disabled={busy || state.status === "pending"} onClick={() => void run("calendars")}>Load shared calendars</button>
      <button className="secondary-button" disabled={busy} onClick={() => void run(state.status === "pending" ? "login/cancel" : "disconnect", {})}>{state.status === "pending" ? "Cancel sign-in" : "Disconnect"}</button>
    </div>
    {state.auth_url && state.status === "pending" && <p><a href={state.auth_url} target="_blank" rel="noreferrer">Open Google sign-in page</a></p>}
    {error && <p role="alert">{error}</p>}
    {calendars.map(calendar => <label key={calendar.id} className="calendar-choice">
      <input type="checkbox" checked={selected.includes(calendar.id)} disabled={["none", "freeBusyReader"].includes(calendar.access_role)} onChange={event => onSelect(event.target.checked ? [...selected, calendar.id] : selected.filter(id => id !== calendar.id))} />
      {" "}{calendar.label} · {calendar.access_role}
    </label>)}
    <p>Select your calendars, then save configuration. Calendar selections are saved locally.</p>
    <p className="field-help">Google External apps in Testing issue refresh tokens that expire after seven days. See the local Google Calendar setup guide before enabling unattended use.</p>
  </section>;
}
