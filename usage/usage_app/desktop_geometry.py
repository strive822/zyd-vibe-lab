"""Monitor-relative placement and exterior docking policy, without Qt objects."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, cast

Edge = Literal["left", "right", "top", "bottom"]
EDGES: tuple[Edge, ...] = ("left", "right", "top", "bottom")


@dataclass(frozen=True, slots=True)
class Rect:
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        if not all(math.isfinite(item) for item in (self.x, self.y, self.width, self.height)) or self.width <= 0 or self.height <= 0:
            raise ValueError("Invalid monitor rectangle")

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def clamp(self, x: float, y: float, width: float, height: float) -> tuple[float, float]:
        return min(max(x, self.x), max(self.x, self.right - width)), min(max(y, self.y), max(self.y, self.bottom - height))


@dataclass(frozen=True, slots=True)
class Monitor:
    key: str
    full: Rect
    work: Rect
    native_full: Rect | None = None


@dataclass(frozen=True, slots=True)
class Placement:
    monitor_key: str
    edge: Edge | None
    edge_offset_ratio: float = .33
    floating_x_ratio: float = .5
    floating_y_ratio: float = .33
    pinned: bool = False
    free_orientation: Edge = "right"

    def __post_init__(self) -> None:
        if self.edge not in (*EDGES, None) or self.free_orientation not in EDGES:
            raise ValueError("Invalid dock edge")
        if not all(math.isfinite(item) and 0 <= item <= 1 for item in (
            self.edge_offset_ratio, self.floating_x_ratio, self.floating_y_ratio)):
            raise ValueError("Invalid placement ratio")

    def position(self, monitor: Monitor, width: float, height: float) -> tuple[float, float]:
        work = monitor.work
        span_x, span_y = max(0, work.width - width), max(0, work.height - height)
        if self.edge in ("left", "right"):
            return work.x + (span_x if self.edge == "right" else 0), work.y + span_y * self.edge_offset_ratio
        if self.edge in ("top", "bottom"):
            return work.x + span_x * self.edge_offset_ratio, work.y + (span_y if self.edge == "bottom" else 0)
        return work.x + span_x * self.floating_x_ratio, work.y + span_y * self.floating_y_ratio


def exterior_edge(monitor: Monitor, edge: Edge, center: float, others: tuple[Monitor, ...], *, radius: float = 36) -> bool:
    work, full = monitor.work, monitor.full
    # A taskbar makes an internal work-area boundary; it is not a display seam.
    if (edge == "left" and work.x > full.x + 1 or edge == "right" and work.right < full.right - 1 or
        edge == "top" and work.y > full.y + 1 or edge == "bottom" and work.bottom < full.bottom - 1):
        return True
    physical = monitor.native_full
    if physical:
        if edge in ("left", "right"):
            ratio = physical.height / full.height
            center = physical.y + (center - full.y) * ratio
        else:
            ratio = physical.width / full.width
            center = physical.x + (center - full.x) * ratio
        radius *= ratio
        full = physical
    for other in others:
        if other.key == monitor.key:
            continue
        target = other.native_full if physical and other.native_full else other.full
        if edge == "left":
            touches = abs(target.right - full.x) <= 2
            low, high = target.y, target.bottom
        elif edge == "right":
            touches = abs(target.x - full.right) <= 2
            low, high = target.y, target.bottom
        elif edge == "top":
            touches = abs(target.bottom - full.y) <= 2
            low, high = target.x, target.right
        else:
            touches = abs(target.y - full.bottom) <= 2
            low, high = target.x, target.right
        if touches and min(center + radius, high) > max(center - radius, low):
            return False
    return True


def nearest_dock(monitor: Monitor, monitors: tuple[Monitor, ...], x: float, y: float,
                 width: float, height: float, delta_x: float, delta_y: float, *, snap: float = 12) -> Edge | None:
    x, y = monitor.work.clamp(x, y, width, height)
    distances = {"left": x - monitor.work.x, "right": max(0, monitor.work.width - width) - (x - monitor.work.x),
                 "top": y - monitor.work.y, "bottom": max(0, monitor.work.height - height) - (y - monitor.work.y)}
    candidates = [edge for edge in EDGES if distances[edge] <= snap and exterior_edge(monitor, edge,
                  y + height / 2 if edge in ("left", "right") else x + width / 2, monitors)]
    if len(candidates) > 1:
        axis = ("left", "right") if abs(delta_x) > abs(delta_y) else ("top", "bottom")
        candidates = [edge for edge in candidates if edge in axis] or candidates
    if not candidates:
        return None
    selected = candidates[0]
    for candidate in candidates[1:]:
        if distances[candidate] < distances[selected]:
            selected = candidate
    return selected


def capture_placement(monitor: Monitor, x: float, y: float, width: float, height: float,
                      edge: Edge | None, pinned: bool, free_orientation: Edge) -> Placement:
    work = monitor.work
    rx = min(1, max(0, (x - work.x) / max(1, work.width - width)))
    ry = min(1, max(0, (y - work.y) / max(1, work.height - height)))
    return Placement(monitor.key, edge, ry if edge in ("left", "right") else rx, rx, ry, pinned, free_orientation)


def placement_data(value: Placement) -> dict[str, object]:
    return {"monitorKey": value.monitor_key, "edge": value.edge, "edgeOffsetRatio": value.edge_offset_ratio,
            "floatingPosition": {"xRatio": value.floating_x_ratio, "yRatio": value.floating_y_ratio},
            "displayMode": "pinned" if value.pinned else "expanded" if value.edge is None else "collapsed",
            "freeOrientation": value.free_orientation}


def placement_from_data(value: object) -> Placement:
    if not isinstance(value, dict) or not isinstance(value.get("floatingPosition"), dict):
        raise ValueError("Invalid placement configuration")
    key = value.get("monitorKey")
    edge = value.get("edge")
    orientation = value.get("freeOrientation", "right")
    if not isinstance(key, str) or edge not in (*EDGES, None) or orientation not in EDGES:
        raise ValueError("Invalid placement configuration")
    mode = value.get("displayMode")
    if mode not in ("pinned", "expanded", "collapsed"):
        raise ValueError("Invalid placement configuration")
    ratios = [value.get("edgeOffsetRatio"), value["floatingPosition"].get("xRatio"), value["floatingPosition"].get("yRatio")]
    if any(not isinstance(item, (int, float)) or isinstance(item, bool) for item in ratios):
        raise ValueError("Invalid placement configuration")
    return Placement(key, cast(Edge | None, edge), float(ratios[0]), float(ratios[1]), float(ratios[2]),
                     mode == "pinned", cast(Edge, orientation))
