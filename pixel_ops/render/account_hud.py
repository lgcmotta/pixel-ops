"""Compact quota and hardware instruments; all inputs are neutral snapshots."""
from datetime import datetime
from math import ceil

from PIL import Image, ImageColor, ImageDraw

from pixel_ops.data_sources.calendar import CalendarEvent
from pixel_ops.render.fonts import font
from pixel_ops.render.renderer import PixelRenderer


def _panel_ink(pal):
    color = ImageColor.getrgb(pal.panel) if isinstance(pal.panel, str) else pal.panel
    return (0, 0, 0) if sum(color[:3]) / 3 > 150 else pal.ink


def _panel(draw, box, pal, title, painter, title_size=15):
    x, y, right, bottom = box
    tile = Image.new("RGB", (max(1, right - x), max(1, bottom - y)), pal.panel)
    canvas = ImageDraw.Draw(tile)
    PixelRenderer.draw_panel(canvas, (0, 0, tile.width - 1, tile.height - 1), pal.panel, pal.panel_shadow, pal.ink)
    canvas.text((16, 10), title, font=font(title_size), fill=_panel_ink(pal))
    painter(canvas, tile.width, tile.height)
    draw._image.paste(tile, (x, y))


def _text(draw, xy, text, size, color, width):
    face = font(size)
    while text and draw.textlength(text, font=face) > width:
        text = text[:-1]
    draw.text(xy, text, font=face, fill=color)


