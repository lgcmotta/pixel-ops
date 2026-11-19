from __future__ import annotations

import os
import sys

from PIL import Image

from pixel_ops.outputs.base import DisplayOutput


def enable_dpi_awareness():
    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except (AttributeError, OSError):
            pass


def hide_from_taskbar(hwnd):
    """Keep the LCD visible while the desktop controller supplies its tray UI."""
    if sys.platform != "win32":
        return
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    get_style = user32.GetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user32.GetWindowLongW
    set_style = user32.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user32.SetWindowLongW
    get_style.argtypes = [wintypes.HWND, ctypes.c_int]
    get_style.restype = ctypes.c_ssize_t
    set_style.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    set_style.restype = ctypes.c_ssize_t
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    style = get_style(hwnd, -20)
    # The shell re-evaluates taskbar membership when the window is shown again.
    user32.ShowWindow(hwnd, 0)
    ctypes.set_last_error(0)
    previous = set_style(hwnd, -20, (style | 0x80) & ~0x40000)  # TOOLWINDOW, not APPWINDOW
    error = ctypes.get_last_error()
    user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x37)  # FRAMECHANGED | NOMOVE | NOSIZE | NOZORDER | NOACTIVATE
    user32.ShowWindow(hwnd, 4)  # SHOWNOACTIVATE
    if not previous and error:
        raise ctypes.WinError(error)


def select_monitor(sizes, target, index=None):
    if index is not None:
        if index < 0 or index >= len(sizes) or tuple(sizes[index]) != tuple(target):
            raise RuntimeError("Selected monitor is absent or has a different resolution. Select the Lian Li monitor in Config Studio.")
        return index
    matches = [i for i, size in enumerate(sizes) if tuple(size) == tuple(target)]
    if len(matches) != 1:
        raise RuntimeError("Enable Lian Li secondary-screen mode and select its 1920x480 monitor in Config Studio. Use Window preview for setup.")
    return matches[0]


class WindowOutput(DisplayOutput):
    """Renders frames into a desktop window for local monitoring."""

    def __init__(self, width: int, height: int, scale: int = 2, title: str = "Pixel OPs", *, borderless=False, monitor=None, preview=False):
        self.width = width
        self.height = height
        self.scale = max(1, scale)
        self.title = title
        self.pygame = None
        self.screen = None
        self.closed = False
        self.borderless = borderless
        self.monitor = monitor
        self.preview = preview
        self.window_size = (self.width * self.scale, self.height * self.scale)

    def start(self) -> None:
        try:
            os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
            import pygame
        except ImportError as error:
            raise RuntimeError("Window output requires pygame-ce. Install dependencies with requirements.txt.") from error

        self.pygame = pygame
        enable_dpi_awareness()
        pygame.init()
        pygame.display.set_caption(self.title)
        if self.preview:
            factor = min(1.0, 1200 / self.width, 700 / self.height)
            self.window_size = (int(self.width * factor), int(self.height * factor))
            self.screen = pygame.display.set_mode(self.window_size)
        elif self.borderless:
            try:
                monitor = select_monitor(pygame.display.get_desktop_sizes(), self.window_size, self.monitor)
            except RuntimeError:
                pygame.quit()
                raise
            self.screen = pygame.display.set_mode(self.window_size, pygame.NOFRAME, display=monitor)
        else:
            self.screen = pygame.display.set_mode(self.window_size, display=self.monitor or 0)
        if not self.preview and os.environ.get("PIXEL_OPS_TRAY") == "1":
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                hide_from_taskbar(hwnd)

    def send(self, frame: Image.Image) -> None:
        if self.closed:
            raise RuntimeError("Window was closed.")
        if self.pygame is None or self.screen is None:
            raise RuntimeError("WindowOutput.start() must be called before send().")

        for event in self.pygame.event.get():
            if event.type == self.pygame.QUIT or (event.type == self.pygame.KEYDOWN and event.key == self.pygame.K_ESCAPE):
                self.closed = True
                raise RuntimeError("Window was closed.")

        display_frame = frame.convert("RGB")
        surface = self.pygame.image.frombuffer(display_frame.tobytes(), display_frame.size, "RGB")
        if surface.get_size() != self.window_size:
            surface = self.pygame.transform.scale(surface, self.window_size)
        self.screen.blit(surface, (0, 0))
        self.pygame.display.flip()

    def stop(self) -> None:
        if self.pygame is not None:
            self.pygame.quit()
        self.pygame = None
        self.screen = None


if __name__ == "__main__":
    import json
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    enable_dpi_awareness()
    pygame.display.init()
    print(json.dumps([{"index": i, "width": w, "height": h} for i, (w, h) in enumerate(pygame.display.get_desktop_sizes())]))
    pygame.display.quit()
