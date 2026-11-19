from __future__ import annotations

import unittest

from PIL import Image, ImageChops, ImageDraw

from pixel_ops.plugins.pokemon.render.text_box import draw_text_box, text_box_visible_lines, _load_text_box_frame
from pixel_ops.render.fonts import font, font_scale_for_canvas


class TextBoxTests(unittest.TestCase):
    def test_widescreen_dialogue_ink_stays_in_the_interior(self):
        from pixel_ops.plugins.pokemon.game.day_night import day_night_palette
        with font_scale_for_canvas(1920, 480):
            image = Image.new("RGB", (1104, 56))
            background = _load_text_box_frame(image.size)
            draw_text_box(image, (0, 0, 1104, 56), "The route feels steady.", day_night_palette(12), 11)
            ink = ImageChops.difference(image, background).getbbox()
            self.assertGreaterEqual(ink[0], 22)
            self.assertGreaterEqual(ink[1], 12)
            self.assertLessEqual(ink[3], 44)
            self.assertAlmostEqual((ink[1] + ink[3]) / 2, 28, delta=3)
            # The trim has a constant width regardless of aspect ratio.
            narrow = _load_text_box_frame((320, 56))
            self.assertEqual(background.crop((0, 0, 15, 56)).tobytes(), narrow.crop((0, 0, 15, 56)).tobytes())

    def test_visible_lines_follow_configured_box_height(self):
        self.assertEqual(text_box_visible_lines((0, 0, 320, 92), ""), 3)
        self.assertEqual(text_box_visible_lines((0, 0, 480, 128), ""), 5)
        self.assertEqual(text_box_visible_lines((0, 0, 320, 48), ""), 1)

    def test_visible_lines_respect_custom_text_origin(self):
        self.assertEqual(text_box_visible_lines((0, 100, 320, 200), "", text_y=120), 3)
        self.assertEqual(text_box_visible_lines((0, 100, 320, 200), "", text_y=106), 4)

    def test_fonts_scale_for_large_canvas_context(self):
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        normal_width = draw.textbbox((0, 0), "Timezone", font=font(10))[2]

        with font_scale_for_canvas(1920, 462):
            large_width = draw.textbbox((0, 0), "Timezone", font=font(10))[2]

        self.assertGreater(large_width, normal_width)


if __name__ == "__main__":
    unittest.main()
