from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw

from pixel_ops.data_sources.calendar import CalendarEvent
from pixel_ops.render.account_hud import draw_status_strip, upcoming_strip_meetings
from pixel_ops.render.fonts import font_scale_for_canvas


class StatusStripTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 30, 9, tzinfo=ZoneInfo("America/Sao_Paulo"))
        self.next = CalendarEvent("Team standup", self.now + timedelta(hours=1))
        self.later = CalendarEvent("Product review", self.now + timedelta(hours=2))
        self.last = CalendarEvent("Planning", self.now + timedelta(hours=3))
        self.palette = SimpleNamespace(panel=(216, 224, 237), panel_shadow="#8e9baf", ink="#18212e", blue="#348ea8")

    def test_pins_earliest_meeting_and_deduplicates_shared_copies(self):
        duplicate = CalendarEvent(" team STANDUP ", self.next.starts_at.astimezone(timezone.utc))
        pinned, later = upcoming_strip_meetings(self.next, [self.last, duplicate, self.next, self.later], self.now)
        self.assertIs(pinned, self.next)
        self.assertEqual(later, (self.later, self.last))

    def test_discards_started_all_day_and_other_day_meetings(self):
        started = CalendarEvent("Already started", self.now - timedelta(minutes=10), ends_at=self.now + timedelta(minutes=20))
        all_day = CalendarEvent("All day", self.now + timedelta(minutes=1), all_day=True)
        tomorrow = CalendarEvent("Tomorrow", self.now + timedelta(days=1))
        pinned, later = upcoming_strip_meetings(started, [started, all_day, tomorrow, self.next, self.later], self.now)
        self.assertIs(pinned, self.next)
        self.assertEqual(later, (self.later,))

    def test_pin_advances_even_before_calendar_observation_refreshes(self):
        pinned, later = upcoming_strip_meetings(self.next, [self.next, self.later, self.last], self.next.starts_at + timedelta(seconds=1))
        self.assertIs(pinned, self.later)
        self.assertEqual(later, (self.last,))

    def test_local_day_boundary_and_tomorrow_pin(self):
        now = self.now.replace(hour=22)
        tonight_utc = CalendarEvent("Late call", (now + timedelta(hours=1)).astimezone(timezone.utc))
        tomorrow = CalendarEvent("Morning call", now + timedelta(hours=10))
        pinned, later = upcoming_strip_meetings(tomorrow, [tonight_utc, tomorrow], now)
        self.assertIs(pinned, tonight_utc)
        self.assertEqual(later, ())
        pinned, later = upcoming_strip_meetings(tomorrow, [], now)
        self.assertIs(pinned, tomorrow)
        self.assertEqual(later, ())

    def test_empty_single_and_simultaneous_meetings(self):
        self.assertEqual(upcoming_strip_meetings(None, [], self.now), (None, ()))
        self.assertEqual(upcoming_strip_meetings(self.next, [self.next], self.now), (self.next, ()))
        conflict = CalendarEvent("Other team", self.next.starts_at)
        pinned, later = upcoming_strip_meetings(self.next, [conflict], self.now)
        self.assertEqual({pinned, *later}, {self.next, conflict})

    def render_calls(self, now, events, weather=None):
        image = Image.new("RGB", (1920, 80), "magenta")
        calls = []
        original = ImageDraw.ImageDraw.text

        def record(draw, xy, text, *args, **kwargs):
            calls.append((xy, text, draw.textbbox(xy, text, font=kwargs["font"], anchor=kwargs["anchor"])))
            if weather is None:
                self.assertEqual(kwargs["fill"], (0, 0, 0))
            return original(draw, xy, text, *args, **kwargs)

        with font_scale_for_canvas(1920, 480), patch.object(ImageDraw.ImageDraw, "text", record):
            draw_status_strip(ImageDraw.Draw(image), self.next, weather, now, (16, 12, 1904, 60), self.palette, events)
        self.assertEqual(image.getpixel((16, 11)), (255, 0, 255))
        self.assertEqual(image.getpixel((16, 60)), (255, 0, 255))
        for _, _, bounds in calls:
            self.assertGreaterEqual(bounds[0], 0)
            self.assertGreaterEqual(bounds[1], 0)
            self.assertLessEqual(bounds[2], 1888)
            self.assertLessEqual(bounds[3], 48)
        return calls

    def test_carousel_rotates_after_ten_seconds_while_next_stays_beside_clock(self):
        # Anchor at an exact carousel boundary, then move to the next page.
        now = self.now.replace(second=0)
        first = self.render_calls(now, [self.next, self.later, self.last])
        second = self.render_calls(now + timedelta(seconds=10), [self.next, self.later, self.last])
        for calls in (first, second):
            titles = {text: xy for xy, text, _ in calls}
            next_label = "Next: Team standup / 10:00"
            self.assertIn(next_label, titles)
            self.assertLess(titles[next_label][0], 400)
            self.assertEqual(sum(self.next.title in text for _, text, _ in calls), 1)
            later_label = next(text for text in titles if text.startswith("Later Today: "))
            self.assertEqual(titles[next_label][1], titles[later_label][1])
            self.assertNotIn("|", titles)
        first_later = [text for _, text, _ in first if text.startswith("Later Today: ")]
        second_later = [text for _, text, _ in second if text.startswith("Later Today: ")]
        self.assertNotEqual(first_later, second_later)

    def test_long_titles_fit_with_weather_and_empty_carousel_is_explicit(self):
        long = CalendarEvent("A very long meeting title " * 8, self.later.starts_at)
        weather = SimpleNamespace(city="Sao Paulo", temperature_c=26, primary_effect="sunny")
        calls = self.render_calls(self.now, [self.next, long], weather)
        self.assertTrue(any("... / 11:00" in text for _, text, _ in calls))
        self.assertTrue(any(text == "Sao Paulo" for _, text, _ in calls))
        calls = self.render_calls(self.now, [self.next])
        self.assertTrue(any(text == "Later Today: No more meetings today" for _, text, _ in calls))


if __name__ == "__main__":
    unittest.main()
