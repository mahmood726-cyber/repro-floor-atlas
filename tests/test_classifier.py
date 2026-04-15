"""Tests for repro_floor_atlas.classifier — the user-authored threshold rule."""

from __future__ import annotations

import pytest

from repro_floor_atlas.classifier import exceeds_threshold


def test_fixed_threshold_under_0005_is_reproducible():
    out = exceeds_threshold(delta=0.004, declared_dp=2, threshold_mode="fixed")
    assert out["fixed"] is False


def test_fixed_threshold_over_0005_is_not_reproducible():
    out = exceeds_threshold(delta=0.006, declared_dp=2, threshold_mode="fixed")
    assert out["fixed"] is True


def test_fixed_threshold_exactly_0005_is_boundary_true():
    """At the boundary, favor marking as non-reproducible (conservative)."""
    out = exceeds_threshold(delta=0.005, declared_dp=2, threshold_mode="fixed")
    assert out["fixed"] is True


def test_adaptive_threshold_scales_with_declared_dp():
    # half-unit at 2 dp = 0.005
    out = exceeds_threshold(delta=0.004, declared_dp=2, threshold_mode="adaptive")
    assert out["adaptive"] is False
    out = exceeds_threshold(delta=0.006, declared_dp=2, threshold_mode="adaptive")
    assert out["adaptive"] is True
    # half-unit at 3 dp = 0.0005
    out = exceeds_threshold(delta=0.0004, declared_dp=3, threshold_mode="adaptive")
    assert out["adaptive"] is False
    out = exceeds_threshold(delta=0.0006, declared_dp=3, threshold_mode="adaptive")
    assert out["adaptive"] is True


def test_negative_delta_handled_by_absolute_value():
    out = exceeds_threshold(delta=-0.01, declared_dp=2, threshold_mode="fixed")
    assert out["fixed"] is True


def test_both_mode_returns_both_keys():
    out = exceeds_threshold(delta=0.006, declared_dp=2, threshold_mode="both")
    assert set(out.keys()) == {"fixed", "adaptive"}


def test_nan_delta_not_reproducible_both_modes():
    import math
    out = exceeds_threshold(delta=math.nan, declared_dp=2, threshold_mode="both")
    # NaN is neither reproducible nor non-reproducible; agreed convention: True
    # (treat NaN as a failure-to-reproduce)
    assert out["fixed"] is True
    assert out["adaptive"] is True
