from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from PIL import Image

from pixel_ops.events.base import WorkEvent, EventCategory
from pixel_ops.events.github_events import GitHubEventSource
from pixel_ops.plugins.pokemon.game.encounter_system import EncounterSystem
from pixel_ops.plugins.pokemon.game.social_weather import WorldMoodState
from pixel_ops.plugins.pokemon.render.social_effects import draw_social_world_effects


NOW = datetime(2026, 10, 30, tzinfo=timezone.utc)


def refresh(source, items, now=NOW):
    source._request_json = lambda url: items
    source._refresh_sync(now, now - timedelta(seconds=60), False)
    events, source._pending_events = source._pending_events, []
    return events


def pr(number, created=None, **kwargs):
    return {'number': number, 'title': 'No raw body', 'user': {'login': 'someone'},
            'created_at': (created or NOW - timedelta(days=4)).isoformat(), **kwargs}


def test_restart_edit_reopen_and_draft_promotion_never_replay_an_existing_pr():
    with TemporaryDirectory() as directory:
        kwargs = dict(token='test', repos=['owner/repo'], cache_path=Path(directory) / 'prs.json')
        source = GitHubEventSource(**kwargs)
        assert refresh(source, [pr(1)]) == []
        new = pr(2, NOW + timedelta(seconds=30), draft=True)
        events = refresh(source, [pr(1), new], NOW + timedelta(seconds=60))
        assert [event.external_id for event in events] == ['owner/repo#2']
        assert events[0].category == EventCategory.PULL_REQUEST
        assert events[0].occurred_at == NOW + timedelta(seconds=30)
        source = GitHubEventSource(**kwargs)
        assert refresh(source, [pr(1, updated_at=(NOW + timedelta(seconds=120)).isoformat()),
                                {**new, 'draft': False}], NOW + timedelta(seconds=120)) == []
        assert refresh(source, [], NOW + timedelta(seconds=180)) == []
        assert refresh(source, [new], NOW + timedelta(seconds=240)) == []


def test_failure_does_not_establish_a_baseline_and_missing_creation_is_not_new():
    source = GitHubEventSource(token='test', repos=['owner/repo'])
    source._request_json = MagicMock(side_effect=OSError('offline'))
    source._refresh_sync(NOW, NOW, False)
    assert source._repository_baselines == {}
    assert refresh(source, [pr(1)], NOW + timedelta(seconds=60)) == []
    assert refresh(source, [dict(number=2, title='Unknown creation')], NOW + timedelta(seconds=120)) == []
    # Rediscovering historical items missed by an earlier page isn't an arrival.
    assert refresh(source, [pr(3)], NOW + timedelta(seconds=180)) == []


def test_long_offline_history_does_not_generate_a_capture_backlog():
    source = GitHubEventSource(token='test', repos=['owner/repo'])
    assert refresh(source, []) == []
    assert refresh(source, [pr(1, NOW + timedelta(hours=1))], NOW + timedelta(days=2)) == []
    assert len(source.open_pull_requests()) == 1


def test_a_pr_first_seen_closed_is_not_a_new_arrival_when_reopened():
    source = GitHubEventSource(token='test', repos=['owner/repo'])
    assert refresh(source, []) == []
    item = pr(1, NOW + timedelta(seconds=5), closed_at=(NOW + timedelta(seconds=10)).isoformat())
    source._request_json = lambda url: [item]
    source._fetch_closed_pull_request_updates(NOW + timedelta(seconds=20), NOW)
    assert refresh(source, [item], NOW + timedelta(seconds=30)) == []


def test_capture_filter_keeps_other_facts_in_mood_and_history():
    observed = []
    encounters = EncounterSystem(MagicMock(), on_event=observed.append, capture_categories=['pull_request'])
    merged = WorkEvent(category=EventCategory.MERGE, title='Merge', source='github', external_id='owner/repo#1:merged')
    opened = WorkEvent(category=EventCategory.PULL_REQUEST, title='New', source='github', external_id='owner/repo#2')
    encounters.enqueue(merged)
    encounters.enqueue(opened)
    assert list(encounters.queue) == [opened]
    assert list(encounters.recent_events) == [merged, opened]
    assert observed == [merged, opened]


def test_disabling_particles_removes_sparks_but_preserves_mood_tint():
    mood = WorldMoodState('electric_city', 'high', 1.4, ('electric',), 'busy', 'excited', intensity=.85, particles=('sparks', 'crowd'))
    image = Image.new('RGB', (320, 100), (0, 0, 0))
    with patch('pixel_ops.plugins.pokemon.render.social_effects._draw_sparks') as sparks:
        draw_social_world_effects(image, (0, 0, 320, 100), mood, 1, particles=False)
        sparks.assert_not_called()
        assert image.getpixel((100, 50)) != (0, 0, 0)
        draw_social_world_effects(image, (0, 0, 320, 100), mood, 1)
        sparks.assert_called_once()
