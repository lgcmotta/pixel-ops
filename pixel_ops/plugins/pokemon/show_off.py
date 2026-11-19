"""Recording scenario: game-owned sample state, never a provider mutation."""
from datetime import timedelta
from uuid import uuid4

from pixel_ops.data_sources.calendar import CalendarEvent
from pixel_ops.events.base import EventCategory, EventPriority, WorkEvent
from pixel_ops.events.github_events import PullRequestSummary
from pixel_ops.plugins.pokemon.game.state_machine import GamePhase


class ShowOffScenario:
    intro_seconds = 5
    countdown_seconds = 300
    first_pr_delay_seconds = 5
    capture_gap_seconds = 8
    starting_now_seconds = 5
    outro_seconds = 10

    def __init__(self, settings):
        self.owner = str(settings.get("owner") or "").casefold()
        repositories = settings.get("repositories")
        self.repositories = [
            repo for repo in repositories
            if isinstance(repo, str) and len(repo.split("/")) == 2 and all(repo.split("/"))
        ] if isinstance(repositories, list) else []
        if not self.repositories:
            self.repositories = ["demo/sample-project", "demo/pixel-ops"]
        self.run_id = str(settings.get("run_id") or uuid4())
        self.started_at = None
        self.meetings = []
        self.personal_prs = []
        self.pr_sent = False
        self.cycle = 0
        self.stage = "intro"
        self.outro_started_at = None
        self.next_pr_at = None
        self.active_pr_id = None
        self.capture_seen = False
        self.pr_count = 0
        self.simulated_prs = []

    def update_pull_requests(self, pull_requests):
        # Unknown/short identities cannot establish ownership. Fail closed.
        self.personal_prs = [pr for pr in pull_requests if self._owned(pr)]

    def _owned(self, pr):
        identity = getattr(pr, "repository", "") or getattr(pr, "repo", "")
        parts = identity.split("/")
        return bool(self.owner) and len(parts) == 2 and parts[0].casefold() == self.owner and bool(parts[1])

    def _start_cycle(self, now):
        self.cycle += 1
        self.started_at = now
        self.stage = "intro"
        self.outro_started_at = None
        self.active_pr_id = None
        self.capture_seen = False
        self.pr_sent = False
        self.pr_count = 0
        self.simulated_prs = []
        self.meetings = [CalendarEvent(
            title, now + timedelta(seconds=self.intro_seconds + self.countdown_seconds, minutes=minutes),
            ends_at=now + timedelta(seconds=self.intro_seconds + self.countdown_seconds, minutes=minutes + 25),
            calendar_name="PixelOps Demo", uid=f"show-off:{self.run_id}:{self.cycle}:{index}",
        ) for index, (title, minutes) in enumerate((
            ("Standup Meeting", 0), ("Backlog Grooming", 30),
            ("Sprint Planning", 60), ("Design Review", 90),
        ))]
        self.next_pr_at = now + timedelta(seconds=self.intro_seconds + self.first_pr_delay_seconds)

    def _observe_capture(self, scene, now):
        if not self.active_pr_id:
            return
        event = scene.encounter.event
        if event and event.external_id == self.active_pr_id and scene._is_battle_phase(scene.state.phase):
            self.capture_seen = True
        if self.capture_seen and scene.state.phase == GamePhase.WALKING and not scene.encounter_system.queue:
            self.active_pr_id = None
            self.capture_seen = False
            self.next_pr_at = now + timedelta(seconds=self.capture_gap_seconds)

    def _capture_budget(self, scene):
        # Respect configured durations and message-reading minimums. Stop adding
        # encounters near meeting start, leaving time for the final countdown.
        return sum(scene.state.duration_for_phase(phase) for phase in GamePhase if phase != GamePhase.WALKING) + 2

    def _receive_pr(self, scene, now):
        repositories = list(dict.fromkeys([*self.repositories, *[
            pr.repository or pr.repo for pr in self.personal_prs
        ]]))
        repository = repositories[self.pr_count % len(repositories)]
        short_repo = repository.split("/", 1)[1]
        number = max([41, *[pr.number for pr in self.personal_prs if (pr.repository or pr.repo).casefold() == repository.casefold()]]) + self.pr_count + 1
        priorities = (EventPriority.HIGH, EventPriority.LOW, EventPriority.MEDIUM)
        priority = priorities[self.pr_count % len(priorities)]
        self.pr_count += 1
        self.pr_sent = True
        self.active_pr_id = f"show-off:{self.run_id}:{self.cycle}:pr:{self.pr_count}"
        self.capture_seen = False
        event = WorkEvent(
            category=EventCategory.PULL_REQUEST, title=f"New PR: {short_repo} #{number}",
            source="show_off", repo=short_repo, actor=self.owner,
            priority=priority, occurred_at=now, external_id=self.active_pr_id,
            metadata={"repository": repository, "number": str(number), "action": "opened", "show_off": "true"},
        )
        scene.enqueue_event(event)
        # Start the regular encounter transition without an extra idle delay.
        scene.state.set_phase(GamePhase.WALKING, now - timedelta(seconds=scene.state.duration_for_phase(GamePhase.WALKING)))
        simulated = PullRequestSummary(
            repo=short_repo, repository=repository, number=number,
            title="Improve project workflow", author=self.owner,
            updated_at=now, created_at=now,
        )
        self.simulated_prs = [simulated, *self.simulated_prs[:5]]

    def tick(self, scene, values, now):
        if self.started_at is None or now < self.started_at:
            self._start_cycle(now)
        self._observe_capture(scene, now)
        if self.stage == "outro" and (now - self.outro_started_at).total_seconds() >= self.outro_seconds:
            self._start_cycle(now)
        elapsed = (now - self.started_at).total_seconds()
        if self.stage == "intro" and elapsed >= self.intro_seconds:
            self.stage = "meeting"
        meeting_start = self.meetings[0].starts_at
        if self.stage == "meeting":
            idle = scene.state.phase == GamePhase.WALKING and not scene.encounter_system.queue and not self.active_pr_id
            if now >= meeting_start + timedelta(seconds=self.starting_now_seconds) and idle:
                self.stage = "outro"
                self.outro_started_at = now
            elif (idle and now >= self.next_pr_at
                  and now + timedelta(seconds=self._capture_budget(scene)) < meeting_start):
                self._receive_pr(scene, now)
        values["calendar.today_updated"] = self.meetings
        values["calendar.next_updated"] = next((event for event in self.meetings if event.starts_at >= now), None)
        values["presentation.show_off"] = True
        values["presentation.show_off_stage"] = self.stage
        values["presentation.show_off_meeting_end"] = meeting_start + timedelta(seconds=self.starting_now_seconds)
        demo_ids = {((pr.repository or pr.repo).casefold(), pr.number) for pr in self.simulated_prs}
        values["github.pull_requests_updated"] = [*self.simulated_prs, *[
            pr for pr in self.personal_prs if ((pr.repository or pr.repo).casefold(), pr.number) not in demo_ids
        ]]
