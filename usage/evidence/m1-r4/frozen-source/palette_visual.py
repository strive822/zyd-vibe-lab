"""Semantic colour candidates for the M1 quota visual prototype.

Colour identifies a provider or a secondary event. Quota length and the low
square / unknown dash remain readable without colour.
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass

from PySide6.QtGui import QColor


@dataclass(frozen=True)
class Palette:
    codex: QColor
    glm: QColor
    balance: QColor
    reminder: QColor
    benefit: QColor
    action: QColor
    low: QColor


LEGACY_PALETTE = Palette(*(QColor(c) for c in (
    "#58623d", "#58623d", "#58623d", "#1e2119",
    "#58623d", "#58623d", "#9d563c",
)))

# The four families change the relationship between platform, money, and
# attention. Four chroma steps per family give 16 actual Qt-rendered seeds.
FAMILIES = {
    "H": ("Herbarium", ("#536d30", "#187578", "#a35436", "#a16b1d", "#637941", "#435c35", "#b54632")),
    "E": ("Enamel", ("#3e5b8b", "#3a765b", "#936522", "#b45139", "#697546", "#455a5a", "#a84036")),
    "M": ("Mineral", ("#56688a", "#347e72", "#895b61", "#a76c27", "#6e7956", "#4c5b68", "#ab4b3d")),
    "T": ("Tonal", ("#66713b", "#416981", "#a15e51", "#9f6428", "#71804a", "#46593e", "#b4473b")),
}


def _chroma(hex_color: str, factor: float) -> QColor:
    color = QColor(hex_color)
    h, l, s = colorsys.rgb_to_hls(color.redF(), color.greenF(), color.blueF())
    r, g, b = colorsys.hls_to_rgb(h, l, min(1.0, s * factor))
    return QColor.fromRgbF(r, g, b)


def _luminance(color: QColor) -> float:
    def channel(value: float) -> float:
        return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
    return .2126 * channel(color.redF()) + .7152 * channel(color.greenF()) + .0722 * channel(color.blueF())


def _text_contrast(color: QColor) -> QColor:
    """Keep the small benefit glyph legible on the fixed warm paper."""
    paper = QColor("#f5f2e9")
    result = QColor(color)
    while (_luminance(paper) + .05) / (_luminance(result) + .05) < 4.5:
        result = result.darker(103)
    return result


def candidate(name: str) -> Palette:
    family, step = name[0], int(name[1])
    assert family in FAMILIES and 1 <= step <= 4
    factor = (0.56, 0.78, 1.0, 1.22)[step - 1]
    colors = [_chroma(hex_color, factor) for hex_color in FAMILIES[family][1]]
    colors[4] = _text_contrast(colors[4])
    return Palette(*colors)
