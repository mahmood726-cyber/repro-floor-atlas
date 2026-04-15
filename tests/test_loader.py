"""Tests for repro_floor_atlas.loader."""

from __future__ import annotations

from pathlib import Path

from repro_floor_atlas.loader import load_reviews, MAInputs


def test_load_reviews_returns_ma_inputs(small_rda_file: Path):
    """Loading one .rda file yields at least one MAInputs with k>=1 trials."""
    results = load_reviews([small_rda_file])
    assert len(results) >= 1, "Expected at least one MA from a real Cochrane review"
    first = results[0]
    assert isinstance(first, MAInputs)
    assert first.k >= 1
    assert first.data_type in ("binary", "continuous", "giv")
    assert first.ma_id.startswith("CD")  # Cochrane review IDs start with CD


def test_ma_inputs_has_trial_level_arrays(small_rda_file: Path):
    """MAInputs exposes trial-level data as numpy arrays for the detected data_type."""
    results = load_reviews([small_rda_file])
    first = results[0]
    if first.data_type == "binary":
        assert first.binary is not None
        assert len(first.binary.e_cases) == first.k
    elif first.data_type == "continuous":
        assert first.continuous is not None
        assert len(first.continuous.e_mean) == first.k
    elif first.data_type == "giv":
        assert first.giv is not None
        assert len(first.giv.yi) == first.k
