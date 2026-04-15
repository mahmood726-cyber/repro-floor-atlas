"""Pure round-and-repool. Zero I/O.

For each MA, computes the 'truth' pooled effect from machine-precision per-trial
inputs, then computes the 'rounded' pooled effect after rounding per-trial
numerics to the precision a Cochrane reader can extract (Scenario A = raw
data, Scenario B = forest-plot log-effects).

Returns the absolute delta on the natural reporting scale (log for binary/GIV;
raw for continuous mean-difference).
"""

from __future__ import annotations

from repro_floor_atlas import _metaaudit_path  # noqa: F401  (ensures metaaudit on sys.path)

from dataclasses import dataclass
from enum import Enum

import numpy as np

from metaaudit.recompute import compute_log_or, compute_md

from repro_floor_atlas.loader import MAInputs


class Scenario(Enum):
    A = "raw_extraction"
    B = "forest_plot_extraction"


@dataclass(frozen=True)
class PrecisionSpec:
    mode: str  # "adaptive" | "fixed"
    dp: int | None = None  # required if mode == "fixed"

    def resolve_dp(self, data_type: str, scenario: Scenario) -> int:
        """Return the effective decimal precision for a given (data_type, scenario)."""
        if self.mode == "fixed":
            if self.dp is None:
                raise ValueError("PrecisionSpec.mode=='fixed' requires dp")
            return self.dp
        # adaptive: map to Cochrane's typical published precision per data type
        if scenario is Scenario.B:
            return 2  # forest plots always show log-effects to ~2 dp
        if data_type == "binary":
            return 0  # counts are integer
        if data_type == "continuous":
            return 1  # means/SDs to 1 dp
        if data_type == "giv":
            return 2  # published yi/se to 2 dp
        raise ValueError(f"unknown data_type: {data_type}")


@dataclass(frozen=True)
class FloorResult:
    ma_id: str
    scenario: str
    rounding_mode: str       # e.g. "adaptive" | "fixed_1dp" | "fixed_2dp" | "fixed_3dp"
    declared_dp: int
    truth_pooled: float
    rounded_pooled: float
    delta: float             # rounded_pooled - truth_pooled (absolute value taken later)
    k: int
    data_type: str


def _round_to(arr: np.ndarray, dp: int) -> np.ndarray:
    """Half-even round to dp decimals; preserves integer-valued arrays when dp==0."""
    if dp == 0:
        return np.rint(arr)
    return np.round(arr, decimals=dp)


def _pool_fixed_effect(yi: np.ndarray, vi: np.ndarray) -> float:
    """Inverse-variance fixed-effect pooled estimate. Guard vi <= 0."""
    vi_safe = np.where(vi > 0, vi, np.finfo(float).eps)
    w = 1.0 / vi_safe
    return float(np.sum(w * yi) / np.sum(w))


def _yi_vi_truth(ma: MAInputs) -> tuple[np.ndarray, np.ndarray]:
    """Compute trial-level (yi, vi) at machine precision."""
    if ma.data_type == "binary":
        b = ma.binary
        return compute_log_or(b.e_cases, b.e_n, b.c_cases, b.c_n)
    if ma.data_type == "continuous":
        c = ma.continuous
        return compute_md(
            c.e_mean, c.e_sd, c.e_n,
            c.c_mean, c.c_sd, c.c_n,
        )
    if ma.data_type == "giv":
        g = ma.giv
        return g.yi.copy(), g.se.copy() ** 2
    raise ValueError(f"unknown data_type: {ma.data_type}")


def _yi_vi_scenario_A(ma: MAInputs, dp: int) -> tuple[np.ndarray, np.ndarray]:
    """Scenario A: round raw per-trial inputs to dp, recompute (yi, vi)."""
    if ma.data_type == "binary":
        b = ma.binary
        # Counts are integers; rounding at dp>=0 is a no-op for binary
        return compute_log_or(
            _round_to(b.e_cases, 0), _round_to(b.e_n, 0),
            _round_to(b.c_cases, 0), _round_to(b.c_n, 0),
        )
    if ma.data_type == "continuous":
        c = ma.continuous
        return compute_md(
            _round_to(c.e_mean, dp), _round_to(c.e_sd, dp), _round_to(c.e_n, 0),
            _round_to(c.c_mean, dp), _round_to(c.c_sd, dp), _round_to(c.c_n, 0),
        )
    if ma.data_type == "giv":
        g = ma.giv
        yi_r = _round_to(g.yi, dp)
        se_r = _round_to(g.se, dp)
        return yi_r, se_r ** 2
    raise ValueError(f"unknown data_type: {ma.data_type}")


def _yi_vi_scenario_B(ma: MAInputs, dp: int) -> tuple[np.ndarray, np.ndarray]:
    """Scenario B: derive truth (yi, vi), then round each to dp."""
    yi, vi = _yi_vi_truth(ma)
    se = np.sqrt(vi)
    yi_r = _round_to(yi, dp)
    se_r = _round_to(se, dp)
    return yi_r, se_r ** 2


def simulate_floor(
    ma: MAInputs,
    spec: PrecisionSpec,
    scenario: Scenario,
) -> FloorResult:
    """Compute the reproduction floor for one MA at one precision/scenario."""
    dp = spec.resolve_dp(ma.data_type, scenario)
    yi_truth, vi_truth = _yi_vi_truth(ma)
    truth = _pool_fixed_effect(yi_truth, vi_truth)

    if scenario is Scenario.A:
        yi_r, vi_r = _yi_vi_scenario_A(ma, dp)
    elif scenario is Scenario.B:
        yi_r, vi_r = _yi_vi_scenario_B(ma, dp)
    else:
        raise ValueError(f"unknown scenario: {scenario}")

    rounded = _pool_fixed_effect(yi_r, vi_r)

    if spec.mode == "adaptive":
        rounding_mode = "adaptive"
    else:
        rounding_mode = f"fixed_{dp}dp"

    return FloorResult(
        ma_id=ma.ma_id,
        scenario=scenario.value,
        rounding_mode=rounding_mode,
        declared_dp=dp,
        truth_pooled=truth,
        rounded_pooled=rounded,
        delta=rounded - truth,
        k=ma.k,
        data_type=ma.data_type,
    )
