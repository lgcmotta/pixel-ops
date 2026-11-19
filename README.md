# Pixel OPs

## Lian Li Windows setup

The 8.8-inch US88v1 supports direct USB output from the signed-in Pixel Ops
runtime. Stop the current display instance, turn off **Secondary screen** in
L-Connect 3, and select `lian_li_usb` in the display's **Output** field in Config
Studio. Save and start the configured runtime. If access to the LCD is denied,
check whether L-Connect 3 or another display app still owns it. This mode uses
the existing Windows WinUSB driver and can keep sending frames through Win+L
while the PC stays awake.

```powershell
.venv/Scripts/python.exe pixel_ops/main.py --plugin pokemon --output lian_li_usb --forever
```

For desktop window mode, enable **Secondary screen**, select `window`, and use
Config Studio's **Detect monitors** control. Auto selection requires a unique
1920x480 display. Kraken uses the local Pokémon thermal web view through NZXT CAM.

```powershell
.venv/Scripts/python.exe pixel_ops/main.py --plugin pokemon --output window --forever
# Normal reduced window for setup, without the secondary display:
.venv/Scripts/python.exe pixel_ops/main.py --plugin pokemon --output window --window-preview --forever
```

In Config Studio, open **Codex Account**, select **Sign in with browser**, then
open the official sign-in link. **Use device code** is the fallback when enabled
for your account. Codex CLI must be installed; its executable path is configurable.
Complete authentication yourself. PixelOps uses a separate Git-ignored login at
`pixel_ops/cache/codex_account`; no API key or macOS helper is required.

The **AI USAGE** HUD displays account-wide remaining percentages and reset times from
the service, including multiple quota buckets. It polls every 60 seconds and
marks data stale after three minutes. An elapsed reset waits for fresh service
data. Optional account token summaries are displayed only when returned; local
chat totals never establish remaining allowance. Closing Studio does not stop
runtime collection. Disconnect affects only the PixelOps login.

Each compact provider block shows its window, remaining allowance/reset countdown,
exact reported account-token total with date when available, and update time.
Two blocks fit the widescreen panel; additional windows/providers paginate without
combining their totals. Codex usage stays live during Demo / Show off mode. Other
account providers can use the same neutral quota observation; connecting Claude
would still require its own integration.

**PC Stats** uses psutil for CPU/RAM and one nvidia-smi query for GPU
utilization/VRAM per sample. In **GitHub**, connect your account and enable owned-repository discovery;
add selected organization/external repositories to the explicit list. Accessible
draft and non-draft PRs both participate. Credentials stay in the local `.env`.
The PR panel pages through inventory, including older open PRs. The first scan
silently establishes a baseline; only new PR creations after that baseline
trigger captures in this setup. Deduplication survives runtime restarts, edits,
draft promotion and reopening. Recent unseen PRs can catch up within the one-hour
startup lookback; older downtime history does not generate a capture backlog.
Set `ambient_particles` to false in the game layout to disable flashing sparks.
Restart the runtime after changing credentials or display/monitor settings.
GitHub's 60-second polling default is a minimum; large repository sets poll less
frequently to stay within the API budget and honor server rate-limit cooldowns.
Calendar/weather integrations may be configured separately; they are disabled
until personalized. Optional AI generation and per-chat Codex monitoring are off.

To keep machine-specific settings out of Git, copy `display.json` to
`display.local.json` in `pixel_ops/config/`. An optional `integrations` object
in `integrations.local.json` provides the same kind of override for integrations.
The runtime and local Config Studio use these files when present.

For Google account sign-in and selection of shared calendars, follow
[Google Calendar setup](docs/google-calendar-setup.md). A Workspace-owned Cloud
project can supply the Desktop client while the personal Gmail supplies calendar
access. The OAuth integration stays disabled until client setup and calendar
selection are complete.

The widescreen top bar pins the next timed meeting beside the clock in one line:
**Next: Meeting / HH:MM   Later Today: Meeting / HH:MM**. Both sections use the
same dark text. **Later today** cycles through the remaining upcoming
meetings every 10 seconds, excluding the pinned meeting, shared duplicates,
all-day entries, and meetings that have already started. Times and day boundaries
use the display timezone. When the next meeting starts, the following one takes
its place; an empty carousel shows **No more meetings today**.

### NZXT Kraken companion

