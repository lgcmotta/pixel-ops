from datetime import datetime, timedelta
import json
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from PIL import ImageDraw
import pytest

from pixel_ops.core.app import PixelOpsApp
from pixel_ops.data_sources.calendar import CalendarEvent
from pixel_ops.events.base import EventCategory, WorkEvent
from pixel_ops.events.github_events import PullRequestSummary
from pixel_ops.events.platform import PixelOpsEvent
from pixel_ops.plugins.pokemon.engine import PokemonEngine
from pixel_ops.plugins.pokemon.game.state_machine import GamePhase
from pixel_ops.plugins.pokemon.plugin import PokemonPlugin
from pixel_ops.plugins.pokemon.scenes.overworld_scene import OverworldScene
from pixel_ops.render.account_hud import draw_hardware, draw_pr_activity, draw_quota
from pixel_ops.plugins.pokemon.game.day_night import day_night_palette


NOW = datetime(2026, 10, 30, 9, 55, tzinfo=ZoneInfo('America/Sao_Paulo'))
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def engine():
    scene = OverworldScene(1920, 480, 'America/Sao_Paulo', lazy_download=False, scanlines=False)
    return PokemonEngine(scene, [], kraken_settings={'enabled': True}, show_off_settings={'enabled': True, 'run_id': 'test', 'owner': 'demo'})


def observation(kind, value):
    return PixelOpsEvent.observation(kind, 'test', value, NOW)


def tick(engine, seconds):
    engine.consume(PixelOpsEvent.tick(NOW + timedelta(seconds=seconds)))
    return engine.render()


def test_intro_countdown_then_pr_battle_on_both_views(engine):
    tick(engine, 0)
    state = json.loads(engine.browser_views()['kraken'].state_json)
    assert state['mode'] == 'thermal' and state['show_off_stage'] == 'intro'
    tick(engine, 4.99)
    assert json.loads(engine.browser_views()['kraken'].state_json)['mode'] == 'thermal'
    tick(engine, 5)
    state = json.loads(engine.browser_views()['kraken'].state_json)
    assert state['mode'] == 'meeting'
    assert state['meeting']['title'] == 'Standup Meeting'
    assert state['meeting']['starts_at'] == (NOW + timedelta(seconds=305)).isoformat()
    tick(engine, 9.99)
    assert not engine.show_off.pr_sent
    tick(engine, 10)
    assert engine.scene.state.phase == GamePhase.ENCOUNTER_START
    assert engine.scene.encounter.event.metadata['repository'] == 'demo/sample-project'
    state = json.loads(engine.browser_views()['kraken'].state_json)
    assert state['mode'] == 'battle' and state['show_off']
    assert state['battle']['phase'] == engine.scene.state.phase.value
    assert state['battle']['number'] == engine.scene.encounter.pokemon.number
    assert engine.values['github.pull_requests_updated'][0].repository == 'demo/sample-project'


def advance(engine, seconds):
    now = NOW + timedelta(seconds=seconds)
    engine.consume(PixelOpsEvent.tick(now))
    engine.scene.advance(now)


def test_repeated_prs_wait_for_capture_and_countdown_breathing_space(engine):
    sends = []
    finished = []
    last_active = None
    for seconds in range(160):
        before = engine.show_off.pr_count
        advance(engine, seconds)
        if engine.show_off.pr_count != before:
            sends.append((seconds, engine.scene.encounter.event))
        if last_active and engine.show_off.active_pr_id is None:
            finished.append(seconds)
            assert engine.scene.state.phase == GamePhase.WALKING
            assert json.loads(engine.browser_views()['kraken'].state_json)['mode'] == 'meeting'
        last_active = engine.show_off.active_pr_id
        assert len(engine.scene.encounter_system.queue) <= 1
    assert len(sends) >= 3
    assert sends[0][0] == 10
    assert sends[0][1].metadata['repository'] == 'demo/sample-project'
    assert sends[1][1].metadata['repository'] == 'demo/pixel-ops'
    for (sent_at, _), ended_at in zip(sends[1:], finished):
        assert sent_at - ended_at >= 8
    assert len({event.external_id for _, event in sends}) == len(sends)
    assert len(engine.show_off.simulated_prs) <= 6


def test_outro_and_next_intro_give_fifteen_uninterrupted_thermal_seconds(engine):
    tick(engine, 0)
    first_uid = engine.show_off.meetings[0].uid
    # A late tick skips expired PR opportunities rather than creating a backlog.
    tick(engine, 305)
    assert json.loads(engine.browser_views()['kraken'].state_json)['mode'] == 'meeting'
    tick(engine, 309.99)
    assert json.loads(engine.browser_views()['kraken'].state_json)['mode'] == 'meeting'
    for seconds in (310, 319.99, 320, 324.99):
        tick(engine, seconds)
        assert json.loads(engine.browser_views()['kraken'].state_json)['mode'] == 'thermal'
    assert engine.show_off.cycle == 2
    assert engine.show_off.meetings[0].uid != first_uid
    assert not engine.show_off.pr_sent
    tick(engine, 325)
    state = json.loads(engine.browser_views()['kraken'].state_json)
    assert state['mode'] == 'meeting'
    assert state['meeting']['starts_at'] == (NOW + timedelta(seconds=625)).isoformat()
    tick(engine, 330)
    assert engine.show_off.pr_count == 1
    assert engine.scene.state.phase == GamePhase.ENCOUNTER_START


