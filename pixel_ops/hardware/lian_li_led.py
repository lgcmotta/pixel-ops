"""Solid border lighting for the Lian Li US88v1 LED controller."""

import re

from pixel_ops.hardware.lian_li_winusb import LianLiWinUsb


def set_border_color(color: str) -> None:
    if not re.fullmatch(r"#?[0-9a-fA-F]{6}", color):
        raise ValueError("Lian Li border color must be a six-digit RGB hex value")
    pixels = bytes.fromhex(color.lstrip("#")) * 20
    transport = LianLiWinUsb("", timeout_ms=500, led_ring=True)
    try:
        # SetLeds carries 20 RGB LEDs per packet. The controller does not reply.
        for offset in (0, 20, 40):
            transport.write(bytes((0x11, offset, 0, 0)) + pixels)
    finally:
        transport.close()
