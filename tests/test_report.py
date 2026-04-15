"""Tests for repro_floor_atlas.report — rendering only, no math."""

from __future__ import annotations

import csv
from pathlib import Path

from repro_floor_atlas.report import render_dashboard, render_e156_draft


SAMPLE_ROWS = [
    {
        "ma_id": "CD000028_pub4__A1", "review_id": "CD000028_pub4",
        "analysis_number": "1", "data_type": "binary", "k": "5",
        "scenario": "raw_extraction", "rounding_mode": "adaptive",
        "declared_dp": "0",
        "truth_pooled": "-0.12", "rounded_pooled": "-0.12",
        "delta": "0.0", "exceeds_fixed": "False", "exceeds_adaptive": "False",
    },
    {
        "ma_id": "CD000028_pub4__A1", "review_id": "CD000028_pub4",
        "analysis_number": "1", "data_type": "binary", "k": "5",
        "scenario": "forest_plot_extraction", "rounding_mode": "fixed_2dp",
        "declared_dp": "2",
        "truth_pooled": "-0.12", "rounded_pooled": "-0.127",
        "delta": "-0.007", "exceeds_fixed": "True", "exceeds_adaptive": "True",
    },
]


def _write_csv(rows, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def test_render_dashboard_produces_offline_html(tmp_path: Path):
    csv_path = tmp_path / "atlas.csv"
    _write_csv(SAMPLE_ROWS, csv_path)
    out_html = tmp_path / "index.html"
    render_dashboard(csv_path, out_html)
    html = out_html.read_text()
    assert "<!doctype html>" in html.lower() or "<!DOCTYPE html>" in html
    # Offline rule: no external CDN URLs
    for forbidden in ("cdn.jsdelivr", "unpkg.com", "cdnjs", "googleapis.com"):
        assert forbidden not in html, f"offline-only rule violated: found {forbidden}"
    # Dashboard must surface the claim headline
    assert "reproduction" in html.lower()
    # Dashboard must surface the 50% / percentage summary token
    assert "%" in html


def test_render_e156_draft_writes_seven_sentences_placeholder_s4(tmp_path: Path):
    csv_path = tmp_path / "atlas.csv"
    _write_csv(SAMPLE_ROWS, csv_path)
    out_md = tmp_path / "e156_paper.md"
    render_e156_draft(csv_path, out_md)
    md = out_md.read_text()
    # S4 is user-authored; must remain a clearly-marked placeholder
    assert "__PLACEHOLDER_S4__" in md
    # Other sentences must be drafted (non-empty)
    for marker in ("S1", "S2", "S3", "S5", "S6", "S7"):
        assert marker in md