def test_a_long_capture_is_not_cut_off_at_the_meeting_boundary(engine):
    # Begin an encounter before lengthening it, as a slow/custom encounter may do.
    engine.scene.state.durations[GamePhase.CAUGHT] = 2.6
    for seconds in range(11):
        advance(engine, seconds)
    engine.scene.state.durations[GamePhase.CAUGHT] = 400
    for seconds in range(11, 400):
        advance(engine, seconds)
    assert engine.show_off.pr_count == 1
    assert engine.show_off.stage == 'meeting'
    assert engine.scene.state.phase == GamePhase.CAUGHT
    assert json.loads(engine.browser_views()['kraken'].state_json)['mode'] == 'battle'
    for seconds in range(400, 435):
        advance(engine, seconds)
        if engine.show_off.stage == 'outro':
            break
    assert engine.show_off.stage == 'outro'
    assert engine.scene.state.phase == GamePhase.WALKING


def test_private_meetings_events_and_unknown_repository_identities_are_not_projected(engine):
    private = CalendarEvent('Private enterprise strategy', NOW, calendar_name='Company secret')
    engine.consume(observation('calendar.next_updated', private))
    engine.consume(observation('calendar.today_updated', [private]))
    engine.consume(observation('social.companions_updated', {'person': 'Secret Person'}))
    engine.consume(observation('tasks.snapshot_updated', {'title': 'Private task'}))
    prs = [PullRequestSummary('repo', number, 'Private PR title' if number < 4 else 'Personal PR', 'author', repository=repo)
           for number, repo in enumerate(('external/private-project', 'another-owner/project', '', 'demo-other/fake', 'DEMO/pixel-ops'), 0)]
    engine.consume(observation('github.pull_requests_updated', prs))
    for category in (EventCategory.MEETING, EventCategory.PULL_REQUEST, EventCategory.MERGE):
        engine.consume(WorkEvent(category, 'Private PR or meeting title', repo='private/repo'))
    tick(engine, 0)
    assert engine.values['github.pull_requests_updated'] == [prs[-1]]
    assert 'tasks.snapshot_updated' not in engine.values
    assert 'social.companions_updated' not in engine.values
    assert not engine.scene.encounter_system.queue
    serialized = engine.browser_views()['kraken'].state_json.decode()
    assert 'Private' not in serialized and 'Company secret' not in serialized
    assert all(event.calendar_name == 'PixelOps Demo' for event in engine.values['calendar.today_updated'])


def test_provider_collection_continues_while_show_off_projects_samples(engine):
    class Source:
        calls = 0

        def poll(self, now):
            self.calls += 1
            return [observation('calendar.today_updated', [CalendarEvent('Private meeting', NOW)])]

    source = Source()
    app = PixelOpsApp(engine, [source])
    app.render_frame(NOW)
    app.render_frame(NOW + timedelta(seconds=1))
    assert source.calls == 2
    assert engine.values['calendar.today_updated'][0].title == 'Standup Meeting'


def test_plugin_uses_no_capture_store_ai_or_screen_rotation_in_show_off():
    from types import SimpleNamespace
    from tempfile import TemporaryDirectory
    config = {'game': {}, 'pokemon': {'cache_dir': 'cache', 'api_base_url': 'https://pokeapi.co/api/v2', 'sprite_base_url': 'https://example.com'}}
    args = SimpleNamespace(offline=False)
    display = {'timezone_primary': 'America/Sao_Paulo', 'show_off': {'enabled': True}}
    with TemporaryDirectory() as directory, patch('pixel_ops.plugins.pokemon.plugin.PixelOpsStateStore') as store, patch('requests.get', side_effect=AssertionError('Demo cannot download data')):
        app = PokemonPlugin().build_app(args, Path(directory), display, config, 1920, 480, 10, [], object(), [])
        assert app.engine.scene.capture_store is None
        assert app.screens is None
        for seconds in range(35):
            app.render_frame(NOW + timedelta(seconds=seconds))
        assert app.engine.scene.captured_pokemon
        store.assert_not_called()


def test_all_light_panel_text_uses_black():
    from PIL import Image
    from types import SimpleNamespace
    pal = day_night_palette(0)
    image = Image.new('RGB', (1920, 480))
    draw = ImageDraw.Draw(image)
    seen = []
    original = ImageDraw.ImageDraw.text

    def record(canvas, xy, text, *args, **kwargs):
        seen.append(kwargs['fill'])
        return original(canvas, xy, text, *args, **kwargs)

    with patch.object(ImageDraw.ImageDraw, 'text', record):
        draw_hardware(draw, None, NOW, (0, 0, 304, 388), pal)
        draw_quota(draw, None, NOW, (320, 0, 768, 208), pal)
        draw_pr_activity(draw, [PullRequestSummary('pixel-ops', 1, 'PR', 'demo', repository='demo/pixel-ops')], NOW, (800, 0, 1248, 168), pal)
    assert seen and all(color == (0, 0, 0) for color in seen)
