# Google Calendar account setup

PixelOps can use your personal Gmail to read calendars shared with or subscribed
to by that account. A Google Workspace organization can own the Google Cloud
project. Access to another organization's private calendar requires that
organization's sharing permissions.

Selection uses calendar IDs rather than guessing from names. Only one Google
account is connected at a time. No separate Outlook login is necessary for
calendars Google already exposes, but Google subscriptions retain Google's sync
cadence and access limitations. Busy-only calendar access cannot provide event
titles and is disabled in the picker.

## Create the client

1. Sign into [Google Cloud Console](https://console.cloud.google.com/) with your
   Workspace account. Create/select a project such as `PixelOps`. You need Cloud
   project permissions; Workspace super-admin status alone may not supply those.
2. [Enable Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com).
3. In **Google Auth Platform**, configure app branding/support email. Set
   **Audience → External** so your personal Gmail can sign in. Internal restricts
   the app to Workspace organization accounts.
4. Initially use Testing and add your personal Gmail under test users. Request
   only `calendar.calendarlist.readonly` and `calendar.events.readonly` under
   Data Access. PixelOps does not need calendar write access or domain delegation.
5. Create an OAuth client with application type **Desktop app**, named e.g.
   `PixelOps Windows`. Download its JSON file. Do not create an API key or service
   account for this flow; do not paste the downloaded JSON into chat or Git.

**Unattended use:** Google External apps in Testing issue refresh tokens that
expire after seven days for these scopes. Use Google's appropriate production
publishing/verification configuration before expecting a permanent connection.
Publishing, consent restrictions and verification requirements are managed by
Google; PixelOps does not bypass an administrator or unverified-app block.

## Connect locally

1. Open Config Studio → Google Calendar. Connection mode is `oauth`.
2. Import the downloaded Desktop app JSON using the local file input.
3. Choose **Sign in with Google**, then **Open Google sign-in page**. Choose your
   **personal Gmail**, grant read access, and return to Studio. The callback is a
   temporary loopback listener; no public web server or manually copied code is
   needed. Sign-in expires after five minutes and can be cancelled.
4. Choose **Load shared calendars** if the list has not loaded automatically.
5. Select the calendars you want to display and **Save configuration**. Selecting calendars
   enables this integration; saving applies it to the running display.

The next-meeting HUD combines selected calendars. Recurrences are expanded by
Google, cancelled/declined invitations are excluded, and identical invitation
UID/start pairs shared across calendars are deduplicated. Time zones and all-day
dates are preserved. Regular calendar events are fetched; working-location,
birthday and focus-time event types do not become meeting reminders.

The personal Pokemon setup still reserves capture animation for new PR arrivals.
Calendar observations supply the HUD and mood without changing that setting.

## Storage and lifecycle

Client JSON and Google-managed refresh credentials are stored under the ignored
`pixel_ops/cache/google_calendar/` directory. Selected calendar IDs and legacy
Google ICS feed URLs are saved in the ignored
`pixel_ops/config/integrations.local.json` by a local Config Studio session.
Shared runtime settings hold the connection mode, enablement and polling
preferences. Frontend responses omit access tokens, refresh tokens and client
secrets.

The runtime polls every two minutes after configuration. It does not depend on
Studio remaining open. A failed partial scan keeps the last complete local
calendar cache. Disconnect removes local credentials and calendar data; the
client definition remains available for reconnecting. Google's account permission
page can revoke the cloud grant separately.

Legacy ICS mode remains available. ICS feeds may be public or private secret
links; OAuth removes the need to collect those links for this setup.

References: [Google Desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app),
[Calendar-list API](https://developers.google.com/workspace/calendar/api/v3/reference/calendarList/list),
[Calendar scopes](https://developers.google.com/workspace/calendar/api/auth),
[refresh-token lifetime](https://developers.google.com/identity/protocols/oauth2/).
