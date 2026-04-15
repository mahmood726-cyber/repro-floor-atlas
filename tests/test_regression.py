"""Regression: re-running the atlas on the 10-MA smoke set must bit-match the
committed fixture. Any drift fails the build.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from repro_floor_atlas.atlas import build_atlas
from repro_floor_atlas.loader import load_directory


FIXTURE = Path(__file__).parent / "fixtures" / "smoke_10_mas.json"


def test_smoke_regression_bit_match(pairwise70_dir: Path, tmp_path: Path):
    if not FIXTURE.is_file():
        pytest.skip(f"Fixture missing: {FIXTURE}. Run scripts/seed_smoke_baseline.py")

    expected = json.loads(FIXTURE.read_text())
    mas = load_directory(pairwise70_dir, max_reviews=None)
    mas_sorted = sorted(mas, key=lambda m: (m.review_id, m.analysis_number))[:10]
    out_csv = tmp_path / "actual.csv"
    build_atlas(mas_sorted, out_csv)

    with out_csv.open() as f:
        actual_rows = list(csv.DictReader(f))

    assert len(actual_rows) == len(expected["rows"]), (
        f"row count drift: expected {len(expected['rows'])}, got {len(actual_rows)}"
    )

    for exp_row, act_row in zip(expected["rows"], actual_rows):
        for k in ("ma_id", "scenario", "rounding_mode", "data_type"):
            assert act_row[k] == exp_row[k], f"string field drift in {k}"
        for k in ("truth_pooled", "rounded_pooled", "delta"):
            a = round(float(act_row[k]), 12)
            e = float(exp_row[k])
            assert abs(a - e) < 1e-10, (
                f"numerical drift in {k} for {act_row['ma_id']}: "
                f"expected {e}, got {a}"
            )
