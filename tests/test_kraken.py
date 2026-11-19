from datetime import datetime, timedelta
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from PIL import Image
import pytest

from pixel_ops.core.app import PixelOpsApp
from pixel_ops.core.browser_view import BrowserView
from pixel_ops.data_sources.calendar import CalendarEvent
from pixel_ops.data_sources.pc_stats import PCMetric, PCStatsSnapshot
from pixel_ops.events.base import EventCategory, WorkEvent
from pixel_ops.outputs.browser import BrowserOutputServer
from pixel_ops.plugins.pokemon.game.encounter_system import EncounterContext
from pixel_ops.plugins.pokemon.game.state_machine import GamePhase
from pixel_ops.plugins.pokemon.kraken import KrakenProjection, countdown_meeting
from pixel_ops.plugins.pokemon.pokemon import get_pokemon
from pixel_ops.plugins.pokemon.scenes.overworld_scene import OverworldScene


NOW = datetime(2026, 10, 30, 13, tzinfo=ZoneInfo('America/Sao_Paulo'))
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def scene():
    return OverworldScene(1920, 480, 'America/Sao_Paulo', lazy_download=False, scanlines=False)


def state(view):
    return json.loads(view.state_json)


def test_meeting_absolute_window_boundaries_and_deduplication():
    event = CalendarEvent('Standup', NOW, calendar_name='Sample calendar', uid='one')
    copy = CalendarEvent('Shared Standup', NOW, calendar_name='Personal', uid='one')
    assert countdown_meeting([event, copy], NOW - timedelta(minutes=5, microseconds=1)) is None
    assert countdown_meeting([event, copy], NOW - timedelta(minutes=5)) is event
    assert countdown_meeting([event], NOW + timedelta(seconds=59)) is event
    assert countdown_meeting([event], NOW + timedelta(minutes=1)) is None
    assert countdown_meeting([CalendarEvent('Holiday', NOW, all_day=True)], NOW) is None


def test_battle_interrupts_meeting_and_resumes_without_extending_it(scene):
    projection = KrakenProjection({})
    meeting = CalendarEvent('Standup', NOW, calendar_name='Sample calendar')
    values = {'calendar.today_updated': [meeting]}
    before = NOW - timedelta(minutes=2)
    assert state(projection.view(scene, values, before))['mode'] == 'meeting'
    scene.encounter = EncounterContext(get_pokemon(25), WorkEvent(EventCategory.PULL_REQUEST, 'PR', repo='owner/repo'))
    scene.state.set_phase(GamePhase.ASH_THROWS, before)
    original_phase_time = scene.state.phase_started_at
    original_frame = scene.frame
    view = projection.view(scene, values, NOW - timedelta(seconds=10))
    data = state(view)
    assert data['mode'] == 'battle'
    assert data['battle']['pokemon'] == scene.encounter.pokemon.name.upper()
    assert data['battle']['phase'] == scene.state.phase.value
    assert Image.open(BytesIO(view.image_png)).size == (384, 280)
    assert scene.state.phase_started_at == original_phase_time
    assert scene.frame == original_frame
    # The mirror cannot capture or advance the primary world.
    assert projection._battle_scene.state is scene.state
    scene.state.set_phase(GamePhase.RESUME_WALKING, NOW)
    resumed = state(projection.view(scene, values, NOW + timedelta(seconds=30)))
    assert resumed['mode'] == 'meeting'
    assert resumed['meeting']['ends_at'] == (NOW + timedelta(seconds=60)).isoformat()
    assert state(projection.view(scene, values, NOW + timedelta(seconds=60)))['mode'] == 'thermal'


def test_pr_finishing_after_meeting_window_returns_to_thermal(scene):
    projection = KrakenProjection({})
    values = {'calendar.today_updated': [CalendarEvent('Standup', NOW)]}
    scene.encounter = EncounterContext(get_pokemon(24), WorkEvent(EventCategory.PULL_REQUEST, 'PR'))
    scene.state.set_phase(GamePhase.CAUGHT, NOW)
    assert state(projection.view(scene, values, NOW + timedelta(seconds=61)))['mode'] == 'battle'
    scene.state.set_phase(GamePhase.RESUME_WALKING, NOW)
    assert state(projection.view(scene, values, NOW + timedelta(seconds=62)))['mode'] == 'thermal'


