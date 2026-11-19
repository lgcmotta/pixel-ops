from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw

from pixel_ops.data_sources.ai_quota import AIQuotaSnapshot, AIQuotaWindow
from pixel_ops.plugins.pokemon.game.day_night import day_night_palette
from pixel_ops.render.account_hud import draw_quota
from pixel_ops.render.fonts import font_scale_for_canvas


NOW = datetime(2026, 10, 30, 10, 33, 26, tzinfo=ZoneInfo('America/Sao_Paulo'))


def account(provider='codex', **changes):
    data = dict(provider=provider, windows=(AIQuotaWindow('weekly', provider, 10080, 4, NOW + timedelta(hours=130, minutes=56)),),
                observed_at=NOW, status='ok', daily_tokens=(('2026-10-20', 40819557),))
    data.update(changes)
    return AIQuotaSnapshot(**data)


def texts(snapshots):
    image = Image.new('RGB', (448, 208))
    calls = []
    original = ImageDraw.ImageDraw.text

    def record(draw, xy, text, *args, **kwargs):
        bounds = draw.textbbox(xy, text, font=kwargs['font'])
        assert bounds[0] >= 0 and bounds[1] >= 0
        assert bounds[2] <= 448 and bounds[3] <= 208
        calls.append(text)
        return original(draw, xy, text, *args, **kwargs)

    with font_scale_for_canvas(1920, 480), patch.object(ImageDraw.ImageDraw, 'text', record):
        draw_quota(ImageDraw.Draw(image), snapshots, NOW, (0, 0, 448, 208), day_night_palette(0))
    return calls


def test_compact_panel_keeps_exact_account_totals_and_reset_time():
    rendered = texts(account())
    assert 'AI USAGE' in rendered
    assert 'codex - 7d' in rendered
    assert '96% remaining  130h 56m' in rendered
    assert '2026-10-20  40,819,557 acct tokens' in rendered
    assert 'Updated 10:33:26' in rendered


def test_two_providers_fit_without_merging_their_usage_or_staleness():
    # A future provider uses the same neutral observation; no Claude integration is invoked.
    second = account('claude', observed_at=NOW - timedelta(minutes=4), daily_tokens=())
    rendered = texts((account(), second))
    assert 'codex - 7d' in rendered and 'claude - 7d' in rendered
    assert '96% remaining  130h 56m' in rendered
    assert 'Quota unavailable / stale' in rendered
    assert rendered.count('2026-10-20  40,819,557 acct tokens') == 1
    assert 'Last update 10:29:26' in rendered


def test_reset_boundary_does_not_infer_new_allowance():
    snapshot = account(windows=(AIQuotaWindow('weekly', 'codex', 10080, 100, NOW),), daily_tokens=())
    rendered = texts(snapshot)
    assert 'Refreshing after reset' in rendered
    assert not any('remaining' in text or 'tokens' in text for text in rendered)
