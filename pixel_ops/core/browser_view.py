"""Optional, game-owned companion presentations for browser-based outputs."""
from dataclasses import dataclass
from typing import Mapping, Protocol


@dataclass(frozen=True)
class BrowserView:
    """Serialized presentation, safe to transfer to an output worker thread."""

    state_json: bytes
    image_png: bytes | None = None


class BrowserViewProvider(Protocol):
    def browser_views(self) -> Mapping[str, BrowserView]: ...
