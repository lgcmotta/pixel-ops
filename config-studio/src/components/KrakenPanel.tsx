export type KrakenWebConfig = {
  enabled?: boolean;
  port?: number;
  pr_battles?: boolean;
  meeting_countdown?: boolean;
};

export function KrakenPanel({ value, onChange }: { value: KrakenWebConfig; onChange: (value: KrakenWebConfig) => void }) {
  const url = `http://127.0.0.1:${value.port ?? 8767}/kraken/`;
  return <div className="field field-wide">
    <span>NZXT Kraken · Pokémon thermal display</span>
    <label><input type="checkbox" checked={Boolean(value.enabled)} onChange={event => onChange({ ...value, enabled: event.target.checked })} /> Serve local CAM Web Integration</label>
    <label>Local port <input type="number" min={1024} max={65535} value={value.port ?? 8767} onChange={event => {
      const port = Number(event.target.value);
      if (Number.isInteger(port) && port >= 1024 && port <= 65535) onChange({ ...value, port });
    }} /></label>
    <label><input type="checkbox" checked={value.pr_battles !== false} onChange={event => onChange({ ...value, pr_battles: event.target.checked })} /> Mirror new PR Pokémon battles</label>
    <label><input type="checkbox" checked={value.meeting_countdown !== false} onChange={event => onChange({ ...value, meeting_countdown: event.target.checked })} /> Meeting countdown: 5 minutes before until 1 minute after</label>
    <a href={url} target="_blank" rel="noreferrer">Open Kraken preview</a>
    <code>{url}</code>
    <small>Paste this URL in NZXT CAM → Web Integration → Custom. Live temperatures come from CAM. PR battles interrupt the countdown and return to it while its time window remains active.</small>
    <small>Save configuration first. Enable/port changes require Restart display; battle and countdown switches reload automatically. Config Studio can be stopped afterwards.</small>
  </div>;
}
