# 0040 — Show off is an isolated game projection

Status: Accepted

## Context

Recordings of the display outputs need a repeatable demonstration without exposing
enterprise calendars or PRs. The recording loops through temperatures, a dummy
five-minute meeting countdown, paced PR encounters, the meeting starting, and a
temperature outro. Meeting carousels must also use sample data.

## Decision

- `display.show_off` enables a Pokémon-owned `ShowOffScenario`. A new `run_id`
  restarts the loop through the existing JSON hot reload. It defaults off.
- The Pokémon projection rejects real work events and non-allowlisted observations
  before storing or enqueuing them. Calendar and companion/task/media/people state
  cannot enter the recording. PC metrics and account quota remain live. Real PR
  listings must carry a full repository identity owned by the configured demo
  owner. Without an owner, the demo uses synthetic listings exclusively.
  Real PR events do not interrupt the staged take.
- The scenario supplies sample calendar projections and synthetic `WorkEvent`s
  inside the game. It does not impersonate a GitHub transport, call a write API,
  publish back into providers, or change real calendar/repository coverage.
- The first five seconds show Kraken temperatures. The meeting then starts a real
  five-minute countdown. Five seconds later the first staged PR arrives on a
  sample repository. Subsequent PRs rotate through the demo repositories and any
  verified owned repositories in the PR observation.
- New PRs are queued only when the prior encounter has completed its entire
  capture/resume sequence, followed by eight seconds of countdown/walking. Only
  one encounter can be pending. The scheduler respects configured phase durations
  and message-reading minimums, and reserves time before the meeting start rather
  than creating a late battle backlog. Bounded synthetic inventory and unique
  per-cycle event IDs allow repeated showcases without provider writes.
- The normal encounter machinery renders both screens; Kraken shares the primary
  phase clock and Pokémon. Slow or extended captures are never cut off by a timer.
- The meeting shows Starting now for five seconds, then a ten-second temperature
  outro begins once the world is idle. A fresh loop includes the five-second
  intro, producing fifteen uninterrupted temperature seconds between countdowns.
  Late ticks do not replay missed PR opportunities. Real meeting reminders keep
  their existing five-minutes-before to one-minute-after behavior.
- The demo scene has no capture store, AI provider, gamification source, or lazy
  Pokemon downloads. Captures are memory-only. No recorded demo encounter changes
  normal capture history. Screen rotation is paused to keep the recording on the
  isolated Pokémon presentation.
- Integration collection remains active and independent of display mode. Disabling
  Show off rebuilds the ordinary projection from current provider observations,
  restoring normal coverage and persistence without replaying demo facts.

## Consequences

The recording mode is explicit and persistent until disabled. Enable or replay it
with Config Studio and save JSON; start recording before saving to capture the
temperature intro. The loop is about five minutes twenty seconds at default
timings and repeats until disabled. Restart resets the take to its temperature
intro. The synthetic PR numbers/titles are examples, and every cycle remains
isolated from production event and capture history.
This is a game presentation fixture, not a replacement provider snapshot channel
or a real GitHub/calendar mutation.
