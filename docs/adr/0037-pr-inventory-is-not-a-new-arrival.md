# 0037 - PR inventory is not a new arrival

Status: Accepted

## Context

The GitHub HUD shows current PR inventory, including older open PRs. Treating
every discovered item as a new work event replays old encounters after runtime
restarts or integration rebuilds. Bursts of inventory events also drive the
world into its busy mood, whose rapidly blinking sparks resemble a cursor when
enlarged on the panoramic display.

## Decision

GitHub keeps observations separate from arrival facts. The first successful,
fully paginated open-PR fetch for each repository establishes a silent baseline.
Failed requests cannot establish that baseline. Inventory still reaches
`github.pull_requests_updated` and may page through older open PRs.

An unseen PR produces one `PULL_REQUEST` work event only when its GitHub
`created_at` is at or after that repository's baseline and within the configured
`startup_lookback_seconds` (one hour in this setup). Future/missing creation times
do not manufacture arrival events. Both draft and non-draft creations are PR
facts; broad polling does not imply that the account was requested as a reviewer.
Open inventory labels therefore say open/draft, rather than claiming review.

Persist repository baselines, known PR identities and emitted event identities
alongside the existing ignored snapshot cache, scoped to its credential and
coverage profile. Old snapshot formats migrate by silently baselining their
inventory. Polls, restarts, edits, draft promotions and reopening an old PR cannot
replay a creation. Long-offline history remains inventory rather than a capture
backlog. Changing account or coverage establishes a fresh quiet baseline.

Pokemon adds an optional `events.capture_categories` allowlist. Its default
retains legacy behavior. This personal setup allows only `pull_request`.
Other work events still reach the engine, recent-event projection and mood;
closures/merges are not removed from the provider stream merely to prevent a
capture. No collection decision depends on which HUD regions are visible.

`game.ambient_particles` is an optional presentation setting, enabled by
default and disabled in the Lian Li profile. It disables the cursor-like sparks
and other particles while retaining mood tint, walking and encounter animation.

## Consequences

An existing PR list is useful context, not evidence of a newly opened PR. A new
arrival discovered after baseline may trigger capture once. Short outages can
catch up recent unseen creations; downtime does not replay days of backlog.
Provider/game boundaries and the neutral event pump remain unchanged.
