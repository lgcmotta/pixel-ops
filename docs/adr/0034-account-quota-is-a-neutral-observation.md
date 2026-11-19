# 0034 - Account quota is a neutral observation

Status: Accepted

## Context

Local token logs cannot establish current account-wide allowance. The Windows
display must reflect the connected account even when work happens on another
computer. Live chat lifecycle, model and effort monitoring are outside this setup.

## Decision

The optional `codex_account` integration publishes immutable `AIQuotaSnapshot`
values through `ai.quota_updated`. Each window retains its metered bucket,
actual duration, used percentage and reset timestamp. Account token summaries
remain separate from local session totals. The core event pump has no new
provider fields; engines own their projections and can ignore the observation.

The collector uses the installed Codex app-server's account-only JSON-RPC methods
over stdio. It never starts/resumes threads, reads conversation items or consumes
earned resets. Runtime account queries have a shared 15-second deadline and run
through the asynchronous integration boundary. Default polling is 60 seconds.
Optional account token summaries may be absent on older servers.

Config Studio runs a Python bridge during browser/device-code sign-in. Runtime
polling does not depend on Studio or an active coding chat. Both use an OS-backed
lock for the same isolated authentication profile. The default profile is
`pixel_ops/cache/codex_account`, which Git ignores. Codex owns credential
persistence and refresh using its file credential store. Disconnect affects this
profile only. An OpenAI API key cannot substitute for subscription authentication.

Account HTTP endpoints accept loopback clients with a loopback Host and reject
foreign Origin/cross-site requests. Frontend responses and logs omit credentials
and arbitrary app-server errors. Sign-in links/codes are exposed only to the
local connection UI. Users complete authentication themselves.

Freshness uses the last successful quota fetch, not the last attempt. Failed
requests may retain last-good data for 180 seconds, then mark it stale. An elapsed
reset shows refreshing until the service confirms the allowance. Missing quota
never implies 100% remaining. No token allowance is inferred from local usage.

The Pokémon **AI Usage** panel groups snapshots by their neutral `provider`
identity. Updates replace only that provider's snapshot. The compact 448×208
presentation fits two provider/window blocks, with overflow paginated, keeping
each block's quota, reported account token totals, freshness and reset handling
independent. Display labels are provider-neutral; `account_quota` remains the
compatible layout kind. The existing Codex connection is unchanged. Show off
mode continues to consume live `ai.quota_updated` observations rather than
substituting sample usage or account totals.

## Consequences

Authentication survives Studio/runtime restarts independently of the coding
client's login. Protocol incompatibilities show unavailable. Hiding the quota
region does not stop collection.

Windows scheduled tasks may lack the Codex desktop application's injected PATH.
The default `codex` executable setting also discovers the installed native CLI in
the current user's versioned OpenAI/Codex bin directory. Explicit executable
overrides remain authoritative; no version hash is saved in shared config.
Studio refreshes visible quota status every minute rather than aging a single
mount-time response indefinitely. Stale/failure handling still preserves the real
last-success timestamp and never infers a new allowance.

Reference: https://learn.chatgpt.com/docs/app-server#authentication
