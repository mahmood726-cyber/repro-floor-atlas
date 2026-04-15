"""Reproduction-threshold classifier.

Decides whether a reproduction delta counts as a 'reproduction failure'.
Called once per (ma_id, scenario, rounding_mode) row in atlas.py.

Design choices:
  - Boundary uses `>=` so exactly-0.005 counts as non-reproducible (conservative).
  - NaN is treated as failure for both modes (NaN can arise from zero-cell
    continuity correction or degenerate compute_md inputs; surfacing it as a
    failure prevents silent corruption per lessons.md 'Silent failure
    sentinels are the enemy').
  - Negative delta handled via abs().
"""

from __future__ import annotations

import math
from typing import Literal


FIXED_THRESHOLD = 0.005  # SGLT2i-HFpEF ship threshold + Cochrane 2-dp CI half-width


def exceeds_threshold(
    delta: float,
    declared_dp: int,
    threshold_mode: Literal["fixed", "adaptive", "both"],
) -> dict[str, bool]:
    """Return whether a reproduction |Δ| counts as non-reproducible.

    Returns:
        - {"fixed": bool} when threshold_mode == "fixed"
        - {"adaptive": bool} when threshold_mode == "adaptive"
        - {"fixed": bool, "adaptive": bool} when threshold_mode == "both"
    """
    is_nan = math.isnan(delta)
    abs_delta = abs(delta)
    adaptive_threshold = 0.5 * 10 ** (-declared_dp)

    out: dict[str, bool] = {}
    if threshold_mode in ("fixed", "both"):
        out["fixed"] = True if is_nan else abs_delta >= FIXED_THRESHOLD
    if threshold_mode in ("adaptive", "both"):
        out["adaptive"] = True if is_nan else abs_delta >= adaptive_threshold
    return out
