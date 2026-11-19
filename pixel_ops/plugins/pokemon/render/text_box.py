from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from pixel_ops.render.fonts import font, scaled_px
from pixel_ops.render.renderer import PixelRenderer

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets/sprites/ash"
MENU_SHEET = ASSET_DIR / "Game Boy Advance - Pokemon FireRed _ LeafGreen - Battle Effects - HP Bars & In-battle Menu.png"
TEXT_BOX_TEXT_TOP_PADDING = 14
TEXT_BOX_LINE_HEIGHT = 18
TEXT_BOX_BOTTOM_PADDING = 18
TEXT_BOX_CURSOR_HEIGHT = 14

_TEXT_BOX_FRAME: Image.Image | None = None


def _load_text_box_frame(size: tuple[int, int]) -> Image.Image | None:
    global _TEXT_BOX_FRAME
    if _TEXT_BOX_FRAME is None:
        if not MENU_SHEET.exists():
            return None
        with Image.open(MENU_SHEET) as sheet:
            # Blank battle message box from the FireRed/LeafGreen interface sheet.
            _TEXT_BOX_FRAME = sheet.convert("RGB").crop((297, 56, 535, 107))
    # Preserve the corners and trim. Stretching the complete 238px asset across
    # a panoramic box also stretches its left border underneath the dialogue.
    source = _TEXT_BOX_FRAME
    edge_x, edge_y = 12, 8
    target_x = min(scaled_px(edge_x), size[0] // 3)
    target_y = min(scaled_px(edge_y), size[1] // 3)
    src_x, src_y = (0, edge_x, source.width - edge_x, source.width), (0, edge_y, source.height - edge_y, source.height)
    dst_x, dst_y = (0, target_x, size[0] - target_x, size[0]), (0, target_y, size[1] - target_y, size[1])
    result = Image.new("RGB", size)
    for row in range(3):
        for col in range(3):
            tile = source.crop((src_x[col], src_y[row], src_x[col + 1], src_y[row + 1]))
            tile = tile.resize((dst_x[col + 1] - dst_x[col], dst_y[row + 1] - dst_y[row]), Image.Resampling.NEAREST)
            result.paste(tile, (dst_x[col], dst_y[row]))
    return result


def text_box_layout(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str):
    """Shared wrapping/origin for drawing and encounter scroll timing."""
    x0, y0, x1, y1 = box
    left = x0 + scaled_px(18)
    top = y0 + scaled_px(10)
    bottom = y1 - scaled_px(10)
    text_font = font(14)
    bbox = draw.textbbox((0, 0), "Ag", font=text_font)
    glyph_height = bbox[3] - bbox[1]
    max_lines = max(1, 1 + (bottom - top - glyph_height) // text_box_line_height())
    lines = wrap_text_lines(draw, text, text_font, max(1, x1 - left - scaled_px(34)))
    count = min(max_lines, len(lines))
    block_height = glyph_height + max(0, count - 1) * text_box_line_height()
    # Pillow's font origin is above its visible glyphs; center the actual ink.
    text_y = top + max(0, (bottom - top - block_height) // 2) - bbox[1]
    return left, text_y, lines, max_lines


def draw_text_box(image: Image.Image, box: tuple[int, int, int, int], text: str, pal, frame: int) -> None:
    draw = ImageDraw.Draw(image)
    x0, y0, x1, y1 = box
    asset = _load_text_box_frame((x1 - x0, y1 - y0))
    if asset:
        image.paste(asset, (x0, y0))
        text_fill = (248, 248, 248)
        cursor_fill = (248, 248, 248)
    else:
        PixelRenderer.draw_panel(draw, box, pal.panel, pal.panel_shadow, pal.ink)
        text_fill = pal.ink
        cursor_fill = pal.red

    text_font = font(14)
    text_x, text_y, lines, max_lines = text_box_layout(draw, box, text)

    y = text_y
    visible_lines = _scroll_lines(lines, max_lines, frame)
    for line in visible_lines:
        draw.text((text_x, y), line, font=text_font, fill=text_fill)
        y += text_box_line_height()
    if frame % 20 < 10:
        cursor_h = text_box_cursor_height()
        cursor_y = y0 + (y1 - y0 - cursor_h) // 2
        draw.polygon(
            [
                (x1 - scaled_px(24), cursor_y),
                (x1 - scaled_px(14), cursor_y + cursor_h // 2),
                (x1 - scaled_px(24), cursor_y + cursor_h),
            ],
            fill=cursor_fill,
        )


def _scroll_lines(lines: list[str], max_lines: int, frame: int) -> list[str]:
    start = scroll_line_start(lines, max_lines, frame)
    return lines[start : start + max_lines]


def scroll_line_start(lines: list[str], max_lines: int, frame: int) -> int:
    if len(lines) <= max_lines:
        return 0
    hold_frames = 8
    step_frames = 8
    cycle = hold_frames + (len(lines) - max_lines) * step_frames + hold_frames
    position = frame % max(1, cycle)
    if position < hold_frames:
        return 0
    return min(len(lines) - max_lines, (position - hold_frames) // step_frames + 1)


def wrap_text_lines(draw: ImageDraw.ImageDraw, text: str, text_font, max_text_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if draw.textbbox((0, 0), candidate, font=text_font)[2] > max_text_width:
                if current:
                    lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines


def text_box_visible_lines(box: tuple[int, int, int, int], text: str, text_y: int | None = None) -> int:
    _, y0, _, y1 = box
    first_line_y = text_y if text_y is not None else y0 + text_box_top_padding()
    available_height = max(0, y1 - first_line_y - text_box_bottom_padding())
    return max(1, available_height // text_box_line_height())


def text_box_top_padding() -> int:
    return scaled_px(TEXT_BOX_TEXT_TOP_PADDING)


def text_box_line_height() -> int:
    return scaled_px(TEXT_BOX_LINE_HEIGHT)


def text_box_bottom_padding() -> int:
    return scaled_px(TEXT_BOX_BOTTOM_PADDING)


def text_box_cursor_height() -> int:
    return scaled_px(TEXT_BOX_CURSOR_HEIGHT)
