from __future__ import annotations

import http.client
import socket
import time
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from pixel_ops.events.base import EventCategory
from pixel_ops.events.github_events import GitHubEventSource, PullRequestSummary


class GitHubEventSourceTests(unittest.TestCase):
    def test_last_known_cache_survives_restart_but_not_an_account_or_coverage_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'github.json'
            source = GitHubEventSource(token='fake-secret-credential', repos=['org/repo'], cache_path=path)
            pr = PullRequestSummary('repo', 7, 'Private PR', 'dev', repository='org/repo', updated_at=datetime.now(timezone.utc))
            source._open_pull_requests = [pr]
            source._save_cache()
            restored = GitHubEventSource(token='fake-secret-credential', repos=['org/repo'], cache_path=path)
            self.assertEqual(restored.open_pull_requests(), [pr])
            self.assertNotIn('fake-secret-credential', path.read_text())
            for kwargs in ({'token': 'different', 'repos': ['org/repo']}, {'token': 'fake-secret-credential', 'repos': ['other/repo']}):
                self.assertEqual(GitHubEventSource(**kwargs, cache_path=path).open_pull_requests(), [])

    def test_observation_refresh_does_not_starve_merge_event_collection(self):
        source = GitHubEventSource(enabled=True, token='test', repos=['org/repo'])
        with patch.object(source, '_start_refresh_worker') as start:
            source.open_pull_requests(datetime.now(timezone.utc))
            self.assertTrue(start.call_args.kwargs['include_closed'])

    def test_open_prs_publish_before_closed_history_finishes(self):
        source = GitHubEventSource(enabled=True, token="test", repos=["org/repo"])
        source._repository_baselines['org/repo'] = datetime(2026, 1, 1, tzinfo=timezone.utc)
        pr = PullRequestSummary("repo", 42, "Title", "dev", repository="org/repo", created_at=datetime.now(timezone.utc))
        source._fetch_open_pull_requests = lambda: [pr]
        def closed(now, since):
            self.assertEqual(source.open_pull_requests(), [pr])
            self.assertEqual(source.poll(now)[0].external_id, "org/repo#42")
            return [], []
        source._fetch_closed_pull_request_updates = closed
        source._fetch_deployment_events = lambda *args: []
        now = datetime.now(timezone.utc)
        source._last_poll_at = now
        source._last_open_fetch_at = now
        source._refresh_sync(now, now, True)

    def test_failed_repository_refresh_preserves_prs_and_newest_activity_sorts_first(self):
        source = GitHubEventSource(enabled=True, token="test", repos=["org/unavailable", "org/working"])
        old = PullRequestSummary("unavailable", 1, "Old", "dev", repository="org/unavailable")
        source._open_pull_requests = [old]
        def request(url):
            if 'unavailable' in url:
                raise socket.timeout()
            return [dict(number=2, title="Updated", updated_at="2026-10-29T12:00:00Z")]
        source._request_json = request
        result = source._fetch_open_pull_requests()
        self.assertEqual([pr.number for pr in result], [2, 1])

    def test_large_coverage_preserves_api_budget_and_cooldown_preserves_state(self):
        source = GitHubEventSource(enabled=True, token="test", repos=[f"owner/r{i}" for i in range(74)], poll_seconds=60, fetch_deployments=False)
        self.assertGreaterEqual(source.effective_poll_seconds, 133)
        source._rate_limit_until = float("inf")
        source._fetch_open_pull_requests = lambda: self.fail("Must not query during cooldown")
        now = datetime.now(timezone.utc)
        source._refresh_sync(now, now, False)

    def test_owned_and_explicit_coverage_paginate_and_deduplicate(self):
        source = GitHubEventSource(enabled=True, token="test", repos=["org/shared"], include_owned=True, fetch_pull_requests=2)
        def request(url):
            if "/user/repos" in url:
                return [{"full_name": "me/shared"}, {"full_name": "ORG/shared"}]
            if "&page=2" in url:
                return [{"number": 3, "title": "Third", "user": {"login": "someone"}}]
            return [{"number": 1, "title": "One", "draft": True}, {"number": 2, "title": "Two"}]
        source._request_json = request
        now = datetime(2026, 10, 29, tzinfo=timezone.utc)
        source._discover_repositories(now)
        self.assertEqual(len(source.repos), 2)
        prs = source._fetch_open_pull_requests()
        self.assertEqual(len(prs), 6)
        source._queue_open_pull_request_events(prs, now)
        self.assertEqual(source._pending_events, [])  # Initial inventory is silent.
        created = now + timedelta(seconds=1)
        additions = [PullRequestSummary(repo.split('/')[-1], 4, 'New', 'anyone', draft=draft,
                                       repository=repo, created_at=created)
                     for repo, draft in zip(source.repos, (True, False))]
        source._queue_open_pull_request_events([*prs, *additions], created)
        self.assertEqual(len(source._pending_events), 2)
        self.assertEqual(len({event.external_id for event in source._pending_events}), 2)
        self.assertIn(EventCategory.PULL_REQUEST, {event.category for event in source._pending_events})

    def test_poll_baselines_existing_prs_then_emits_a_new_pull_request(self):
        source = GitHubEventSource(
            enabled=True,
            token="token",
            repos=["owner/repo"],
            poll_seconds=0,
            fetch_deployments=False,
        )
        source._request_json = lambda _url: [
            {
                "number": 42,
                "title": "Add ambient PR encounters",
                "user": {"login": "dev"},
                "draft": False,
            }
        ]
        now = datetime(2026, 5, 26, tzinfo=timezone.utc)

        source._refresh_sync(now, now, False)
        self.assertEqual(source._pending_events, [])
        source._request_json = lambda _url: [{"number": 43, "title": "New", "created_at": (now + timedelta(seconds=1)).isoformat()}]

        events = []
        for _ in range(20):
            events.extend(source.poll(now + timedelta(seconds=2)))
            if events:
                break
            time.sleep(0.01)

        self.assertFalse(source._refresh_running)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].category, EventCategory.PULL_REQUEST)
        self.assertEqual(events[0].external_id, "owner/repo#43")

    def test_network_disconnect_does_not_kill_refresh_worker_with_traceback(self):
        source = GitHubEventSource(
            enabled=True,
            token="token",
            repos=["owner/repo"],
            poll_seconds=0,
            fetch_deployments=False,
        )
        source._request_json = lambda _url: (_ for _ in ()).throw(http.client.RemoteDisconnected())
        now = datetime(2026, 5, 26, tzinfo=timezone.utc)

        events = source.poll(now)
        for _ in range(20):
            if not source._refresh_running:
                break
            time.sleep(0.01)

        self.assertEqual(events, [])
        self.assertFalse(source._refresh_running)
        self.assertEqual(source.open_pull_requests(), [])

    def test_socket_timeout_does_not_kill_refresh_worker_with_traceback(self):
        source = GitHubEventSource(
            enabled=True,
            token="token",
            repos=["owner/repo"],
            poll_seconds=0,
            fetch_deployments=True,
        )
        source._request_json = lambda _url: (_ for _ in ()).throw(socket.timeout("timed out"))
        now = datetime(2026, 5, 26, tzinfo=timezone.utc)

        events = source.poll(now)
        for _ in range(20):
            if not source._refresh_running:
                break
            time.sleep(0.01)

        self.assertEqual(events, [])
        self.assertFalse(source._refresh_running)
        self.assertEqual(source.open_pull_requests(), [])

    def test_refresh_worker_swallows_transient_network_errors(self):
        source = GitHubEventSource(
            enabled=True,
            token="token",
            repos=["owner/repo"],
            poll_seconds=0,
            fetch_deployments=True,
        )
        source._refresh_sync = lambda _now, _since, _include_closed: (_ for _ in ()).throw(
            http.client.RemoteDisconnected()
        )
        now = datetime(2026, 5, 26, tzinfo=timezone.utc)

        events = source.poll(now)
        for _ in range(20):
            if not source._refresh_running:
                break
            time.sleep(0.01)

        self.assertEqual(events, [])
        self.assertFalse(source._refresh_running)


if __name__ == "__main__":
    unittest.main()