In Config Studio's Display panel, enable **NZXT Kraken**, save, and restart the
display. Enter `http://127.0.0.1:8767/kraken/` in NZXT CAM → Web Integration →
Custom. CAM supplies live CPU/GPU/coolant temperatures; NVIDIA temperature also
has a fallback through the existing PC Stats sample (`gpu_temperature` field).
An ordinary browser shows available fallback readings and setup instructions.
The setup page includes clearly
labelled sample previews. No public website is needed. Keep CAM running.

The circular view normally shows temperatures. From five minutes before a timed
meeting until one minute after its start, it shows the name, start time, calendar
name and countdown. A new-PR Pokémon battle temporarily takes over, sharing the
primary world's Pokémon and phase clock. Afterwards it returns to the countdown
if that absolute window is still active, otherwise to temperatures. A small
temperature strip stays visible during both takeovers. Old PR inventory never
triggers the mirror. Calendar names populate on the next successful Google refresh.

PR encounter headings include `owner/repository#PR-number POKEMON`, in both live
and Show off modes. The reference remains visible through the capture on the
widescreen and Kraken. The PR number is independent of the Pokémon's Pokédex ID.

The runtime serves the page independently of Config Studio and starts with the
existing PixelOps desktop task. `display.kraken_web` contains `enabled`, `port`
(default 8767), `pr_battles`, and `meeting_countdown`. Enable/port changes require
restart; the two takeover switches hot reload. The page adapts to CAM's injected
dimensions, shape and frame budget, with rendering capped at 30 FPS. If a machine
restart loads CAM before PixelOps, use CAM's refresh button after PixelOps starts.
There is no new scheduled task to register.

### Recording a Demo / Show off video

In Config Studio → Display → **Demo / Show off**, click **Start / restart loop**
and **Save JSON**. Start filming before saving to capture the five-second Kraken
temperature intro. A five-minute **Standup Meeting** countdown follows. Five
seconds later a simulated PR triggers the same Pokémon battle on the configured
views. After the entire capture/resume sequence finishes, the
countdown gets eight seconds of breathing room before another PR arrives. PRs
rotate through your repositories, with no overlapping captures or queued backlog.

Near meeting start, new captures pause so the countdown can reach **Starting
now**. Five seconds after the start, once any capture is finished, Kraken returns
to temperatures for ten seconds. The loop then restarts automatically with its
five-second intro, giving fifteen uninterrupted temperature seconds between
countdowns. The default loop is approximately five minutes twenty seconds. The
Lian Li's Next and Later Today sections use dummy standup, grooming, planning and
review meetings. Restart returns to the intro; disabling the mode stops looping.

Real meetings and work activity are hidden. Real PR listings require an explicit
demo repository owner. Demo captures are never written to normal
history. CPU/GPU/RAM, CAM temperatures and account quota stay live. Screen rotation
is paused while Show off is enabled. To return to normal coverage, uncheck the
mode and **Save JSON**. The setting is `display.show_off` and defaults off. An
optional local `owner` and list of `repositories` customize the demo inventory.

Validation: `python -m pytest -q`, and in `config-studio`, `npm run build`,
`npm run lint`, and `npm run test:account`. The browser model tests run with
`node --test tests/kraken_model.test.mjs` from the repository root.