def draw_hardware(draw, snapshot, now, box, pal):
    ink = _panel_ink(pal)
    def paint(canvas, width, height):
        fresh = snapshot and 0 <= (now - snapshot.observed_at).total_seconds() <= 10
        metrics = {metric.key: metric for metric in snapshot.metrics} if fresh else {}
        row_height = max(56, min(85, (height - 48) // 4))
        for index, (key, label) in enumerate((("cpu", "CPU LOAD"), ("gpu_usage", "GPU LOAD"), ("ram", "RAM"), ("vram", "VRAM"))):
            y = 46 + index * row_height
            if y + 48 > height:
                break
            metric = metrics.get(key)
            _text(canvas, (16, y), label, 12, ink, width - 32)
            value = metric.value if metric and metric.status != "unknown" else "Unavailable"
            _text(canvas, (16, y + 20), value, 14, ink, width - 32)
            canvas.rectangle((16, y + 44, width - 16, y + 50), fill=pal.panel_shadow)
            if metric and metric.numeric_value is not None and metric.total and metric.status != "unknown":
                fraction = max(0, min(1, metric.numeric_value / metric.total))
                if fraction:
                    canvas.rectangle((16, y + 44, 16 + int((width - 32) * fraction), y + 50), fill=pal.blue)
    _panel(draw, box, pal, "SYSTEM VITALS", paint)


def draw_quota(draw, snapshot, now, box, pal):
    ink = _panel_ink(pal)
    def paint(canvas, width, height):
        accounts = list(snapshot) if isinstance(snapshot, (tuple, list)) else [snapshot] if snapshot else []
        if not accounts:
            _text(canvas, (16, 48), "Connect an account in Config Studio", 14, ink, width - 32)
            return
        cards = [(account, window) for account in accounts for window in (account.windows or (None,))]
        capacity = max(1, (height - 42) // 80)
        pages = max(1, (len(cards) + capacity - 1) // capacity)
        page = int(now.timestamp() // 8) % pages
        _text(canvas, (width - 70, 13), f"{page + 1}/{pages}", 12, ink, 60)
        for index, (account, window) in enumerate(cards[page * capacity:(page + 1) * capacity]):
            y = 42 + index * 80
            label = account.provider
            if window:
                if window.label.casefold() != account.provider.casefold():
                    label += f" / {window.label}"
                minutes = window.window_minutes
                duration = f"{minutes // 1440}d" if minutes % 1440 == 0 else f"{minutes // 60}h" if minutes % 60 == 0 else f"{minutes}m"
                label += f" - {duration}"
            _text(canvas, (16, y), label, 15, ink, width - 32)
            fresh = account.fresh(now)
            remaining = window.remaining(now) if fresh and window else None
            if not fresh:
                value = "Connect in Config Studio" if account.status == "disconnected" else "Quota unavailable / stale"
            elif window is None:
                value = "Limits not reported"
            elif remaining is None:
                value = "Refreshing after reset"
            else:
                value = f"{remaining:.0f}% remaining"
                if window.reset_at:
                    seconds = max(0, int((window.reset_at - now).total_seconds()))
                    value += f"  {seconds // 3600}h {(seconds % 3600) // 60:02d}m"
            _text(canvas, (16, y + 22), value, 16, ink, width - 32)
            if account.daily_tokens:
                day, count = max(account.daily_tokens)
                _text(canvas, (16, y + 46), f"{day}  {count:,} acct tokens", 11, ink, width - 32)
            if account.observed_at:
                updated = account.observed_at.astimezone(now.tzinfo).strftime("%H:%M:%S")
                _text(canvas, (16, y + 64), f"{'Updated' if fresh else 'Last update'} {updated}", 10, ink, width - 32)
    _panel(draw, box, pal, "AI USAGE", paint, title_size=17)


def draw_pr_activity(draw, pull_requests, now, box, pal):
    ink = _panel_ink(pal)
    def paint(canvas, width, height):
        if not pull_requests:
            _text(canvas, (16, 52), "No PR activity available", 16, ink, width - 32)
            return
        capacity = max(1, (height - 48) // 60)
        pages = max(1, (len(pull_requests) + capacity - 1) // capacity)
        page = int(now.timestamp() // 8) % pages
        canvas.text((width - 70, 13), f"{page + 1}/{pages}", font=font(12), fill=ink)
        for i, pr in enumerate(pull_requests[page * capacity:(page + 1) * capacity]):
            state = "draft" if pr.draft else pr.review_state
            y = 45 + 60 * i
            _text(canvas, (16, y), pr.repository or pr.repo, 16, ink, width - 32)
            _text(canvas, (16, y + 25), f"#{pr.number} / {state}", 18, ink, width - 32)
    _panel(draw, box, pal, "PR ACTIVITY", paint, title_size=17)


def upcoming_strip_meetings(
    event: CalendarEvent | None, today_events: list[CalendarEvent], now: datetime,
) -> tuple[CalendarEvent | None, tuple[CalendarEvent, ...]]:
    """Keep the next timed meeting pinned; rotate only later meetings today.

    Observations can lag the clock briefly. Drop meetings as they start rather
    than leaving an old next meeting pinned until the next calendar refresh.
    """
    candidates = {}
    for meeting in [event, *today_events]:
        if meeting is None or meeting.all_day or meeting.starts_at < now:
            continue
        local_start = meeting.starts_at.astimezone(now.tzinfo)
        if meeting is not event and local_start.date() != now.date():
            continue
        key = (meeting.starts_at, meeting.title.strip().casefold())
        candidates.setdefault(key, meeting)
    ordered = sorted(candidates.values(), key=lambda meeting: (meeting.starts_at, meeting.title.casefold()))
    pinned = ordered[0] if ordered else None
    later = tuple(meeting for meeting in ordered[1:] if meeting.starts_at.astimezone(now.tzinfo).date() == now.date())
    return pinned, later


def _fit_strip_text(draw, text, face, width):
    if draw.textlength(text, font=face) > width:
        suffix = "..."
        while text and draw.textlength(text + suffix, font=face) > width:
            text = text[:-1]
        text = text + suffix if draw.textlength(suffix, font=face) <= width else ""
    return text


def _strip_text(draw, xy, text, size, color, width):
    """Fit one line inside its column without hiding truncation."""
    face = font(size)
    text = _fit_strip_text(draw, text, face, width)
    draw.text(xy, text, font=face, fill=color, anchor="lt")


def draw_status_strip(draw, event, weather, now, box, pal, today_events=None):
    ink = _panel_ink(pal)
    x, y, right, bottom = box
    tile = Image.new("RGB", (max(1, right - x), max(1, bottom - y)), pal.panel)
    canvas = ImageDraw.Draw(tile)
    PixelRenderer.draw_panel(canvas, (0, 0, tile.width - 1, tile.height - 1), pal.panel, pal.panel_shadow, pal.ink)
    clock = now.strftime("%a %d %b   %H:%M")
    clock_face = font(17)
    clock_width = min(ceil(canvas.textlength(clock, font=clock_face)), max(1, tile.width // 3))
    bounds = clock_face.getbbox(clock)
    _strip_text(canvas, (16, max(6, (tile.height - (bounds[3] - bounds[1])) // 2)), clock, 17, ink, clock_width)

    start = 16 + clock_width + 28
    end = tile.width - 16
    weather_width = min(280, tile.width // 6) if weather and tile.width >= 1100 else 0
    if weather_width:
        end -= weather_width + 24
        _strip_text(canvas, (end + 24, 7), weather.city, 10, ink, weather_width)
        _strip_text(canvas, (end + 24, 25), f"{weather.temperature_c:.0f} C / {weather.primary_effect}", 14, ink, weather_width)

    pinned, later = upcoming_strip_meetings(event, today_events or [], now)
    show_carousel = end - start >= 750
    column_width = max(1, (end - start - 28) // 2 if show_carousel else end - start)

    meeting_face = font(15)
    bounds = meeting_face.getbbox("Next: Meeting / 00:00")
    meeting_y = max(6, (tile.height - (bounds[3] - bounds[1])) // 2)

    def meeting_column(left, label, meeting, empty):
        prefix = f"{label}: "
        suffix = ""
        title = empty
        if meeting:
            local_start = meeting.starts_at.astimezone(now.tzinfo)
            time_label = local_start.strftime("%H:%M" if local_start.date() == now.date() else "%a %d %b %H:%M")
            suffix = f" / {time_label}"
            title = meeting.title
        title_width = column_width - canvas.textlength(prefix + suffix, font=meeting_face)
        title = _fit_strip_text(canvas, title, meeting_face, title_width)
        _strip_text(canvas, (left, meeting_y), prefix + title + suffix, 15, ink, column_width)

    meeting_column(start, "Next", pinned, "No upcoming meeting")
    if show_carousel:
        left = start + column_width + 28
        index = int(now.timestamp() // 10) % len(later) if later else 0
        meeting_column(left, "Later Today", later[index] if later else None, "No more meetings today")
    draw._image.paste(tile, (x, y))
