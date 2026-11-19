"""Read-only Google Calendar OAuth and a normalized local calendar cache."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, time, timedelta, timezone
import json
from pathlib import Path
import threading
import urllib.parse
import urllib.request

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).resolve().parents[2]
HOME = ROOT / "pixel_ops/cache/google_calendar"
SCOPES = ["https://www.googleapis.com/auth/calendar.calendarlist.readonly", "https://www.googleapis.com/auth/calendar.events.readonly"]
API = "https://www.googleapis.com/calendar/v3/"


@contextmanager
def credential_lock(home):
    # SQLite's file lock works across Studio and runtime processes on Windows.
    import sqlite3
    home.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(home / "profile.lock.sqlite", timeout=10)
    try:
        connection.execute("BEGIN EXCLUSIVE")
        yield
    finally:
        connection.close()


def write_private(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def credentials(home):
    class BoundedRequest(Request):
        def __call__(self, *args, **kwargs):
            kwargs["timeout"] = 10
            return super().__call__(*args, **kwargs)
    value = Credentials.from_authorized_user_file(home / "token.json", SCOPES)
    if not value.valid:
        value.refresh(BoundedRequest())
        write_private(home / "token.json", value.to_json())
    return value


def api_pages(credential, resource, params=None):
    params = dict(params or {}, maxResults=250)
    for _ in range(1000):
        response = requests.get(API + resource, params=params, headers={"Authorization": f"Bearer {credential.token}"}, timeout=10)
        response.raise_for_status()
        data = response.json()
        yield from data.get("items", [])
        token = data.get("nextPageToken")
        if not token:
            return
        params["pageToken"] = token
    raise ValueError("Calendar pagination exceeded safety bound")


def list_calendars(home):
    with credential_lock(home):
        credential = credentials(home)
        return [{"id": row["id"], "label": row.get("summaryOverride") or row.get("summary") or row["id"],
                 "access_role": row.get("accessRole", "none"), "primary": bool(row.get("primary")),
                 "timezone": row.get("timeZone", "UTC")}
                for row in api_pages(credential, "users/me/calendarList", {"showHidden": "true", "fields": "nextPageToken,items(id,summary,summaryOverride,accessRole,primary,timeZone,deleted)"})
                if not row.get("deleted")]


def _escape(value):
    return str(value).replace("\\", "\\\\").replace("\r", "").replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")


def events_to_ics(rows):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//PixelOps//Google Calendar//EN"]
    seen = set()
    for row in rows:
        if row.get("status") == "cancelled" or any(a.get("self") and a.get("responseStatus") == "declined" for a in row.get("attendees", [])):
            continue
        start, end = row.get("start", {}), row.get("end", {})
        beginning = start.get("dateTime") or start.get("date")
        identity = (row.get("iCalUID") or row.get("id"), beginning)
        if not beginning or identity in seen:
            continue
        seen.add(identity)
        try:
            def stamp(value):
                if value.get("date"):
                    return ";VALUE=DATE:" + value["date"].replace("-", "")
                parsed = datetime.fromisoformat(value["dateTime"].replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    from zoneinfo import ZoneInfo
                    parsed = parsed.replace(tzinfo=ZoneInfo(value.get("timeZone", "UTC")))
                return ":" + parsed.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            title = " ".join(str(row.get("summary") or "Busy").split())
            event_lines = ["BEGIN:VEVENT", "UID:" + _escape(identity[0]), "DTSTART" + stamp(start), "DTEND" + stamp(end),
                           "SUMMARY:" + _escape(title), "X-PIXEL-OPS-CALENDAR:" + _escape(row.get("_calendar_name", "Google Calendar")), "END:VEVENT"]
            lines.extend(event_lines)
        except (KeyError, ValueError, TypeError):
            continue
    return "\r\n".join([*lines, "END:VCALENDAR", ""])


class GoogleCalendarCache:
    def __init__(self, home=HOME, calendar_ids=(), poll_seconds=120):
        self.home = Path(home)
        self.ids = list(calendar_ids)
        self.poll_seconds = max(30, int(poll_seconds))
        self.path = self.home / "events.ics"
        self.checked_at = None
        self._refresh_lock = threading.Lock()

    def warm(self):
        self.refresh(datetime.now().astimezone())

    def refresh(self, now):
        if not self._refresh_lock.acquire(blocking=False):
            return
        rows = []
        try:
            with credential_lock(self.home):
                credential = credentials(self.home)
                labels = {row["id"]: row.get("summaryOverride") or row.get("summary") or "Google Calendar"
                          for row in api_pages(credential, "users/me/calendarList", {"fields": "nextPageToken,items(id,summary,summaryOverride)"})}
                start = datetime.combine((now - timedelta(days=1)).date(), time.min, tzinfo=now.tzinfo)
                params = {"timeMin": start.isoformat(), "timeMax": (start + timedelta(days=8)).isoformat(),
                          "singleEvents": "true", "orderBy": "startTime", "showDeleted": "false", "eventTypes": "default",
                          "fields": "nextPageToken,items(id,iCalUID,status,summary,start,end,attendees(self,responseStatus))"}
                for calendar_id in self.ids:
                    resource = "calendars/" + urllib.parse.quote(calendar_id, safe="") + "/events"
                    rows.extend({**row, "_calendar_name": labels.get(calendar_id, "Google Calendar")}
                                for row in api_pages(credential, resource, params))
                write_private(self.path, events_to_ics(rows))
            self.checked_at = now
        except Exception:
            # A partial/failing scan cannot replace a complete previous calendar.
            return
        finally:
            self._refresh_lock.release()

    def poll(self, now):
        if self.checked_at is None or (now - self.checked_at).total_seconds() >= self.poll_seconds:
            self.refresh(now)
            # Back off failures too; never poll a broken connection every frame.
            self.checked_at = now
        return []


class CalendarController:
    def __init__(self, home=HOME):
        self.home = Path(home)
        self.status = "idle"
        self.url = None
        self.callback = None
        self.state = None
        self.cancelled = threading.Event()
        self.ready = threading.Event()
        self.thread = None

    def close(self):
        self.cancelled.set()
        if self.callback and self.thread and self.thread.is_alive():
            try:
                uri = self.callback + "?" + urllib.parse.urlencode({"error": "access_denied", "state": self.state})
                urllib.request.urlopen(uri, timeout=2).close()
            except OSError:
                pass
            self.thread.join(timeout=12)

    def login(self):
        self.close()
        if self.thread and self.thread.is_alive():
            raise RuntimeError("Previous sign-in is still stopping")
        self.cancelled.clear()
        self.ready.clear()
        self.url = self.callback = None
        self.status = "pending"
        controller = self

        class LocalFlow(InstalledAppFlow):
            def authorization_url(self, **kwargs):
                result = super().authorization_url(**kwargs)
                controller.url, controller.state = result
                controller.callback = self.redirect_uri
                controller.ready.set()
                return result

            def fetch_token(self, **kwargs):
                return super().fetch_token(timeout=10, **kwargs)

        def worker():
            try:
                with credential_lock(self.home):
                    flow = LocalFlow.from_client_secrets_file(self.home / "client.json", SCOPES, autogenerate_code_verifier=True)
                    credential = flow.run_local_server(host="127.0.0.1", bind_addr="127.0.0.1", port=0, open_browser=False,
                                                       authorization_prompt_message=None, timeout_seconds=300,
                                                       success_message="Google sign-in received. Return to PixelOps Config Studio.",
                                                       prompt="consent select_account")
                    if not self.cancelled.is_set():
                        write_private(self.home / "token.json", credential.to_json())
                        self.status = "connected"
            except Exception:
                self.status = "cancelled" if self.cancelled.is_set() else "failed"
            finally:
                self.ready.set()
        self.thread = threading.Thread(target=worker, daemon=True)
        self.thread.start()
        self.ready.wait(5)
        return {"status": self.status, "auth_url": self.url}

    def handle(self, method, params):
        if method == "client/import":
            value = params.get("client") or {}
            installed = value.get("installed", {})
            if (not str(installed.get("client_id", "")).endswith(".apps.googleusercontent.com")
                    or not installed.get("client_secret")
                    or installed.get("auth_uri") not in ("https://accounts.google.com/o/oauth2/auth", "https://accounts.google.com/o/oauth2/v2/auth")
                    or installed.get("token_uri") != "https://oauth2.googleapis.com/token"):
                raise ValueError("Use the Google-downloaded Desktop app OAuth JSON")
            self.close()
            with credential_lock(self.home):
                write_private(self.home / "client.json", json.dumps({"installed": installed}))
                (self.home / "token.json").unlink(missing_ok=True)
                (self.home / "events.ics").unlink(missing_ok=True)
            return {"status": "configured", "client_configured": True}
        if method == "login/start":
            return self.login()
        if method == "login/status":
            return {"status": self.status, "auth_url": self.url if self.status == "pending" else None}
        if method == "login/cancel":
            self.close()
            self.status = "cancelled"
            return {"status": self.status}
        if method == "disconnect":
            self.close()
            with credential_lock(self.home):
                (self.home / "token.json").unlink(missing_ok=True)
                (self.home / "events.ics").unlink(missing_ok=True)
            return {"status": "disconnected"}
        if method == "calendars":
            return {"status": "connected", "calendars": list_calendars(self.home)}
        if method == "status":
            return {"status": "connected" if (self.home / "token.json").exists() else "disconnected",
                    "client_configured": (self.home / "client.json").exists()}
        raise ValueError("Unknown calendar action")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", default=str(HOME))
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    controller = CalendarController(Path(args.home))
    import sys
    try:
        for line in sys.stdin:
            request = {}
            try:
                request = json.loads(line)
                result = controller.handle(request["method"], request.get("params") or {})
                response = {"id": request.get("id"), "result": result}
            except Exception:
                response = {"id": request.get("id"), "error": "Google Calendar connection unavailable. Check the Desktop app client, sign-in, Calendar API and calendar permissions."}
            print(json.dumps(response), flush=True)
    finally:
        controller.close()


if __name__ == "__main__":
    main()