[![License](https://img.shields.io/github/license/marcelors27/pixel-ops)](LICENSE)
![Last commit](https://img.shields.io/github/last-commit/marcelors27/pixel-ops)
![Repo size](https://img.shields.io/github/repo-size/marcelors27/pixel-ops)
![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)

<img src="pixel_ops/assets/logo/pixel_ops_gaco_logo.jpg" alt="Pixel OPs logo" width="512">

Pixel Ops is an event-driven runtime for ambient pixel-art worlds. Integrations translate outside activity into neutral events, a selected game engine owns its projections and visual rules, and output drivers deliver frames to files, windows, or hardware. Pokemon is the default game engine, not the platform model; Spaceship is the first independent persistent world.

The display is intentionally ambient. Meetings become encounters, pull requests become world events, Discord voice state becomes map companions, and operational pressure becomes mood instead of a notification wall.

## Quick Start

```bash
python pixel_ops/main.py --plugin pokemon --output preview
python pixel_ops/main.py --plugin spaceship --output preview
python pixel_ops/main.py --plugin pokemon --output window --forever
python pixel_ops/main.py --plugin pokemon --output gif --seconds 8
python pixel_ops/main.py --plugin pokemon --output turzx --forever --fps 10 --offline
python pixel_ops/main.py --plugin pokemon --output thermalright --forever --fps 2 --offline
python pixel_ops/main.py --plugin pokemon --output lcd --forever --fps 10 --offline
```

Window mode:

```bash
python pixel_ops/main.py --plugin pokemon --window --forever
python pixel_ops/main.py --plugin pokemon --window --window-scale 1 --forever
python pixel_ops/main.py --plugin pokemon --window --window-scale 3 --forever
```

Local outputs:

```text
pixel_ops/output/preview.png
pixel_ops/output/preview.gif
```

Platform setup and USB display notes:

- [Linux](docs/linux.md)
- [Windows](docs/windows.md)

## Platform Support

Supported development/runtime targets:

- Linux: `preview`, `gif`, `window`, and TURZX USB with libusb plus udev permissions.
- Windows: `preview`, `gif`, `window`, and TURZX USB with a WinUSB/libusb driver such as Zadig.
- macOS: useful for development and preview/window output, but USB display support is not the primary target.

Run the platform check before testing hardware:

```bash
python scripts/linux_check.py
python scripts/windows_check.py
```

Both checks validate Python dependencies, local system tools, PC stats availability, and expected TURZX USB setup. CI runs Linux and Windows workflows for Python tests, Config Studio build, and offline preview rendering.

## Config Studio

Windows tray controls and owner-run scheduled-task setup are documented in
[tools/windows/README.md](tools/windows/README.md). The display task starts at
sign-in; Studio can run on demand. Stopping Studio leaves the display running.

Config Studio is the local React UI for editing runtime JSON config.

```bash
cd config-studio
npm install
npm run dev
```

The dev server exposes local endpoints that read and write repository JSON files. The packaged Electron app starts the same local server against the bundled Pixel OPs runtime; on Windows the installer creates Start Menu and desktop shortcuts for `Pixel OPs Config Studio`.

Config Studio detects available visual plugins from `pixel_ops/plugins/*/plugin.py`, loads plugin-owned JSON only when the plugin is selected, and detects integrations from `pixel_ops/integrations/*/plugin.py`.

## Configuration

JSON is the primary runtime config format. Matching YAML files are fallback only.

Core config:

- `pixel_ops/config/display.json`: display size, FPS, output target, AI decision config, splash, and HUD layout.
- `pixel_ops/config/people.json`: people and time zones.
- `pixel_ops/config/integrations.json`: integration enables and non-secret provider settings.

Pokemon plugin config:

- `pixel_ops/plugins/pokemon/game.json`: scene timing, HUD/game layout, events, and Pokemon selection behavior.
- `pixel_ops/plugins/pokemon/pokemon.json`: PokeAPI, cache, sprite, and offline settings.
- `pixel_ops/plugins/pokemon/companions.json`: Pokemon-specific visual mapping for Discord companions.

Spaceship plugin config:

- `pixel_ops/plugins/spaceship/game.json`: procedural layout seed, active-time progression, save cadence, palette, and event settings.
- `pixel_ops/plugins/spaceship/assets/`: local PixelLab-generated ship, crew, interior, and asteroid sprites.

Integration sidecars:

- `pixel_ops/config/discord_people.json`: recent Discord users and nicknames observed from voice state.

Secrets stay in `.env`. Runtime toggles, guild IDs, repo lists, city names, sprite choices, and other UI-editable values stay in JSON.

Secret env vars currently used:

```env
PIXEL_OPS_SLACK_APP_TOKEN=xapp-...
PIXEL_OPS_SLACK_BOT_TOKEN=xoxb-...
PIXEL_OPS_KITE_TOKEN=...
PIXEL_OPS_DISCORD_BOT_TOKEN=...
PIXEL_OPS_ZOOM_ACCOUNT_ID=...
PIXEL_OPS_ZOOM_CLIENT_ID=...
PIXEL_OPS_ZOOM_CLIENT_SECRET=...
PIXEL_OPS_GITHUB_TOKEN=github_pat_...
PIXEL_OPS_CLICKUP_TOKEN=pk_...
OPENAI_API_KEY=sk-...
OPENAI_ADMIN_KEY=sk-admin-...
OPENWEATHERMAP_API_KEY=...
```

## Runtime Architecture

```text
provider transport
  -> integration event source
  -> WorkEvent / PixelOpsEvent
  -> selected GameEngine
  -> game-owned projection and renderer
  -> output driver
```

`PixelOpsApp` never queries provider-specific state or assembles a scene-shaped render call. It delivers events, emits `runtime.tick`, and requests a frame. The selected engine decides how calendar, GitHub, weather, social presence, tasks, local metrics, media, and AI usage affect its world.

Snapshot APIs are adapted into observation events. Important event types include `calendar.today_updated`, `github.pull_requests_updated`, `weather.conditions_updated`, `system.metrics_updated`, `tasks.snapshot_updated`, and `social.companions_updated`.

See [ADR 0026](docs/adr/0026-all-game-inputs-are-platform-events.md) for the boundary and migration constraints.

## Extension Types

Pixel OPs has three plugin-style boundaries:

- game engines consume events, own projections, and render a world;
- integration plugins collect outside activity and emit neutral events;
- AI decision plugins provide optional structured model decisions.

### Game Engine Plugins

Game plugins live in `pixel_ops/plugins/<name>/`. They own a complete display experience, event projections, world rules, and rendering.

Games consume `WorkEvent` and `PixelOpsEvent` through the `GameEngine` contract. They must not make provider transport calls or receive provider source objects directly.

The visual plugin object contract is duck-typed by `pixel_ops/main.py`:

- `name`: stable CLI/config key.
- `display_name`: human-readable name for UI tooling.
- `add_arguments(parser)`: optional CLI flags.
- `load_config(plugin_dir, load_config)`: load plugin-owned JSON config.
- `maybe_handle_command(args, root_dir, config)`: handle one-shot commands.
- `fps(config, display_fps)`: choose render FPS.
- `event_config(config)`: expose event settings to the runtime.
- `build_app(...)`: construct a `GameEngine` and return a `PixelOpsApp` wired only to event sources.

To create a visual plugin:

1. Create `pixel_ops/plugins/<name>/plugin.py`.
2. Add plugin JSON files under that directory.
3. Implement the plugin class.
4. Register it in `pixel_ops/plugins/registry.py`.
5. Build game-owned projections from events instead of importing provider transports or sources.
6. Add documentation and an ADR when changing runtime boundaries or event semantics.

Game-specific docs:

- [Pokemon plugin documentation](pixel_ops/plugins/pokemon/README.md)
- [Spaceship plugin documentation](pixel_ops/plugins/spaceship/README.md)

### Integration Plugins

Integration plugins live in `pixel_ops/integrations/<name>/plugin.py`. They own provider setup, polling, sockets, local file reads, and normalization.

Integration plugins implement the protocol in `pixel_ops/integration_plugins/base.py`:

- `name`: stable key under `pixel_ops/config/integrations.json`.
- `enabled(ctx)`: decide whether the plugin should load.
- `build(ctx)`: return an `IntegrationContribution`.

`IntegrationContribution` can provide only event and lifecycle boundaries:

- `event_sources`;
- `calendar_paths`;
- `starters`;
- `warmers`;
- `closers`;

To create an integration plugin:

1. Create `pixel_ops/integrations/<name>/plugin.py`.
2. Add a class with `name`, `enabled(ctx)`, and `build(ctx)`.
3. Return normalized contributions only.
4. Add the module to `PLUGIN_MODULES` and env fallback to `PLUGIN_ENABLES`.
5. Add non-secret config under `pixel_ops/config/integrations.json`.
6. Keep secrets in `.env` and reference them from JSON by env var name.
7. Normalize social/meeting activity through `AmbientSignal` and `WorkEvent`.

Provider integrations must not render raw messages, provider payloads, or chat feeds.

### AI Decision Plugins

AI decision plugins live under `pixel_ops/plugins/ai/`. They are not visual plugins.

The protocol in `pixel_ops/plugins/ai/plugin.py` is:

- `enabled`: boolean.
- `decide_json(request)`: return a JSON object matching the request schema, or `None`.

Rules:

- calls are optional;
- successful decisions should be cached when practical;
- return `None` on disabled config, missing keys, API errors, or invalid JSON;
- keep provider-specific API code in the AI plugin, not visual scenes.

To add an AI provider, implement the protocol, extend `build_ai_plugin()`, add JSON config under `display.ai`, and document any new secret env vars.

## Integrations

All providers normalize into ambient state. Social/meeting providers first produce `AmbientSignal`, then `WorkEvent`. The common vocabulary lives in `pixel_ops/events/ambient_signals.py`.

### Calendars

Local ICS file:

```bash
python pixel_ops/main.py --ics path/to/calendar.ics
```

ICS config:

```json
{
  "integrations": {
    "ics": {
      "enabled": true,
      "paths": ["/path/to/calendar.ics"],
      "poll_seconds": 300
    }
  }
}
```

Google Calendar via private ICS URL:

```json
{
  "integrations": {
    "google_calendar": {
      "enabled": true,
      "ics_urls": ["https://calendar.google.com/calendar/ical/..."],
      "poll_seconds": 300
    }
  }
}
```

### GitHub

```json
{
  "integrations": {
    "github": {
      "enabled": true,
      "token_env": "PIXEL_OPS_GITHUB_TOKEN",
      "repos": ["owner/repo"],
      "poll_seconds": 60,
      "max_pull_requests": 4,
      "fetch_deployments": true,
      "deployment_workflows": []
    }
  }
}
```

GitHub pull requests feed the compact HUD. When `fetch_deployments` is enabled, recent GitHub Actions workflow runs are normalized into ambient deploy/build events. Leave `deployment_workflows` empty to observe all workflows.

### ClickUp

```json
{
  "integrations": {
    "clickup": {
      "enabled": true,
      "token_env": "PIXEL_OPS_CLICKUP_TOKEN",
      "team_id": "",
      "assignee_id": "",
      "poll_seconds": 120,
      "max_tasks": 5,
      "due_within_days": 14
    }
  }
}
```

ClickUp tasks feed the optional `tasks` HUD window with assigned task names, due dates, and remaining time. Leave `team_id` and `assignee_id` empty to resolve the first authorized Workspace and current API user.

### Capacities Project Radar

Capacities can feed the optional `project_radar` HUD with one active project, one project that needs to resurface, and compact Inbox/Review pressure counts. Create a custom Capacities object type named `Projeto` or `Project` with any of these properties (Portuguese and English names are both discovered):

- `Estado` / `State` or `Status`
- `Área` / `Area`
- `Próxima ação` / `Next action`
- `Revisitar em` / `Review date`
- `Último toque` / `Last touched`
- `Importância` / `Importance`

Create a read-only personal token under Capacities Settings → Capacities API and store it in `.env`:

```bash
PIXEL_OPS_CAPACITIES_TOKEN=cap-api-...
```

Enable `capacities` in `pixel_ops/config/integrations.json`, then add a `project_radar` HUD window in Config Studio. The Capacities MCP connection used by AI clients is separate from this unattended runtime token.

### Weather

```json
{
  "integrations": {
    "weather": {
      "enabled": true,
      "provider": "open_meteo",
      "city": "Porto Alegre",
      "country_code": "BR",
      "poll_seconds": 900,
      "timeout_seconds": 8,
      "api_key_env": "OPENWEATHERMAP_API_KEY"
    }
  }
}
```

Supported providers:

- `open_meteo`: default, no key.
- `wttr_in`: no key.
- `openweathermap`: requires the configured API key env var.

### AI Usage

```json
{
  "integrations": {
    "ai_usage": {
      "enabled": true,
      "providers": ["codex", "claude", "openai_api"],
      "poll_seconds": 300,
      "codex_home": "~/.codex",
      "claude_projects_path": "~/.claude/projects",
      "openai_admin_key_env": "OPENAI_ADMIN_KEY",
      "thresholds": [75, 90]
    }
  }
}
```

Supported sources:

- Codex local JSONL sessions under `CODEX_HOME` or `~/.codex`.
- Claude local JSONL project logs under `~/.claude/projects`.
- OpenAI Admin API usage/cost endpoints via `OPENAI_ADMIN_KEY`.

Pixel OPs renders this as ambient gauges and threshold events, not billing tables or token logs.

### Codex Semaphore

Add **Codex Semaphore** in Config Studio's layout editor. The `codex_status` integration is independent of AI usage gauges and polls local execution state every two seconds.

- One dot per active task, with a short task-ID suffix underneath.
- Yellow **P**: processing. Red **A/R/E/I**: approval, reply needed, error, interrupted.
- Green **C**: completed, shown when no active task remains.
- Gray **?**: unavailable or stale; **-**: no session.
- Small HUDs cycle task pages every four seconds. Tasks are ordered by ID so their positions stay stable between polls.

With multiple root sessions, live approval/input requests and system errors take priority over processing. Running work takes priority over past interruptions or failures; when idle, desktop mode shows the newest root’s outcome. Temporary/subagent sessions are excluded. Leave Session ID empty to observe all eligible root sessions, or enter one thread ID. Leave Socket Path empty for automatic mode: it observes the shared daemon and reads desktop turn metadata in read-only mode, since the desktop may execute work in a separate process. Desktop roots must be non-archived and updated within 30 minutes. An explicit Socket Path observes only that daemon. Paths resolve under `$CODEX_HOME` (default `~/.codex`); no API key is needed. Pixel OPs never starts or modifies Codex sessions. Validated on Codex 0.153.4/macOS. Desktop metadata detects execution and completion; pending approval/input flags require the live WebSocket and may appear as processing for desktop-only sessions. A question written as an ordinary final response appears as completed.

The layout kind is `codex_status`; a useful initial size is 300 × 72. The HUD is configured on the Work and Pokémon screens. Hiding it does not stop collection. After installing the code change, restart an already-running Pixel OPs process; subsequent JSON edits hot reload normally.

### Slack

```json
{
  "integrations": {
    "slack": {
      "enabled": true,
      "app_token_env": "PIXEL_OPS_SLACK_APP_TOKEN",
      "bot_token_env": "PIXEL_OPS_SLACK_BOT_TOKEN",
      "bot_user_id": "U123456",
      "socket_reconnect_seconds": 10
    }
  }
}
```

Slack uses Socket Mode. Enable Socket Mode in the Slack app, create an app-level token with `connections:write`, and install the bot with event scopes for mentions, messages, reactions, and presence-like activity.

### Discord

```json
{
  "integrations": {
    "discord": {
      "enabled": true,
      "bot_token_env": "PIXEL_OPS_DISCORD_BOT_TOKEN",
      "guild_id": "1133891225209024633",
      "focus_user_id": "242829666488942593",
      "max_companions": 30,
      "gateway_reconnect_seconds": 10
    }
  }
}
```

Discord runs a local Gateway client. It tracks voice state for one guild, emits provider-neutral voice activity events on voice channel joins/switches, and exposes a current voice snapshot for visual plugins. Recent Discord identities are stored in `discord_people.json`; Pokemon sprite choices are stored separately in `pixel_ops/plugins/pokemon/companions.json`.

## Pokemon Cache

Download/cache PokeAPI metadata plus front and animated sprites:

```bash
python pixel_ops/main.py --plugin pokemon --warm-cache
python pixel_ops/main.py --plugin pokemon --warm-cache --pokemon-limit 25
```

Run without network access:

```bash
python pixel_ops/main.py --plugin pokemon --output preview --offline
```

## Hardware

Display transport is isolated in `pixel_ops/hardware/`. The current reference device is a TURZX/Turing Smart Screen-style 3.5-inch USB display:

- Size: 3.5-inch portrait display.
- Resolution: 320x480.
- Protocol: Rev. A-compatible USB bulk transport (`1a86:5722`).
- Backend: `usb_bulk_rev_a`.

Purchase links:

- Brazil: [TURZX 3.5-inch secondary USB monitor on Mercado Livre](https://www.mercadolivre.com.br/tela-ips-monitoramento-35-polegadas-secundaria-usb-monitor-turzx-telinha-auxiliar-aida-64-mini-tela-pc/p/MLB29751860)
- United States: [TURZX 3.5-inch USB monitor search on Amazon](https://www.amazon.com/s?k=TURZX+3.5+inch+USB+monitor)

Listings change frequently. Match a 3.5-inch TURZX/Turing Smart Screen/USB monitor with 320x480 resolution before buying.

## Architecture Records

Architecture decisions live in [docs/adr](docs/adr/README.md). Add or update an ADR when changing provider/plugin boundaries, config ownership, event semantics, AI policy, hot reload behavior, or renderer product principles.

## Credits

- [CodexBar](https://github.com/steipete/CodexBar), by Peter Steinberger, inspired the provider-normalized AI usage gauges and local/API usage tracking approach used by the `ai_usage` integration.
- Pixel OPs was originally built from a local fork of [`mathoudebine/turing-smart-screen-python`](https://github.com/mathoudebine/turing-smart-screen-python). The upstream project provided the original USB display protocol research and Python driver foundation for Turing Smart Screen style devices. The current repository keeps a minimal adapted USB bulk transport and RGB565 serializer.
