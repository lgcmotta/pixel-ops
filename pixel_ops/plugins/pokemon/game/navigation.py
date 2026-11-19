"""Quiet, collision-aware overworld wandering in native map coordinates."""
from __future__ import annotations

import math
import random
from collections import deque

from PIL import Image, ImageDraw

Rect = tuple[int, int, int, int]
Point = tuple[int, int]


class WanderNavigator:
    """Walk connected paths using a small ground footprint, rather than the head.

    Walkable rectangles form a union. A route never jumps between disconnected
    islands, cuts a corner, or moves through an excluded region.
    """

    def __init__(self, bounds: Rect, walkable: list[Rect], blocked: list[Rect],
                 sprite_size: Point, rng: random.Random):
        self.rng = rng
        self.size = sprite_size
        self.step = 4
        x0, y0, x1, y1 = bounds
        mask = Image.new("L", (x1 - x0, y1 - y0))
        draw = ImageDraw.Draw(mask)
        for rects, fill in ((walkable, 255), (blocked, 0)):
            for left, top, right, bottom in rects:
                draw.rectangle((left - x0, top - y0, right - x0 - 1, bottom - y0 - 1), fill=fill)
        w, h = sprite_size
        self.nodes: set[Point] = set()
        for fy in range(y0 + h - 5, y1 - 4, self.step):
            for fx in range(x0 + w // 2, x1 - (w + 1) // 2 + 1, self.step):
                footprint = (fx - x0 - 5, fy - y0 - 3, fx - x0 + 5, fy - y0 + 3)
                if mask.crop(footprint).getextrema() == (255, 255):
                    self.nodes.add((fx, fy))
        self.position: tuple[float, float] | None = None
        self.path: deque[Point] = deque()
        self.pause_until = 0
        self.last_frame: int | None = None
        self.direction: str | None = None
        self.moving = False

    def place(self, x: float, y: float) -> None:
        if not self.nodes:
            return
        w, h = self.size
        target = (x + w / 2, y + h - 5)
        self.position = min(self.nodes, key=lambda p: (p[0] - target[0]) ** 2 + (p[1] - target[1]) ** 2)
        self.path.clear()

    def _choose_path(self) -> None:
        if self.position is None:
            return
        start = (round(self.position[0]), round(self.position[1]))
        parents: dict[Point, Point | None] = {start: None}
        distances = {start: 0}
        queue = deque([start])
        while queue:
            x, y = queue.popleft()
            for point in ((x + self.step, y), (x - self.step, y), (x, y + self.step), (x, y - self.step)):
                if point in self.nodes and point not in parents:
                    parents[point] = (x, y)
                    distances[point] = distances[(x, y)] + self.step
                    queue.append(point)
        farthest = max(distances.values())
        minimum = min(64, farthest * .6)
        candidates = [p for p, distance in distances.items() if distance >= minimum and distance > 0]
        if not candidates:
            return
        target = self.rng.choice(candidates)
        reverse = []
        while target != start:
            reverse.append(target)
            target = parents[target]
        # Keep corners; remove grid points along a straight stretch.
        points = [start] + list(reversed(reverse))
        for index in range(1, len(points)):
            a, b = points[index - 1], points[index]
            if index == len(points) - 1 or (b[0] - a[0], b[1] - a[1]) != (
                points[index + 1][0] - b[0], points[index + 1][1] - b[1]
            ):
                self.path.append(b)

    def pose(self, frame: int, fps: int, speed: float, *, enabled: bool = True) -> tuple[int, int, str | None]:
        if self.position is None:
            raise ValueError("Navigator must be placed before walking")
        if frame != self.last_frame:
            self.last_frame = frame
            self.moving = False
            if enabled and frame >= self.pause_until:
                if not self.path:
                    self._choose_path()
                if self.path:
                    x, y = self.position
                    tx, ty = self.path[0]
                    distance = math.hypot(tx - x, ty - y)
                    amount = min(max(.1, speed), distance)
                    if distance:
                        self.position = (x + (tx - x) * amount / distance, y + (ty - y) * amount / distance)
                        self.direction = ("right" if tx > x else "left") if tx != x else ("down" if ty > y else "up")
                        self.moving = True
                    if amount >= distance:
                        self.position = (tx, ty)
                        self.path.popleft()
                        if not self.path:
                            self.pause_until = frame + self.rng.randint(max(1, fps // 2), max(1, fps * 2))
        w, h = self.size
        return round(self.position[0] - w / 2), round(self.position[1] - h + 5), self.direction
