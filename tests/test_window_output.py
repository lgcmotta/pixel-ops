import unittest
from unittest.mock import MagicMock, patch
from PIL import Image, ImageDraw
from pixel_ops.outputs.window import WindowOutput, select_monitor


class WindowOutputTests(unittest.TestCase):
    def test_tray_mode_hides_only_the_display_window_from_taskbar(self):
        pygame = MagicMock()
        pygame.display.get_wm_info.return_value = {'window': 1234}
        with patch.dict('sys.modules', {'pygame': pygame}), patch.dict('os.environ', {'PIXEL_OPS_TRAY': '1'}), patch('pixel_ops.outputs.window.hide_from_taskbar') as hide, patch('pixel_ops.outputs.window.enable_dpi_awareness'):
            output = WindowOutput(320, 240)
            output.start()
            hide.assert_called_once_with(1234)
            hide.reset_mock()
            WindowOutput(320, 240, preview=True).start()
            hide.assert_not_called()

    def test_camera_leaves_room_for_ash_to_walk_before_following(self):
        from types import SimpleNamespace
        from pixel_ops.plugins.pokemon.scenes.overworld_scene import OverworldScene
        scene = SimpleNamespace(display_layout={"game": {"camera_zoom": 3}},
                                current_map_area=SimpleNamespace(crop_box=(0, 0, 900, 300)),
                                map_box=(0, 0, 900, 300), _ash_render_x=300, _ash_render_y=140, frame=0)
        OverworldScene._zoom_world_view(scene, Image.new("RGB", (900, 300)))
        original = scene._camera_position
        scene._ash_render_x += 10
        scene.frame += 1
        OverworldScene._zoom_world_view(scene, Image.new("RGB", (900, 300)))
        self.assertEqual(scene._camera_position, original)
        scene._ash_render_x += 150
        scene.frame += 1
        OverworldScene._zoom_world_view(scene, Image.new("RGB", (900, 300)))
        self.assertGreater(scene._camera_position[0], original[0])
        self.assertLessEqual(scene._camera_position[0] - original[0], 2.5)

    def test_panoramic_camera_removes_native_map_gutters(self):
        from types import SimpleNamespace
        from pixel_ops.plugins.pokemon.scenes.overworld_scene import OverworldScene
        scene = SimpleNamespace(display_layout={"game": {"camera_zoom": 3}}, current_map_area=SimpleNamespace(crop_box=(0, 0, 300, 300)),
                                map_box=(0, 0, 900, 300), _ash_render_x=440, _ash_render_y=140)
        image = Image.new("RGB", (900, 300), "black")
        draw = ImageDraw.Draw(image)
        draw.rectangle((300, 0, 599, 299), fill="green")
        draw.rectangle((440, 140, 460, 160), fill="red")
        OverworldScene._zoom_world_view(scene, image)
        self.assertEqual(image.getpixel((0, 0)), (0, 128, 0))
        self.assertEqual(image.getpixel((899, 299)), (0, 128, 0))
        self.assertIn((255, 0, 0), image.getdata())

    def test_auto_selection_requires_unique_native_monitor(self):
        self.assertEqual(select_monitor([(3440, 1440), (1920, 480)], (1920, 480)), 1)
        for sizes in ([(3440, 1440)], [(1920, 480), (1920, 480)]):
            with self.assertRaises(RuntimeError):
                select_monitor(sizes, (1920, 480))

    def test_explicit_selection_validates_dimensions(self):
        self.assertEqual(select_monitor([(1920, 480)] * 2, (1920, 480), 1), 1)
        with self.assertRaises(RuntimeError):
            select_monitor([(3440, 1440)], (1920, 480), 0)

    def test_preview_uses_normal_reduced_window(self):
        pygame = MagicMock()
        output = WindowOutput(1920, 480, scale=1, borderless=True, preview=True)
        with patch.dict("sys.modules", {"pygame": pygame}), patch("pixel_ops.outputs.window.enable_dpi_awareness") as dpi:
            output.start()
        dpi.assert_called_once()
        pygame.display.set_mode.assert_called_once_with((1200, 300))
        output.stop()

    def test_borderless_missing_display_never_opens_primary_window(self):
        pygame = MagicMock()
        pygame.display.get_desktop_sizes.return_value = [(3440, 1440)]
        with patch.dict("sys.modules", {"pygame": pygame}):
            with self.assertRaises(RuntimeError):
                WindowOutput(1920, 480, scale=1, borderless=True).start()
        pygame.display.set_mode.assert_not_called()
