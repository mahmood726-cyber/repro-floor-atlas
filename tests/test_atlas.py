"""Tests for repro_floor_atlas.atlas — the orchestrator."""

from __future__ import annotations

import csv
from pathlib import Path

from repro_floor_atlas.atlas import build_atlas
from repro_floor_atlas.loader import load_directory


EXPECTED_COLUMNS = [
    "ma_id", "review_id", "analysis_number", "data_type", "k",
    "scenario", "rounding_mode", "declared_dp",
    "truth_pooled", "rounded_pooled", "delta",
    "exceeds_fixed", "exceeds_adaptive",
]


def test_build_atlas_on_first_review(pairwise70_dir: Path, tmp_path: Path):
    """Running the orchestrator on one review produces a well-formed atlas.csv."""
    # Only load the first 1 review for speed
    mas = load_directory(pairwise70_dir, max_reviews=1)
    assert len(mas) >= 1

    out_csv = tmp_path / "atlas.csv"
    n_rows = build_atlas(mas, out_csv)

    # Each MA produces 2 scenarios × 4 rounding modes = 8 rows
    assert n_rows == len(mas) * 8

    with out_csv.open() as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        assert header == EXPECTED_COLUMNS
        rows = list(reader)
    assert len(rows) == n_rows
    # Every row has a non-empty ma_id
    assert all(r["ma_id"] for r in rows)
    # scenario values are constrained
    assert all(r["scenario"] in ("raw_extraction", "forest_plot_extraction") for r in rows)
    # rounding_mode values are constrained
    valid_modes = {"adaptive", "fixed_1dp", "fixed_2dp", "fixed_3dp"}
    assert all(r["rounding_mode"] in valid_modes for r in rows)
