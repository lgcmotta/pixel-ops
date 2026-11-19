# 0038 - Google Calendar uses read-only user OAuth

Status: Accepted

## Context

The existing Google integration consumed ICS URLs despite exposing unused
credential/token-path settings. The personal account already has multiple
work calendars shared with it and needs explicit calendar selection, including
shared/subscribed calendars rather than just its primary calendar.

## Decision

Add an optional OAuth mode alongside legacy ICS. Use Google-auth and
google-auth-oauthlib for Desktop app authorization-code/PKCE with a temporary
loopback-only callback and state validation. Users supply their own Google Cloud
Desktop client through a local import control and complete browser consent.
Only calendar-list and event read scopes are requested. Gmail can connect to an
External OAuth app owned by a Workspace Cloud project.

Config Studio lists paginated calendars and saves selected IDs and legacy Google
ICS URLs in Git-ignored local integration config. Client and refresh credentials
remain under the ignored cache directory. HTTP account-management routes reuse
the local same-origin guard and bounded Python account bridge. Responses/logs omit arbitrary OAuth
payloads, secrets and tokens. Cancellation wakes the local listener; profile
file locking serializes authentication and runtime refresh across processes.

The provider fetches paginated regular events with recurrence expansion and a
bounded date range, normalizes time zones/all-day dates, excludes cancelled and
self-declined entries, and deduplicates identical iCalUID/start pairs. It writes
one complete normalized local ICS cache atomically. A partial scan cannot replace
the previous complete cache. Token refresh and HTTP reads have bounded timeouts;
overlapping source refreshes are serialized.

Reuse existing CalendarEventSource and calendar-path observation adapters for
meeting facts, next meeting, and today's schedule. This adds no provider snapshot
fields to the core runtime and no Google dependencies to game renderers. Closing
Studio cannot stop calendar polling. The personal capture-category allowlist
continues to permit new PR facts only.

## Consequences

Cloud client setup, consent and calendar sharing are prerequisites to live use;
the integration remains disabled until calendar selection. Workspace ownership
does not override external calendar permissions. Google External Testing refresh
tokens expire in seven days for these scopes, requiring an appropriate publishing
configuration for unattended use. Outlook calendars exposed through Google follow
Google's subscription update behavior. Full calendar migration/live validation
requires the owner's client and sign-in.
