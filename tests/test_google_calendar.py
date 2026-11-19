from datetime import datetime, timezone, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from urllib.parse import parse_qs, urlparse

import pytest

from pixel_ops.data_sources.calendar import ics_events_between
from pixel_ops.data_sources.google_calendar import CalendarController, GoogleCalendarCache, api_pages, events_to_ics, SCOPES


CLIENT = {'installed': {'client_id': 'local-test.apps.googleusercontent.com', 'client_secret': 'not-a-real-secret',
                        'auth_uri': 'https://accounts.google.com/o/oauth2/auth', 'token_uri': 'https://oauth2.googleapis.com/token',
                        'redirect_uris': ['http://localhost']}}
NOW = datetime(2026, 10, 29, tzinfo=timezone.utc)


def event(**kwargs):
    return dict(id='one', iCalUID='shared-invite', summary='Planning', start={'dateTime': '2026-10-29T10:00:00-03:00'},
                end={'dateTime': '2026-10-29T10:30:00-03:00'}, **kwargs)


def test_normalization_deduplicates_shared_copies_expands_received_instances_and_keeps_busy():
    rows = [event(), event(), event(status='cancelled'), event(attendees=[{'self': True, 'responseStatus': 'declined'}]),
            {'id': 'all-day', 'start': {'date': '2026-10-29'}, 'end': {'date': '2026-10-30'}}]
    with TemporaryDirectory() as directory:
        path = Path(directory) / 'events.ics'
        path.write_text(events_to_ics(rows))
        result = ics_events_between(path, NOW, NOW + timedelta(days=1))
    assert len(result) == 2
    assert result[0].title == 'Busy' and result[0].all_day
    assert result[1].starts_at.hour == 13


def test_pagination_follows_tokens_even_when_first_page_is_short():
    responses = [MagicMock(), MagicMock()]
    responses[0].json.return_value = {'items': [{'id': 1}], 'nextPageToken': 'next'}
    responses[1].json.return_value = {'items': [{'id': 2}]}
    with patch('pixel_ops.data_sources.google_calendar.requests.get', side_effect=responses) as get:
        assert [row['id'] for row in api_pages(SimpleNamespace(token='fake'), 'users/me/calendarList')] == [1, 2]
        assert get.call_args.kwargs['params']['pageToken'] == 'next'


def test_failed_partial_calendar_scan_preserves_the_complete_cache():
    with TemporaryDirectory() as directory:
        source = GoogleCalendarCache(Path(directory), ['first', 'second'])
        source.path.write_text('previous complete cache')
        with patch('pixel_ops.data_sources.google_calendar.credentials', return_value=object()), patch('pixel_ops.data_sources.google_calendar.api_pages', side_effect=[[{'id': 'first', 'summary': 'Kite'}], [event()], OSError('offline')]):
            source.refresh(NOW)
        assert source.path.read_text() == 'previous complete cache'


def test_complete_scan_supplies_existing_neutral_calendar_events():
    from pixel_ops.events.calendar_events import CalendarEventSource
    from pixel_ops.main import next_event
    with TemporaryDirectory() as directory:
        source = GoogleCalendarCache(Path(directory), ['first', 'second'])
        with patch('pixel_ops.data_sources.google_calendar.credentials', return_value=object()), patch('pixel_ops.data_sources.google_calendar.api_pages', side_effect=[[{'id': 'first', 'summary': 'Kite', 'summaryOverride': 'Kite Work'}, {'id': 'second', 'summary': 'Personal'}], [event()], [event()]]):
            source.refresh(NOW)
        now = NOW + timedelta(hours=12, minutes=45)
        meeting = next_event(now, [source.path], True)
        assert meeting.title == 'Planning'
        assert meeting.calendar_name == 'Kite Work'
        assert meeting.uid == 'shared-invite'
        facts = CalendarEventSource(enabled=True, path=source.path).poll(now)
        assert len(facts) == 1


def test_client_import_is_sanitized_and_rejects_non_google_endpoints():
    with TemporaryDirectory() as directory:
        controller = CalendarController(Path(directory))
        result = controller.handle('client/import', {'client': CLIENT})
        assert result == {'status': 'configured', 'client_configured': True}
        assert 'not-a-real-secret' not in str(result)
        bad = {'installed': {**CLIENT['installed'], 'token_uri': 'https://example.com/token'}}
        with pytest.raises(ValueError):
            controller.handle('client/import', {'client': bad})
        assert not any('write' in scope for scope in SCOPES)


def test_real_loopback_signin_uses_pkce_and_cancel_releases_the_profile_without_tokens():
    with TemporaryDirectory() as directory:
        home = Path(directory)
        controller = CalendarController(home)
        controller.handle('client/import', {'client': CLIENT})
        try:
            result = controller.handle('login/start', {})
            assert result['status'] == 'pending'
            query = parse_qs(urlparse(result['auth_url']).query)
            assert query['code_challenge_method'] == ['S256']
            assert query['redirect_uri'][0].startswith('http://127.0.0.1:')
            assert 'client_secret' not in query
            assert controller.handle('login/cancel', {})['status'] == 'cancelled'
            assert not controller.thread.is_alive()
            assert not (home / 'token.json').exists()
        finally:
            controller.close()


def test_successful_login_persists_credentials_without_returning_them_to_studio():
    from google_auth_oauthlib.flow import InstalledAppFlow
    with TemporaryDirectory() as directory:
        home = Path(directory)
        controller = CalendarController(home)
        controller.handle('client/import', {'client': CLIENT})
        fake = MagicMock()
        fake.to_json.return_value = '{"token":"private-access-token","refresh_token":"private-refresh-token"}'
        def finish(flow, **kwargs):
            flow.redirect_uri = 'http://127.0.0.1:12345/'
            flow.authorization_url()
            return fake
        with patch.object(InstalledAppFlow, 'run_local_server', finish):
            result = controller.handle('login/start', {})
            controller.thread.join(timeout=2)
        assert controller.status == 'connected'
        assert 'private-access-token' not in str(result)
        assert 'private-refresh-token' in (home / 'token.json').read_text()
        assert CalendarController(home).handle('status', {})['status'] == 'connected'
        controller.handle('disconnect', {})
        assert not (home / 'token.json').exists()
