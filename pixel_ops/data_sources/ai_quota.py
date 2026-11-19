"""Provider-neutral, immutable account quota observations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AIQuotaWindow:
    bucket: str
    label: str
    window_minutes: int
    used_percent: float
    reset_at: datetime | None = None

    def remaining(self, now: datetime) -> float | None:
        if self.reset_at is not None and now >= self.reset_at:
            return None
        return max(0.0, min(100.0, 100.0 - self.used_percent))


@dataclass(frozen=True)
class AIQuotaSnapshot:
    provider: str
    windows: tuple[AIQuotaWindow, ...] = ()
    observed_at: datetime | None = None
    status: str = "disconnected"
    account: str = ""
    plan: str = ""
    daily_tokens: tuple[tuple[str, int], ...] = ()
    lifetime_tokens: int | None = None
    stale_seconds: int = 180

    def fresh(self, now: datetime) -> bool:
        return self.status == "ok" and self.observed_at is not None and 0 <= (now - self.observed_at).total_seconds() <= self.stale_seconds
