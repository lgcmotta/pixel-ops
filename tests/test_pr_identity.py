import json
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from PIL import ImageDraw
import pytest

from pixel_ops.events.base import EventCategory, WorkEvent
from pixel_ops.plugins.pokemon.game.day_night import day_night_palette
from pixel_ops.plugins.pokemon.game.encounter_system import EncounterContext
from pixel_ops.plugins.pokemon.game.state_machine import GamePhase
from pixel_ops.plugins.pokemon.kraken import KrakenProjection
from pixel_ops.plugins.pokemon.pokemon import get_pokemon
from pixel_ops.plugins.pokemon.scenes.overworld_scene import OverworldScene


NOW = datetime(2026, 10, 30, 12, tzinfo=ZoneInfo('America/Sao_Paulo'))


@pytest.mark.parametrize('event', [
    WorkEvent(EventCategory.PULL_REQUEST, 'sample-project #42 opened', source='github', repo='sample-project', external_id='demo/sample-project#42', metadata={'repository': 'demo/sample-project'}),
    WorkEvent(EventCategory.PULL_REQUEST, 'Demo PR', source='show_off', repo='sample-project', external_id='show-off:run:1:pr:1', metadata={'repository': 'demo/sample-project', 'number': '42'}),
    WorkEvent(EventCategory.PULL_REQUEST, 'Legacy PR', repo='sample-project', external_id='demo/sample-project#42'),
])
def test_pr_identity_is_preserved_for_real_demo_and_legacy_events(event):
    encounter = EncounterContext(get_pokemon(24), event)
    assert encounter.pr_repository == 'demo/sample-project'
    assert encounter.pr_number == 42
    assert encounter.pr_reference == 'demo/sample-project#42'
    scene = OverworldScene(1920, 480, 'America/Sao_Paulo', lazy_download=False)
    scene.encounter = encounter
    scene.state.set_phase(GamePhase.POKEMON_APPEARS, NOW)
    projection = KrakenProjection({})
    data = json.loads(projection.view(scene, {}, NOW).state_json)['battle']
    assert data['repository'] == encounter.pr_repository
    assert data['pr_number'] == 42
    assert data['number'] == 25  # Independent Pokédex identity stays compatible.
    assert data['reference'] == encounter.pr_reference


def test_missing_pr_number_is_not_substituted_with_a_pokedex_number():
    encounter = EncounterContext(get_pokemon(24), WorkEvent(EventCategory.PULL_REQUEST, 'New PR', repo='demo/pixel-ops'))
    assert encounter.pr_number is None
    assert encounter.pr_reference == 'demo/pixel-ops'


def test_widescreen_background_keeps_reference_visible_and_does_not_cache_old_identity():
    scene = OverworldScene(1920, 480, 'America/Sao_Paulo', lazy_download=False,
                          display_layout={'game': {'x': 336, 'y': 76, 'width': 1104, 'height': 324}})
    texts = []
    original = ImageDraw.ImageDraw.text

    def record(draw, xy, text, *args, **kwargs):
        texts.append(text)
        return original(draw, xy, text, *args, **kwargs)

    with patch.object(ImageDraw.ImageDraw, 'text', record):
        for number in (42, 43):
            scene.encounter = EncounterContext(get_pokemon(24), WorkEvent(EventCategory.PULL_REQUEST, 'PR', detail='private body',
                metadata={'repository': 'demo/sample-project', 'number': str(number)}))
            for phase in (GamePhase.ENCOUNTER_START, GamePhase.ASH_THROWS, GamePhase.CAUGHT):
                scene.state.set_phase(phase, NOW)
                scene._battle_background_for_current_mood(day_night_palette(0))
                assert texts[-2:] == ['PR ENCOUNTER', f'demo/sample-project#{number} PIKACHU']
    assert not any('private body' in text for text in texts)
