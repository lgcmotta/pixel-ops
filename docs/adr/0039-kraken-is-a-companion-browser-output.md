# 0039 — Kraken is a companion browser output

Status: Accepted

## Context

The Lian Li Windows display remains the primary Pokémon world. NZXT CAM can
render a local web page on Kraken and inject monitoring data once per second.
The requested circular view shows temperatures, the same new-PR encounter as
the primary world, and a meeting countdown from five minutes before its start
until one minute afterwards. A PR battle interrupts the countdown; its absolute
deadline continues to run.

## Decision

- The optional `BrowserViewProvider` extension publishes immutable serialized
  presentations through `PixelOpsApp.browser_views()`. Legacy engines remain
  valid. The core forwards the active game's presentations without interpreting
  provider or Pokémon state.
- The Pokémon plugin owns countdown selection and battle projection. It reads
  existing neutral calendar observations and the primary encounter state, never
  starts a second game loop or records a second capture. Its separate battle
  layout shares the primary state clock and sprites without advancing them.
- The loopback-only `BrowserOutputServer` serves fixed local assets and published
  JSON/PNG snapshots. HTTP workers cannot call game engines or integration APIs.
  Foreign Host/Origin/cross-site requests are rejected and no credentials enter
  its payloads. No public hosting or additional authentication flow is needed.
- CAM supplies CPU/GPU/coolant temperatures directly to the page through its
  documented callback. NVIDIA is selected ahead of an integrated GPU. When CAM
  lacks that temperature, the existing asynchronous PC collector includes it in
  its single bounded NVIDIA query, exposing a numeric `gpu_temperature` metric
  through `system.metrics_updated`. The plugin publishes this fresh fallback;
  missing or stale readings show unavailable values. CAM's last-update count
  and GPU names/readings are stored locally for the shared configuration window's
  diagnostics, never transmitted to an external service.
  Metadata such as dimensions, shape and target FPS is preserved. The browser
  limits rendering to at most 30 FPS and polls battle frames at most 10 FPS.
- Battle takes priority over meeting, then thermal. Only the actual active
  `pull_request` encounter is mirrored: PR inventory, other event categories,
  and the previous encounter during walking cannot trigger a takeover. Existing
  arrival deduplication remains authoritative.
- Encounter headings show the full repository identity, PR number and Pokémon
  name in both live and demo modes. The PR number is separate from the Pokédex
  number. Providers supply optional `number` metadata; existing event IDs/titles
  remain readable for compatibility, and missing PR numbers are never inferred
  from a Pokémon's identity. The widescreen battle keeps this reference in its
  dynamic background throughout capture phases and dirty-region updates; Kraken
  lays it out separately to fit its circular screen without duplicating captions.
- A meeting window is derived from its start instant, not timers that can restart
  after polling, reconnection or config reload. All-day events are excluded;
  overlapping windows choose the earliest meeting deterministically. Absolute
  expiry and stale-presentation fallback are also checked by the page.
- Calendar observations retain optional `calendar_name` and `uid` fields. Google
  enriches its normalized ICS cache with readable calendar labels and shared
  invitations remain deduplicated. The renderer never contacts Google.
- `display.kraken_web` owns enable, port, PR battle and meeting settings. Enable
  and port changes require a runtime restart; presentation switches hot reload.
  The runtime owns the server, so closing Config Studio has no effect.

## Consequences

CAM and PixelOps must run in the logged-in desktop session. The existing desktop
scheduled task starts PixelOps and its browser output; no extra task is needed.
If the runtime stops, CAM readings can continue in the already-loaded page, with
takeovers falling back to thermal after five seconds. A page that initially loads
before the local server is available may need CAM's refresh control.

The bounded, requested meeting/encounter takeovers are companion presentations,
not a new notification feed. No raw PR bodies, chat content or secrets are shown.

References: [NZXT development interface](https://developer.nzxt.com/docs/development/),
[monitoring types](https://github.com/NZXTCorp/web-integrations-types/blob/main/v1/index.d.ts).
