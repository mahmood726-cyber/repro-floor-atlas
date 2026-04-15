"""Orchestrator: iterate MAs × scenarios × rounding modes; write atlas.csv."""

from __future__ import annotations

import csv
from pathlib import Path

from repro_floor_atlas.classifier import exceeds_threshold
from repro_floor_atlas.loader import MAInputs
from repro_floor_atlas.precision_floor import (
    PrecisionSpec, Scenario, simulate_floor,
)


CSV_COLUMNS = [
    "ma_id", "review_id", "analysis_number", "data_type", "k",
    "scenario", "rounding_mode", "declared_dp",
    "truth_pooled", "rounded_pooled", "delta",
    "exceeds_fixed", "exceeds_adaptive",
]

ROUNDING_SPECS = [
    PrecisionSpec(mode="adaptive"),
    PrecisionSpec(mode="fixed", dp=1),
    PrecisionSpec(mode="fixed", dp=2),
    PrecisionSpec(mode="fixed", dp=3),
]

SCENARIOS = [Scenario.A, Scenario.B]


def build_atlas(mas: list[MAInputs], out_csv: Path) -> int:
    """Run the full (MAs × scenarios × rounding modes) grid; write CSV.

    Returns the number of rows written.
    """
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    n_written = 0
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for ma in mas:
            for scenario in SCENARIOS:
                for spec in ROUNDING_SPECS:
                    fr = simulate_floor(ma, spec, scenario)
                    cls = exceeds_threshold(
                        delta=fr.delta,
                        declared_dp=fr.declared_dp,
                        threshold_mode="both",
                    )
                    writer.writerow({
                        "ma_id": fr.ma_id,
                        "review_id": ma.review_id,
                        "analysis_number": ma.analysis_number,
                        "data_type": fr.data_type,
                        "k": fr.k,
                        "scenario": fr.scenario,
                        "rounding_mode": fr.rounding_mode,
                        "declared_dp": fr.declared_dp,
                        "truth_pooled": fr.truth_pooled,
                        "rounded_pooled": fr.rounded_pooled,
                        "delta": fr.delta,
                        "exceeds_fixed": cls["fixed"],
                        "exceeds_adaptive": cls["adaptive"],
                    })
                    n_written += 1
    return n_written
