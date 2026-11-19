import { useEffect, useState } from "react";

type QuotaStatus = {
  status: string; account?: string; plan?: string; observed_at?: string;
  windows?: Array<{ bucket: string; label: string; window_minutes: number; used_percent: number; reset_at: string | null }>;
  authUrl?: string; verificationUrl?: string; userCode?: string;
};

async function accountAction(action: string, body?: object): Promise<QuotaStatus> {
  const response = await fetch(`/api/codex-account/${action}`, {
    method: body ? "POST" : "GET", headers: body ? { "content-type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || "Account connection unavailable");
  return value;
}

export function CodexAccountPanel() {
  const [state, setState] = useState<QuotaStatus>({ status: "loading" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [tick, setTick] = useState(Date.now());
  async function run(action: string, body?: object) {
    setBusy(true); setError("");
    try { setState(await accountAction(action, body)); }
    catch (reason) { setError(String(reason)); }
    finally { setBusy(false); }
  }
  const pending = state.status === "pending";
  useEffect(() => {
    if (pending) return;
    let active = true;
    let running = false;
    async function refresh() {
      if (running) return;
      running = true;
      try {
        const value = await accountAction("status");
        if (active) { setState(value); setError(""); }
      } catch { if (active) setError("Account connection unavailable. Check the configured Codex executable."); }
      finally { running = false; }
    }
    void refresh();
    const timer = setInterval(() => void refresh(), 60000);
    return () => { active = false; clearInterval(timer); };
  }, [pending]);
  useEffect(() => {
    if (state.status !== "pending") return;
    let active = true;
    let running = false;
    const timer = setInterval(async () => {
      if (running) return;
      running = true;
      try {
        let value = await accountAction("login/status");
        if (value.status === "connected") value = await accountAction("refresh", {});
        if (active) setState(value);
      } catch { if (active) { setState({ status: "failed" }); setError("Sign-in connection failed. Try again."); } }
      finally { running = false; }
    }, 1500);
    return () => { active = false; clearInterval(timer); };
  }, [state.status]);
  useEffect(() => { const timer = setInterval(() => setTick(Date.now()), 1000); return () => clearInterval(timer); }, []);
  const age = state.observed_at ? tick - new Date(state.observed_at).getTime() : Infinity;
  return <section className="codex-account-connection">
    <h3>Codex account</h3>
    <p>Account-wide quota across your devices. This connection has its own local login.</p>
    <p role="status">{state.account || "Not connected"}{state.plan ? ` · ${state.plan}` : ""} · {state.status}{age > 180000 && state.observed_at ? " · stale" : ""}</p>
    <div className="runtime-actions">
      <button className="primary-button" disabled={busy || state.status === "pending"} onClick={() => void run("login/start", { flow: "browser" })}>Sign in with browser</button>
      <button className="secondary-button" disabled={busy || state.status === "pending"} onClick={() => void run("login/start", { flow: "device" })}>Use device code</button>
      <button className="secondary-button" disabled={busy || state.status === "pending"} onClick={() => void run("refresh", {})}>Refresh</button>
      <button className="secondary-button" disabled={busy} onClick={() => void run(state.status === "pending" ? "login/cancel" : "disconnect", {})}>{state.status === "pending" ? "Cancel sign-in" : "Disconnect"}</button>
    </div>
    {state.authUrl && <p><a className="secondary-button" href={state.authUrl} target="_blank" rel="noreferrer">Open official sign-in page</a></p>}
    {state.verificationUrl && <p><a href={state.verificationUrl} target="_blank" rel="noreferrer">Open verification page</a> · Code: <strong>{state.userCode}</strong></p>}
    {state.status === "pending" && <p>Complete sign-in in your browser. This page checks automatically.</p>}
    {error && <p role="alert">{error}</p>}
    <ul>{state.windows?.map((window, index) => {
      const seconds = window.reset_at ? Math.max(0, Math.floor((new Date(window.reset_at).getTime() - tick) / 1000)) : null;
      const available = state.status === "ok" && age <= 180000 && seconds !== 0;
      return <li key={`${window.bucket}-${index}`}>
        {window.label} · {window.window_minutes} minute window · {available ? `${(100 - window.used_percent).toFixed(0)}% remaining` : seconds === 0 ? "Refreshing after reset" : "Unavailable / stale"}
        {seconds !== null && seconds > 0 ? ` · resets in ${Math.floor(seconds / 3600)}h ${Math.floor(seconds % 3600 / 60)}m` : ""}
      </li>;
    })}</ul>
    {state.observed_at && <small>Last successful update: {new Date(state.observed_at).toLocaleTimeString()}</small>}
  </section>;
}
