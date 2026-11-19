"""Frame output for the 8.8-inch Lian Li Universal Screen (US88v1)."""

from __future__ import annotations

import io
import logging
import struct
import time

from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
from cryptography.hazmat.primitives.ciphers import Cipher, modes
from PIL import Image

from pixel_ops.hardware.lian_li_led import set_border_color
from pixel_ops.hardware.lian_li_winusb import LianLiWinUsb
from pixel_ops.outputs.base import DisplayOutput


LANDSCAPE_SIZE = (1920, 480)
PANEL_SIZE = (480, 1920)
_MAX_IMAGE_BYTES = 512_000
_STOP_CLOCK = 0x34
_PUSH_JPEG = 0x65
_PUSH_PNG = 0x66
_QUERY_BUFFER = 0x7A
_STOP_PLAYBACK = 0x7B
# Fixed DES key and IV required by the panel's wire protocol.
_LCD_KEY = b"slv3tuzx"
# Repeating the single DES key makes EDE equivalent to DES.
_HEADER_CIPHER = Cipher(TripleDES(_LCD_KEY * 3), modes.CBC(_LCD_KEY))
_LOG = logging.getLogger(__name__)


def _command_packet(opcode: int, stamp: int, payload: bytes) -> bytes:
    header = bytearray(500)
    struct.pack_into("<B x 2s I", header, 0, opcode, b"\x1a\x6d", stamp)
    if payload:
        struct.pack_into(">I", header, 8, len(payload))
    encoder = _HEADER_CIPHER.encryptor()
    encrypted = encoder.update(header + b"\x04" * 4) + encoder.finalize()
    return encrypted + b"\x00" * 6 + b"\xa1\x1a" + payload


def _encode_jpeg(frame: Image.Image, quality: int) -> bytes:
    if frame.size != LANDSCAPE_SIZE:
        frame = frame.resize(LANDSCAPE_SIZE, Image.Resampling.NEAREST)
    portrait = frame.transpose(Image.Transpose.ROTATE_90).convert("RGB")
    for candidate in range(quality, 0, -5):
        buffer = io.BytesIO()
        portrait.save(buffer, "JPEG", quality=candidate, subsampling=2)
        if buffer.tell() <= _MAX_IMAGE_BYTES:
            return buffer.getvalue()
    raise RuntimeError("Could not encode a Lian Li USB frame within the panel's 512 KB limit")


class LianLiUsbOutput(DisplayOutput):
    def __init__(self, *, serial_number: str = "", timeout_ms: int = 2000, jpeg_quality: int = 90, border_color: str = ""):
        self.serial_number = serial_number
        self.timeout_ms = max(1, timeout_ms)
        self.jpeg_quality = min(95, max(1, jpeg_quality))
        self.border_color = border_color
        self._transport: LianLiWinUsb | None = None
        self._stamp = time.monotonic_ns() // 1_000_000 & 0xFFFFFFFF
        self._buffered_frames = 0

    @classmethod
    def from_config(cls, config: dict) -> LianLiUsbOutput:
        return cls(
            serial_number=str(config.get("serial_number") or "").strip(),
            timeout_ms=int(config.get("timeout_ms", 2000)),
            jpeg_quality=int(config.get("jpeg_quality", 90)),
            border_color=str(config.get("border_color") or "").strip(),
        )

    def start(self) -> None:
        if self._transport is not None:
            return
        self._transport = LianLiWinUsb(self.serial_number, self.timeout_ms)
        self._buffered_frames = 0
        try:
            self._exchange(_STOP_PLAYBACK)
            self._exchange(_STOP_CLOCK)
            time.sleep(0.25)  # The panel can ignore frames while its clock thread exits.
            overlay = io.BytesIO()
            Image.new("RGBA", PANEL_SIZE).save(overlay, "PNG")
            self._exchange(_PUSH_PNG, overlay.getvalue())
        except Exception:
            self.stop()
            raise
        if self.border_color:
            try:
                set_border_color(self.border_color)
            except (OSError, RuntimeError, ValueError) as error:
                _LOG.warning("Could not set the Lian Li border color: %s", error)

    def send(self, frame: Image.Image) -> None:
        if self._buffered_frames >= 3:
            self._buffered_frames = self._exchange(_QUERY_BUFFER)
            if self._buffered_frames > 2:
                return
        self._buffered_frames = self._exchange(_PUSH_JPEG, _encode_jpeg(frame, self.jpeg_quality))

    def _exchange(self, opcode: int, payload: bytes = b"") -> int:
        if self._transport is None:
            raise RuntimeError("Lian Li USB output must be started before sending a frame")
        self._stamp = (self._stamp + 1) & 0xFFFFFFFF
        expected = bytes((opcode, 0xC8)) + struct.pack("<I", self._stamp)
        self._transport.write(_command_packet(opcode, self._stamp, payload))
        # An earlier client or a failed transfer can leave replies on the IN pipe.
        for _ in range(8):
            reply = self._transport.read()
            if len(reply) >= 9 and reply.startswith(expected):
                return reply[8]
        raise RuntimeError(f"Lian Li USB did not acknowledge command 0x{opcode:02x}")

    def stop(self) -> None:
        if self._transport is not None:
            self._transport.close()
            self._transport = None
