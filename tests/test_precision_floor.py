"""Tests for repro_floor_atlas.precision_floor — pure round-and-repool."""

from __future__ import annotations

import numpy as np

from repro_floor_atlas.loader import (
    BinaryTrials, ContinuousTrials, GIVTrials, MAInputs,
)
from repro_floor_atlas.precision_floor import (
    PrecisionSpec, Scenario, simulate_floor,
)


def _make_binary_ma(k: int = 5, seed: int = 0) -> MAInputs:
    rng = np.random.default_rng(seed)
    e_n = rng.integers(50, 500, size=k).astype(float)
    c_n = rng.integers(50, 500, size=k).astype(float)
    e_cases = (e_n * rng.uniform(0.05, 0.30, size=k)).astype(int).astype(float)
    c_cases = (c_n * rng.uniform(0.10, 0.35, size=k)).astype(int).astype(float)
    return MAInputs(
        ma_id="TEST_BIN__A1", review_id="TEST_BIN", analysis_number=1,
        k=k, data_type="binary",
        binary=BinaryTrials(e_cases=e_cases, e_n=e_n, c_cases=c_cases, c_n=c_n),
    )


def _make_continuous_ma(k: int = 4, seed: int = 1) -> MAInputs:
    rng = np.random.default_rng(seed)
    e_n = rng.integers(30, 200, size=k).astype(float)
    c_n = rng.integers(30, 200, size=k).astype(float)
    e_mean = rng.normal(10.0, 2.0, size=k)
    c_mean = rng.normal(11.0, 2.0, size=k)
    e_sd = rng.uniform(1.0, 3.0, size=k)
    c_sd = rng.uniform(1.0, 3.0, size=k)
    return MAInputs(
        ma_id="TEST_CONT__A1", review_id="TEST_CONT", analysis_number=1,
        k=k, data_type="continuous",
        continuous=ContinuousTrials(
            e_mean=e_mean, e_sd=e_sd, e_n=e_n,
            c_mean=c_mean, c_sd=c_sd, c_n=c_n,
        ),
    )


def _make_giv_ma(k: int = 3, seed: int = 2) -> MAInputs:
    rng = np.random.default_rng(seed)
    yi = rng.normal(-0.3, 0.2, size=k)
    se = rng.uniform(0.05, 0.25, size=k)
    return MAInputs(
        ma_id="TEST_GIV__A1", review_id="TEST_GIV", analysis_number=1,
        k=k, data_type="giv",
        giv=GIVTrials(yi=yi, se=se),
    )


def test_binary_scenario_A_integer_counts_gives_zero_floor():
    """Scenario A binary: counts are integer → rounding is a no-op → delta==0."""
    ma = _make_binary_ma()
    spec = PrecisionSpec(mode="adaptive")
    result = simulate_floor(ma, spec, Scenario.A)
    assert abs(result.delta) < 1e-12


def test_continuous_scenario_A_rounding_to_1dp_produces_nonzero_delta():
    """Scenario A continuous: means/SDs rounded to 1 dp → nonzero delta in general."""
    ma = _make_continuous_ma()
    spec = PrecisionSpec(mode="fixed", dp=1)
    result = simulate_floor(ma, spec, Scenario.A)
    assert abs(result.delta) > 0  # with generic random inputs, rounding bites
    assert np.isfinite(result.truth_pooled)
    assert np.isfinite(result.rounded_pooled)


def test_giv_scenario_B_scaling_law_holds():
    """Scenario B GIV: rounding log-effect+SE to d dp gives |delta| bounded by ~5e-d."""
    ma = _make_giv_ma(k=10, seed=42)
    for dp in (1, 2, 3):
        spec = PrecisionSpec(mode="fixed", dp=dp)
        result = simulate_floor(ma, spec, Scenario.B)
        bound = 5 * 10 ** (-dp)  # loose but fair: half-unit times small factor
        assert abs(result.delta) < bound, (
            f"dp={dp}: |delta|={abs(result.delta):.6f} exceeded bound {bound:.6f}"
        )


def test_idempotent_at_high_precision():
    """At dp=10, rounding is effectively a no-op → delta ≈ 0."""
    ma = _make_continuous_ma()
    spec = PrecisionSpec(mode="fixed", dp=10)
    result = simulate_floor(ma, spec, Scenario.A)
    assert abs(result.delta) < 1e-8


def test_single_trial_ma_handled():
    """k=1 MA still returns a valid FloorResult (no division by zero)."""
    ma = _make_giv_ma(k=1, seed=0)
    spec = PrecisionSpec(mode="fixed", dp=2)
    result = simulate_floor(ma, spec, Scenario.B)
    assert np.isfinite(result.truth_pooled)
    assert np.isfinite(result.rounded_pooled)