def test_non_pr_encounters_disabled_switches_and_cancelled_meetings(scene):
    projection = KrakenProjection({})
    scene.encounter = EncounterContext(get_pokemon(24), WorkEvent(EventCategory.MERGE, 'Merged'))
    scene.state.set_phase(GamePhase.POKEMON_APPEARS, NOW)
    assert state(projection.view(scene, {}, NOW))['mode'] == 'thermal'
    scene.encounter = EncounterContext(get_pokemon(24), WorkEvent(EventCategory.PULL_REQUEST, 'PR'))
    disabled = KrakenProjection({'pr_battles': False, 'meeting_countdown': False})
    values = {'calendar.today_updated': [CalendarEvent('Standup', NOW)]}
    assert state(disabled.view(scene, values, NOW))['mode'] == 'thermal'
    scene.state.set_phase(GamePhase.WALKING, NOW)
    assert state(projection.view(scene, values, NOW))['mode'] == 'meeting'
    assert state(projection.view(scene, {}, NOW))['mode'] == 'thermal'


def test_meeting_continues_over_midnight_without_reset(scene):
    projection = KrakenProjection({})
    starts = NOW.replace(hour=23, minute=59, second=30)
    meeting = CalendarEvent('Late call', starts, calendar_name='Kite')
    values = {'calendar.today_updated': [meeting]}
    assert state(projection.view(scene, values, starts))['mode'] == 'meeting'
    assert state(projection.view(scene, {}, starts + timedelta(seconds=40)))['meeting']['calendar'] == 'Kite'
    assert state(projection.view(scene, {}, starts + timedelta(seconds=60)))['mode'] == 'thermal'


def test_app_browser_extension_is_optional_and_uses_the_active_game():
    app = PixelOpsApp(SimpleNamespace(name='legacy'))
    assert app.browser_views() == {}
    view = BrowserView(b'{"mode":"thermal"}')
    app.engine = SimpleNamespace(browser_views=lambda: {'kraken': view})
    assert app.browser_views() == {'kraken': view}


def test_temperature_fallback_is_numeric_and_expires_with_its_observation(scene):
    projection = KrakenProjection({})
    values = {'system.metrics_updated': PCStatsSnapshot((PCMetric('gpu_temperature', 'GPU TEMP', '41C', numeric_value=41, unit='C'),), NOW)}
    assert state(projection.view(scene, values, NOW))['temperatures']['gpu'] == 41
    assert 'temperatures' not in state(projection.view(scene, values, NOW + timedelta(seconds=11)))


def test_loopback_server_serves_snapshots_and_rejects_other_origins():
    server = BrowserOutputServer({'kraken': ROOT / 'pixel_ops/web/kraken'}, port=0)
    server.start()
    base = f'http://127.0.0.1:{server.port}'
    try:
        server.publish({'kraken': BrowserView(b'{"mode":"battle","frame":1}', b'fixture-image')})
        assert json.load(urlopen(base + '/kraken/state'))['frame'] == 1
        assert urlopen(base + '/kraken/frame.png?frame=1').read() == b'fixture-image'
        assert b'canvas' in urlopen(base + '/kraken?kraken=1').read()
        assert 'script-src' in urlopen(base + '/kraken/').headers['Content-Security-Policy']
        for path, headers, status in [
            ('/kraken/state', {'Origin': 'https://example.com'}, 403),
            ('/kraken/state', {'Host': f'evil.example:{server.port}'}, 403),
            ('/kraken/state', {'Sec-Fetch-Site': 'cross-site'}, 403),
            ('/kraken/../../.env', {}, 404),
            ('/kraken/token.json', {}, 404),
        ]:
            with pytest.raises(HTTPError) as error:
                urlopen(Request(base + path, headers=headers))
            assert error.value.code == status
        with patch('pixel_ops.outputs.browser.time.monotonic', return_value=server._published_at + 6):
            assert json.load(urlopen(base + '/kraken/state')) == {'mode': 'thermal', 'available': False}
        server.publish({})
        assert json.load(urlopen(base + '/kraken/state'))['available'] is False
    finally:
        server.close()
