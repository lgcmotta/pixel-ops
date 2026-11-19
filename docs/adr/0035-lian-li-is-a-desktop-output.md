# 0035 - Lian Li is a desktop output

Status: Accepted

## Context

The Lian Li US88v1 supports a 1920x480 Windows secondary-display mode. The Kraken
Elite already displays temperatures through CAM. This setup needs one PixelOps
output rather than a new USB transport or ownership of cooler controls.

## Decision

Extend desktop output with optional borderless placement and monitor selection.
A unique native-resolution match is selected automatically; missing/ambiguous
matches fail with a setup message. An explicit index must match the resolution.
Enable Windows DPI awareness before SDL initializes. Window-preview mode uses a
normal reduced window. Monitor, dimensions and output choices require restart.

The saved Lian Li Pokemon presentation combines a central world with a status
strip, hardware gauges, account quota and PR activity. Optional presentation-only
camera zoom transforms the finished overworld. A dead zone and bounded camera
motion let the actor move visibly before the view follows. Zoomed overworld
sprites use their native map scale; battle presentation remains separate.
Pixel art uses nearest-neighbor scaling.
The initial target is 10 FPS.

Pokemon owns collision-aware wandering: a feet footprint follows cardinal paths
through the union of configured walkable regions, excluding blockers. Only the
current connected component supplies destinations. Short idle pauses stop the
walk animation; encounters freeze the current pose rather than snapping back to
an old route point. Each frame advances at most once, even when dirty-region
rendering asks for sprite bounds repeatedly. Collection and event semantics are
unaffected.

CPU/RAM and NVIDIA utilization/VRAM collection stay in `pc_stats` and enter via
`system.metrics_updated`. Optional numeric values/units/totals extend `PCMetric`
without replacing text fields. One bounded read-only NVIDIA query provides each
sample. Missing/stale readings remain unavailable. Renderers never call platform
APIs. Layout visibility cannot disable telemetry or work events.

GitHub coverage is an explicit list plus optional owned-repository discovery,
refreshed every 15 minutes. PR pagination is independent of the HUD display limit.
Full repository identity prevents collisions across owners. Draft and non-draft
PRs remain ambient activity without a personal-review filter. The wide HUD calls
this PR activity.

Open PRs publish before the closed-history scan completes. Transient repository
failures preserve the last known open PRs. The HUD rotates through the most
recently updated entries, with open PRs first.
Discrete facts describe new arrivals after a silent inventory baseline, with
durable identities preventing restart replays (ADR 0037).
The Lian Li layout reserves its right strip for larger quota and PR typography,
with separate repository and PR/status lines. Capture history remains available
as an optional presentation region; hiding it does not stop PR collection,
encounters, or capture persistence.
Saving a manual GitHub token in Studio takes precedence over an older inherited
token when Studio reads GitHub or starts its runtime subprocess.
GitHub's last-known PR snapshot persists under the ignored cache directory and
is scoped to the credential and selected coverage. It restores display state
and arrival-deduplication state after restarts. A one-second observation
reader publishes available state while one shared, budgeted network scheduler
refreshes both open PRs and merge/closure events.

The configured PR polling interval is a minimum. Large repository sets increase
the effective interval to reserve REST API budget; server rate-limit responses
pause requests until retry/reset rather than repeatedly polling denied calls.

## Consequences

L-Connect must expose the secondary display before configured output can start.
CAM retains temperatures and cooling control. PC stats, GitHub, account quota,
calendars and weather can be configured independently.
