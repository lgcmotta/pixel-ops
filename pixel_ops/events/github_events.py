from __future__ import annotations

import http.client
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock, Thread
from pathlib import Path

from pixel_ops.events.base import EventCategory, EventPriority, WorkEvent

_GITHUB_REQUEST_ERRORS = (urllib.error.URLError, OSError, http.client.HTTPException)
_GITHUB_PAYLOAD_ERRORS = _GITHUB_REQUEST_ERRORS + (KeyError, ValueError, TypeError)
_GITHUB_WORKFLOW_ERRORS = _GITHUB_PAYLOAD_ERRORS + (AttributeError,)


@dataclass(frozen=True)
class PullRequestSummary:
    repo: str
    number: int
    title: str
    author: str
    draft: bool = False
    review_state: str = "open"
    updated_at: datetime | None = None
    repository: str = ""
    created_at: datetime | None = None

    @property
    def label(self) -> str:
        state = "DRAFT" if self.draft else self.review_state.upper()
        return f"{self.repo} #{self.number} {state}: {self.title}"


class GitHubEventSource:
    """Polls GitHub for open pull requests and keeps a compact HUD list."""

    def __init__(
        self,
        enabled: bool = False,
        token: str | None = None,
        repos: list[str] | None = None,
        poll_seconds: int = 300,
        max_pull_requests: int = 4,
        fetch_pull_requests: int | None = None,
        fetch_deployments: bool = True,
        deployment_workflows: list[str] | None = None,
        startup_lookback_seconds: int = 3600,
        timeout_seconds: int = 20,
        include_owned: bool = False,
        discovery_seconds: int = 900,
        cache_path: Path | None = None,
    ):
        self.enabled = enabled
        self.token = token or os.environ.get("PIXEL_OPS_GITHUB_TOKEN", "")
        self.repos = repos or []
        self._configured_repos = list(self.repos)
        self.include_owned = include_owned
        self.discovery_seconds = max(60, int(discovery_seconds))
        self._last_discovery_at: datetime | None = None
        self._rate_limit_until = 0.0
        self.poll_seconds = poll_seconds
        self.max_pull_requests = max_pull_requests
        self.fetch_pull_requests = fetch_pull_requests or max(max_pull_requests, 20)
        self.fetch_deployments = fetch_deployments
        self.deployment_workflows = tuple(name.lower() for name in (deployment_workflows or []) if name)
        self.startup_lookback_seconds = max(self.poll_seconds, int(startup_lookback_seconds))
        self.timeout_seconds = timeout_seconds
        self._last_poll_at: datetime | None = None
        self._last_open_fetch_at: datetime | None = None
        self._open_pull_requests: list[PullRequestSummary] = []
        self._closed_pull_requests: list[PullRequestSummary] = []
        self._pull_requests: list[PullRequestSummary] = []
        self._pending_events: list[WorkEvent] = []
        self._seen: set[str] = set()
        self._known_pull_requests: set[str] = set()
        self._repository_baselines: dict[str, datetime] = {}
        self._successful_open_repos: set[str] = set()
        self._lock = Lock()
        self._refresh_running = False
        self.debug = _env_bool("PIXEL_OPS_DEBUG_EVENTS")
        self.cache_path = cache_path
        self._cache_identity = hashlib.sha256(json.dumps([self.token, sorted(r.lower() for r in self._configured_repos), self.include_owned]).encode()).hexdigest()
        self._load_cache()

    def _load_cache(self) -> None:
        if self.cache_path is None:
            return
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            if data.get("identity") != self._cache_identity:
                return
            def decode(items):
                return [PullRequestSummary(**{**item, "updated_at": self._parse_github_datetime(item.get("updated_at")),
                                             "created_at": self._parse_github_datetime(item.get("created_at"))}) for item in items]
            opened, closed = decode(data["open"]), decode(data["closed"])
            self._open_pull_requests, self._closed_pull_requests = opened, closed
            self._pull_requests = [*opened, *closed][:self.max_pull_requests]
            self._seen = {str(key) for key in data.get("seen_events", [])}
            self._known_pull_requests = {str(key) for key in data.get("known_pull_requests", [])}
            self._known_pull_requests.update(f"{pr.repository or pr.repo}#{pr.number}".lower() for pr in [*opened, *closed])
            self._repository_baselines = {repo: stamp for repo, value in data.get("repository_baselines", {}).items()
                                          if (stamp := self._parse_github_datetime(value)) is not None}
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            return

    def _save_cache(self) -> None:
        if self.cache_path is None:
            return
        try:
            def encode(items):
                return [{**asdict(item), "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                         "created_at": item.created_at.isoformat() if item.created_at else None} for item in items]
            data = {"identity": self._cache_identity, "open": encode(self._open_pull_requests), "closed": encode(self._closed_pull_requests),
                    "seen_events": sorted(self._seen), "known_pull_requests": sorted(self._known_pull_requests),
                    "repository_baselines": {repo: stamp.isoformat() for repo, stamp in self._repository_baselines.items()}}
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.cache_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(data), encoding="utf-8")
            temporary.replace(self.cache_path)
        except OSError:
            pass

    def warm(self) -> None:
        if not self.enabled or not self.token or not (self.repos or self.include_owned):
            return
        now = datetime.now(timezone.utc)
        since = now - timedelta(seconds=self.startup_lookback_seconds)
        with self._lock:
            if self._refresh_running:
                return
            self._refresh_running = True
            self._last_poll_at = now
            self._last_open_fetch_at = now
        try:
            self._refresh_sync(now, since, include_closed=True)
        finally:
            with self._lock:
                self._refresh_running = False

    def poll(self, now: datetime) -> list[WorkEvent]:
        self._refresh(now)
        with self._lock:
            events = self._pending_events
            self._pending_events = []
        return events

    def open_pull_requests(self, now: datetime | None = None) -> list[PullRequestSummary]:
        if now:
            self._refresh_hud(now)
        with self._lock:
            return list(self._pull_requests)

    def _refresh(self, now: datetime) -> None:
        if not self.enabled or not self.token or not (self.repos or self.include_owned):
            return
        if self._last_poll_at and (now - self._last_poll_at).total_seconds() < self.effective_poll_seconds:
            return

        previous_poll_at = self._last_poll_at
        self._last_poll_at = now
        since = previous_poll_at or now - timedelta(seconds=self.poll_seconds)
        self._start_refresh_worker(now, since, include_closed=True)

    def _refresh_hud(self, now: datetime) -> None:
        # Both event and observation readers share one network scheduler. An
        # earlier HUD-only refresh must not starve closed/merged event polling.
        self._refresh(now)

    def _start_refresh_worker(self, now: datetime, since: datetime, include_closed: bool) -> None:
        with self._lock:
            if self._refresh_running:
                return
            self._refresh_running = True
            self._last_open_fetch_at = now

        def worker() -> None:
            try:
                self._refresh_sync(now, since, include_closed)
            except _GITHUB_WORKFLOW_ERRORS as error:
                self._debug(f"refresh error: {type(error).__name__}: {error}")
            finally:
                with self._lock:
                    self._refresh_running = False

        Thread(target=worker, name="pixel-ops-github-refresh", daemon=True).start()

    def _refresh_sync(self, now: datetime, since: datetime, include_closed: bool) -> None:
        if time.time() < self._rate_limit_until:
            return
        self._discover_repositories(now)
        open_pull_requests = self._fetch_open_pull_requests()
        # Open PRs should reach the HUD and encounter queue without waiting for
        # closed-history pagination across every covered repository.
        with self._lock:
            self._open_pull_requests = open_pull_requests
            self._pull_requests = [*open_pull_requests, *self._closed_pull_requests][: self.max_pull_requests]
            self._queue_open_pull_request_events(open_pull_requests, now)
            self._save_cache()
        closed_pull_requests: list[PullRequestSummary] = []
        closed_events: list[WorkEvent] = []
        deployment_events: list[WorkEvent] = []
        if include_closed:
            closed_pull_requests, closed_events = self._fetch_closed_pull_request_updates(now, since)
            deployment_events = self._fetch_deployment_events(now, since)
        with self._lock:
            self._open_pull_requests = open_pull_requests
            if include_closed:
                self._closed_pull_requests = closed_pull_requests
            combined = [*open_pull_requests, *self._closed_pull_requests]
            self._pull_requests = combined[: self.max_pull_requests]
            self._debug(
                f"prs open={len(open_pull_requests)} closed={len(self._closed_pull_requests)} "
                f"hud={len(self._pull_requests)}"
            )
            self._pending_events.extend(closed_events)
            self._pending_events.extend(deployment_events)
            self._save_cache()

    def _refresh_open_pull_requests(self, now: datetime) -> list[PullRequestSummary]:
        if self._last_open_fetch_at and (now - self._last_open_fetch_at).total_seconds() < self.effective_poll_seconds:
            return list(self._open_pull_requests)
        self._last_open_fetch_at = now
        self._open_pull_requests = self._fetch_open_pull_requests()
        return list(self._open_pull_requests)

    def _fetch_open_pull_requests(self) -> list[PullRequestSummary]:
        pull_requests: list[PullRequestSummary] = []
        self._successful_open_repos = set()
        for repo in self.repos:
            encoded_repo = urllib.parse.quote(repo, safe="/")
            url = f"https://api.github.com/repos/{encoded_repo}/pulls?state=open&sort=created&direction=desc&per_page={self.fetch_pull_requests}"
            try:
                repository_prs = []
                for item in self._pages(url, self.fetch_pull_requests):
                    repository_prs.append(
                        PullRequestSummary(
                            repo=repo.split("/")[-1],
                            number=int(item["number"]),
                            title=str(item["title"]),
                            author=str(item.get("user", {}).get("login", "unknown")),
                            draft=bool(item.get("draft", False)),
                            review_state="open",
                            repository=repo,
                            updated_at=self._parse_github_datetime(item.get("updated_at")),
                            created_at=self._parse_github_datetime(item.get("created_at")),
                        )
                    )
                pull_requests.extend(repository_prs)
                self._successful_open_repos.add(repo.lower())
            except _GITHUB_PAYLOAD_ERRORS as error:
                self._debug(f"open_prs error repo={repo}: {type(error).__name__}: {error}")
                # A failed request is not evidence that those PRs disappeared.
                pull_requests.extend(pr for pr in self._open_pull_requests if (pr.repository or pr.repo).lower() == repo.lower())
                continue
        pull_requests.sort(key=lambda pr: pr.updated_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return pull_requests

    def _queue_open_pull_request_events(self, pull_requests: list[PullRequestSummary], now: datetime) -> None:
        for pr in pull_requests:
            key = f"{pr.repository or pr.repo}#{pr.number}"
            known_key = key.lower()
            if known_key in self._known_pull_requests:
                continue
            self._known_pull_requests.add(known_key)
            baseline = self._repository_baselines.get((pr.repository or pr.repo).lower())
            # A first successful scan is inventory, not a batch of new arrivals.
            # Edits/reopens of older PRs and long-offline history are inventory too.
            if (baseline is None or pr.created_at is None
                    or pr.created_at < baseline.replace(microsecond=0)
                    or (now - pr.created_at).total_seconds() > self.startup_lookback_seconds
                    or pr.created_at > now):
                continue
            if key in self._seen:
                continue
            self._seen.add(key)
            self._pending_events.append(
                WorkEvent(
                    category=EventCategory.PULL_REQUEST,
                    title=f"{pr.repo} #{pr.number} opened",
                    detail=pr.title,
                    priority=EventPriority.MEDIUM,
                    source="github",
                    repo=pr.repo,
                    actor=pr.author,
                    external_id=key,
                    occurred_at=pr.created_at,
                    metadata={"action": "opened", "draft": "true" if pr.draft else "false", "repository": pr.repository or pr.repo, "number": str(pr.number)},
                )
            )
            self._debug(f"queued {self._pending_events[-1].category.value} {key}")
        for repo in self._successful_open_repos:
            self._repository_baselines.setdefault(repo, now)

    def _fetch_closed_pull_request_updates(
        self,
        now: datetime,
        since: datetime,
    ) -> tuple[list[PullRequestSummary], list[WorkEvent]]:
        summaries: list[PullRequestSummary] = []
        events: list[WorkEvent] = []
        for repo in self.repos:
            encoded_repo = urllib.parse.quote(repo, safe="/")
            url = (
                f"https://api.github.com/repos/{encoded_repo}/pulls"
                f"?state=closed&sort=updated&direction=desc&per_page={self.max_pull_requests}"
            )
            short_repo = repo.split("/")[-1]
            try:
                for item in self._pages(url, self.max_pull_requests, since=since):
                    closed_at = self._parse_github_datetime(item.get("closed_at"))
                    if closed_at is None:
                        continue
                    number = int(item["number"])
                    self._known_pull_requests.add(f"{repo}#{number}".lower())
                    title = str(item["title"])
                    author = str(item.get("user", {}).get("login", "unknown"))
                    merged = bool(item.get("merged_at"))
                    state = "merged" if merged else "closed"
                    summaries.append(
                        PullRequestSummary(
                            repo=short_repo,
                            number=number,
                            title=title,
                            author=author,
                            draft=False,
                            review_state=state,
                            updated_at=closed_at,
                            repository=repo,
                        )
                    )
                    if closed_at <= since:
                        continue
                    key = f"{repo}#{number}:{state}"
                    if key in self._seen:
                        continue
                    self._seen.add(key)
                    events.append(
                        WorkEvent(
                            category=EventCategory.MERGE if merged else EventCategory.PR_CLOSED,
                            title=f"{short_repo} #{number} {state}",
                            detail=title,
                            priority=EventPriority.MEDIUM,
                            source="github",
                            repo=short_repo,
                            actor=author,
                            external_id=key,
                            occurred_at=closed_at.astimezone(now.tzinfo),
                            metadata={"state": state},
                        )
                    )
            except _GITHUB_PAYLOAD_ERRORS as error:
                self._debug(f"closed_prs error repo={repo}: {type(error).__name__}: {error}")
                continue
        summaries.sort(key=lambda item: item.updated_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return summaries[: self.fetch_pull_requests], events

    def _fetch_deployment_events(self, now: datetime, since: datetime) -> list[WorkEvent]:
        if not self.fetch_deployments:
            return []
        events: list[WorkEvent] = []
        for repo in self.repos:
            encoded_repo = urllib.parse.quote(repo, safe="/")
            short_repo = repo.split("/")[-1]
            url = f"https://api.github.com/repos/{encoded_repo}/actions/runs?per_page=10"
            try:
                payload = self._request_json(url)
                for item in payload.get("workflow_runs", []):
                    updated_at = self._parse_github_datetime(item.get("updated_at"))
                    if updated_at is None or updated_at <= since:
                        continue
                    workflow = str(item.get("name") or "workflow")
                    if self.deployment_workflows and workflow.lower() not in self.deployment_workflows:
                        continue
                    status = str(item.get("status") or "").lower()
                    conclusion = str(item.get("conclusion") or "").lower()
                    category = self._workflow_category(status, conclusion)
                    if category is None:
                        continue
                    run_id = str(item.get("id") or item.get("run_number") or workflow)
                    state = conclusion or status
                    key = f"{repo}:workflow:{run_id}:{state}"
                    if key in self._seen:
                        continue
                    self._seen.add(key)
                    events.append(
                        WorkEvent(
                            category=category,
                            title=f"{workflow} {self._workflow_title_state(category)}",
                            detail=short_repo,
                            priority=EventPriority.HIGH if category == EventCategory.BUILD_BROKEN else EventPriority.MEDIUM,
                            source="github",
                            repo=short_repo,
                            external_id=key,
                            occurred_at=updated_at.astimezone(now.tzinfo),
                            metadata={"workflow": workflow, "state": state},
                        )
                    )
                    self._debug(f"queued workflow category={category.value} key={key}")
            except _GITHUB_WORKFLOW_ERRORS as error:
                self._debug(f"workflow_runs error repo={repo}: {type(error).__name__}: {error}")
                continue
        return events

    @staticmethod
    def _workflow_category(status: str, conclusion: str) -> EventCategory | None:
        if status in ("queued", "in_progress", "requested", "pending", "waiting"):
            return EventCategory.DEPLOY_STARTED
        if conclusion == "success":
            return EventCategory.DEPLOY_COMPLETED
        if conclusion in ("failure", "cancelled", "timed_out", "action_required", "startup_failure"):
            return EventCategory.BUILD_BROKEN
        return None

    def _pages(self, url: str, page_size: int, since: datetime | None = None):
        page_size = max(1, min(100, page_size))
        # GitHub caps per_page at 100. Normalize before deciding whether to continue.
        parsed = urllib.parse.urlsplit(url)
        query = dict(urllib.parse.parse_qsl(parsed.query))
        query["per_page"] = str(page_size)
        for page in range(1, 1001):
            if page > 1:
                query["page"] = str(page)
            page_url = urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query)))
            items = self._request_json(page_url)
            if not isinstance(items, list):
                raise ValueError("Expected a GitHub list")
            yield from items
            if len(items) < page_size:
                return
            if since is not None:
                updated = [self._parse_github_datetime(item.get("updated_at")) for item in items]
                if updated and all(stamp is not None and stamp <= since for stamp in updated):
                    return
        raise ValueError("GitHub pagination exceeded safety bound")

    def _discover_repositories(self, now: datetime):
        if not self.include_owned or (self._last_discovery_at and (now - self._last_discovery_at).total_seconds() < self.discovery_seconds):
            return
        try:
            owned = [str(item["full_name"]) for item in self._pages("https://api.github.com/user/repos?affiliation=owner&per_page=100", 100)
                     if not item.get("archived")]
        except _GITHUB_PAYLOAD_ERRORS:
            return  # Preserve the last successfully discovered coverage.
        self.repos = list({repo.lower(): repo for repo in [*self._configured_repos, *owned]}.values())
        self._last_discovery_at = now

    @property
    def effective_poll_seconds(self) -> float:
        # Two base PR requests per repository, leaving budget for pagination,
        # discovery, other clients and manual refreshes under GitHub's usual
        # 5,000/hour token limit. The configured interval remains the minimum.
        requests_per_cycle = len(self.repos) * (3 if self.fetch_deployments else 2)
        return max(self.poll_seconds, requests_per_cycle * 3600 / 4000)

    @staticmethod
    def _workflow_title_state(category: EventCategory) -> str:
        if category == EventCategory.DEPLOY_STARTED:
            return "is deploying"
        if category == EventCategory.DEPLOY_COMPLETED:
            return "deployed"
        return "needs attention"

    @staticmethod
    def _parse_github_datetime(value: object) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

    def _request_json(self, url: str):
        if time.time() < self._rate_limit_until:
            raise urllib.error.URLError("GitHub rate-limit cooldown")
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "pixel-ops",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                if response.headers.get("X-RateLimit-Remaining") == "0":
                    self._rate_limit_until = float(response.headers.get("X-RateLimit-Reset") or time.time() + 60)
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code in (403, 429) and (error.headers.get("X-RateLimit-Remaining") == "0" or error.headers.get("Retry-After")):
                self._rate_limit_until = max(time.time() + float(error.headers.get("Retry-After") or 60), float(error.headers.get("X-RateLimit-Reset") or 0))
            raise

    def _debug(self, message: str) -> None:
        if self.debug:
            print(f"[pixel-ops github] {message}", file=sys.stderr)


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")
