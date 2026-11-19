import io
import struct
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from PIL import Image

from pixel_ops.hardware.lian_li_led import set_border_color
from pixel_ops.main import runtime_display_configs, runtime_output
from pixel_ops.outputs.lian_li_usb import (
    LianLiUsbOutput,
    _command_packet,
    _encode_jpeg,
    _HEADER_CIPHER,
)


class ReplyingTransport:
    def __init__(self):
        self.replies = []
        self.writes = []
        self.closed = False
        self.buffer_levels = {}

    def write(self, packet):
        decoder = _HEADER_CIPHER.decryptor()
        header = decoder.update(packet[:504]) + decoder.finalize()
        opcode = header[0]
        self.writes.append((opcode, packet[512:]))
        self.replies.append(bytes((opcode, 0xC8)) + header[4:8] + b"\0\0" + bytes((self.buffer_levels.get(opcode, 0),)))

    def read(self):
        return self.replies.pop(0)

    def close(self):
        self.closed = True


class LianLiUsbTests(TestCase):
    def test_border_color_writes_three_rgb_packets_on_the_led_interface(self):
        with patch("pixel_ops.hardware.lian_li_led.LianLiWinUsb") as open_usb:
            transport = open_usb.return_value
            set_border_color("#CE00FF")
        open_usb.assert_called_once_with("", timeout_ms=500, led_ring=True)
        self.assertEqual(
            [call.args[0] for call in transport.write.call_args_list],
            [bytes((0x11, offset, 0, 0)) + bytes((206, 0, 255)) * 20 for offset in (0, 20, 40)],
        )
        transport.read.assert_not_called()
        transport.close.assert_called_once_with()

    def test_border_failure_leaves_the_lcd_running(self):
        transport = ReplyingTransport()
        output = LianLiUsbOutput.from_config({"border_color": "#CE00FF"})
        set_color = Mock(side_effect=RuntimeError("LED ring busy"))
        with (
            patch("pixel_ops.outputs.lian_li_usb.LianLiWinUsb", return_value=transport),
            patch("pixel_ops.outputs.lian_li_usb.set_border_color", set_color),
            self.assertLogs("pixel_ops.outputs.lian_li_usb", "WARNING"),
        ):
            output.start()
        output.send(Image.new("RGB", (1920, 480)))
        set_color.assert_called_once_with("#CE00FF")
        self.assertEqual(transport.writes[-1][0], 0x65)
        self.assertFalse(transport.closed)
        output.stop()

    def test_header_matches_documented_jpeg_vector(self):
        jpeg = b"\xff" * 123456
        packet = _command_packet(0x65, 42, jpeg)
        self.assertEqual(packet[:16].hex(), "6edf63cc8e6c3fe43f32428b39cce22c")
        self.assertEqual(packet[496:512].hex(), "27382732b83ef643000000000000a11a")
        self.assertEqual(packet[512:], jpeg)

    def test_wide_frame_is_encoded_in_panel_orientation(self):
        frame = Image.new("RGB", (1920, 480), "blue")
        frame.paste("red", (0, 0, 960, 480))
        with Image.open(io.BytesIO(_encode_jpeg(frame, 90))) as jpeg:
            self.assertEqual(jpeg.size, (480, 1920))
            self.assertGreater(jpeg.getpixel((240, 1680))[0], 240)
            self.assertGreater(jpeg.getpixel((240, 240))[2], 240)

    def test_start_send_and_close_handle_stale_replies_and_buffer_pressure(self):
        transport = ReplyingTransport()
        transport.replies.append(b"\x7b\xc8" + struct.pack("<I", 0) + b"\0\0\0")
        transport.buffer_levels.update({0x65: 4, 0x7A: 3})
        output = LianLiUsbOutput()
        with patch("pixel_ops.outputs.lian_li_usb.LianLiWinUsb", return_value=transport):
            output.start()
        frame = Image.new("RGB", (1920, 480))
        output.send(frame)
        output.send(frame)
        transport.buffer_levels[0x7A] = 2
        output.send(frame)
        output.stop()
        self.assertEqual([opcode for opcode, _ in transport.writes], [0x7B, 0x34, 0x66, 0x65, 0x7A, 0x7A, 0x65])
        self.assertTrue(transport.closed)

    def test_failed_start_releases_interface_for_retry(self):
        transport = ReplyingTransport()
        output = LianLiUsbOutput()
        with (
            patch("pixel_ops.outputs.lian_li_usb.LianLiWinUsb", return_value=transport),
            patch.object(transport, "read", side_effect=RuntimeError("disconnected")),
            self.assertRaisesRegex(RuntimeError, "disconnected"),
        ):
            output.start()
        self.assertTrue(transport.closed)
        with self.assertRaisesRegex(RuntimeError, "started"):
            output.send(Image.new("RGB", (1920, 480)))

    def test_configured_runtime_selects_lian_li_usb_display(self):
        args = SimpleNamespace(output=None)
        display = {
            "device": {
                "output": "window",
                "lian_li_usb": {"jpeg_quality": 80},
                "displays": [{"output": "lian_li_usb", "lian_li_usb": {"timeout_ms": 125}}],
            },
        }
        target, = runtime_display_configs(args, display)
        self.assertEqual(runtime_output(args, target), "lian_li_usb")
        self.assertEqual((target["width"], target["height"]), (1920, 480))
        self.assertEqual(target["device"]["lian_li_usb"], {"jpeg_quality": 80, "timeout_ms": 125})
