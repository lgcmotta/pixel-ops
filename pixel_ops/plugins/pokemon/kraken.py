"""Pokemon-owned companion projection, sharing the primary encounter clock."""
from copy import copy
from datetime import datetime, timedelta
from io import BytesIO
import json

from PIL import Image

from pixel_ops.core.browser_view import BrowserView
from pixel_ops.events.base import EventCategory
from pixel_ops.plugins.pokemon.game.day_night import day_night_palette
from pixel_ops.plugins.pokemon.game.state_machine import GamePhase
from pixel_ops.render.renderer import PixelRenderer


def countdown_meeting(events, now):
    """A continuous, absolute window: start minus five minutes to start plus one."""
    unique = {}
    for event in events:
        if event is None or event.all_day:
            continue
        if event.starts_at - timedelta(minutes=5) <= now < event.starts_at + timedelta(minutes=1):
            unique.setdefault((event.uid or event.title.strip().casefold(), event.starts_at), event)
    return min(unique.values(), key=lambda event: (event.starts_at, event.title.casefold()), default=None)


class KrakenProjection:
    def __init__(self, settings):
        self.settings = settings
        self.last_meeting = None
        self._battle_scene = None

    def view(self, scene, values, now: datetime):
        events = [values.get("calendar.next_updated"), *(values.get("calendar.today_updated") or [])]
        # Today's observation rolls at midnight, but a 23:59 meeting lasts to 00:00.
        if self.last_meeting and self.last_meeting.starts_at.astimezone(now.tzinfo).date() < now.date():
            events.append(self.last_meeting)
        meeting = countdown_meeting(events, now) if self.settings.get("meeting_countdown", True) else None
        show_off_stage = values.get("presentation.show_off_stage")
        show_off_meeting_end = values.get("presentation.show_off_meeting_end")
        if show_off_stage in ("intro", "outro") or (show_off_meeting_end and now >= show_off_meeting_end):
            meeting = None
        self.last_meeting = meeting
        state = {"mode": "thermal", "observed_at": now.isoformat(), "timezone": str(now.tzinfo)}
        if values.get("presentation.show_off"):
            state["show_off"] = True
            state["show_off_stage"] = show_off_stage
        metrics = values.get("system.metrics_updated")
        if metrics and 0 <= (now - metrics.observed_at).total_seconds() <= 10:
            gpu = next((metric for metric in metrics.metrics if metric.key == "gpu_temperature" and metric.status != "unknown"), None)
            if gpu and gpu.unit == "C" and gpu.numeric_value is not None:
                state["temperatures"] = {"gpu": gpu.numeric_value, "observed_at": metrics.observed_at.isoformat()}
        if meeting:
            state.update(mode="meeting", meeting={
                "title": meeting.title, "calendar": meeting.calendar_name or "Calendar",
                "starts_at": meeting.starts_at.isoformat(),
                "ends_at": (show_off_meeting_end or meeting.starts_at + timedelta(minutes=1)).isoformat(),
                "time_label": meeting.starts_at.astimezone(now.tzinfo).strftime("%H:%M"),
            })
        encounter = scene.encounter
        phase = scene.state.phase
        battle = (self.settings.get("pr_battles", True) and encounter.event
                  and encounter.event.category == EventCategory.PULL_REQUEST and scene._is_battle_phase(phase))
        image = None
        if battle:
            state.update(mode="battle", battle={
                "pokemon": encounter.pokemon.name.upper(), "number": encounter.pokemon.number,
                "phase": phase.value, "repository": encounter.pr_repository,
                "pr_number": encounter.pr_number, "reference": encounter.pr_reference,
                "label": {
                    GamePhase.ENCOUNTER_START: "A new encounter!", GamePhase.POKEMON_APPEARS: "A wild Pokemon appeared!",
                    GamePhase.ASH_THROWS: "ASH used POKE BALL!", GamePhase.BALL_SHAKE: "Will it stay?",
                    GamePhase.CAUGHT: "PR encounter logged!",
                }[phase],
            })
            # A shallow presentation copy shares sprites and the actual phase clock.
            # It never advances, enqueues, captures, or writes game persistence.
            if self._battle_scene is None:
                self._battle_scene = copy(scene)
                self._battle_scene.renderer = PixelRenderer(384, 280)
                self._battle_scene.display_layout = {"game": {"x": 0, "y": 0, "width": 384, "height": 280}}
                self._battle_scene._battle_backgrounds = {}
                self._battle_scene._show_pr_identity = False
            renderer = self._battle_scene
            renderer.encounter, renderer.state = encounter, scene.state
            renderer.frame, renderer.current_mood = scene.frame, scene.current_mood
            palette = day_night_palette(now.hour)
            canvas = Image.new("RGB", (384, 280), palette.sky_bottom)
            renderer._draw_battle_scene(canvas, phase, palette)
            buffer = BytesIO()
            canvas.save(buffer, format="PNG", compress_level=1)
            image = buffer.getvalue()
            state["frame"] = scene.frame
        return BrowserView(json.dumps(state, ensure_ascii=False).encode("utf-8"), image)
