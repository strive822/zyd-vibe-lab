"""Fixed M1 presentation samples and the meaning of their graphic marks.

The collapsed C/G dials each show that provider's lowest known remaining
percentage across five-hour and weekly windows, with an inner window glyph.
Expansion shows both windows separately. Percentages are relative to each
provider's own plan and are never absolute capacity.
DeepSeek is an account balance, so it has no invented progress percentage.
"""

from __future__ import annotations

from dataclasses import dataclass


LOW_REMAINING = 15


@dataclass(frozen=True)
class QuotaSample:
    codex_5h: float | None
    codex_week: float | None
    glm_5h: float | None
    glm_week: float | None
    deepseek_balance: str | None

    def percent(self, provider: str, window: str) -> float | None:
        field = {("codex", "5h"): self.codex_5h,
                 ("codex", "week"): self.codex_week,
                 ("glm", "5h"): self.glm_5h,
                 ("glm", "week"): self.glm_week}[(provider, window)]
        return field


def lowest_remaining(sample: QuotaSample, *, include_week: bool = False) -> tuple[str, str, float] | None:
    """Choose the smallest known remaining percentage; unknown is never zero.

    The stable order prefers five-hour windows, then Codex, when values tie.
    DeepSeek's currency balance cannot be ranked against quota percentages.
    """
    windows: tuple[tuple[str, str], ...] = (("codex", "5h"), ("glm", "5h"))
    if include_week:
        windows += (("codex", "week"), ("glm", "week"))
    known = [(provider, window, value)
             for provider, window in windows
             if (value := sample.percent(provider, window)) is not None]
    return min(known, key=lambda entry: entry[2]) if known else None


def tightest_provider_window(sample: QuotaSample, provider: str) -> tuple[str, float] | None:
    """The dock's one dial per provider shows its lowest known window.

    Prefer five hours on a tie; a missing window is never treated as zero.
    """
    known = [(window, value) for window in ("5h", "week")
             if (value := sample.percent(provider, window)) is not None]
    return min(known, key=lambda entry: entry[1]) if known else None


SCENARIOS: dict[str, QuotaSample] = {
    "baseline": QuotaSample(68, 42, 71, 58, "¥86.42"),
    "abundant": QuotaSample(92, 84, 87, 76, "¥86.42"),
    "middle": QuotaSample(51, 47, 48, 53, "¥86.42"),
    "low": QuotaSample(8, 19, 71, 58, "¥86.42"),
    "week_low": QuotaSample(92, 3, 87, 76, "¥86.42"),
    "both_low": QuotaSample(8, 6, 12, 9, "¥86.42"),
    "unknown": QuotaSample(None, 42, None, 58, None),
    # Keep the two dock-selected weekly readings equal to baseline. Only the
    # completeness of the other windows changes in trust-state comparisons.
    "partial_unknown": QuotaSample(None, 42, None, 58, "¥86.42"),
    "all_unknown": QuotaSample(None, None, None, None, None),
}


def sample_for(scenario: str, state: str) -> QuotaSample:
    sample = SCENARIOS[scenario]
    if state in ("loading", "empty", "error"):
        return QuotaSample(None, None, None, None, None)
    if state == "disconnected":
        return QuotaSample(sample.codex_5h, sample.codex_week, sample.glm_5h, sample.glm_week, None)
    return sample
