"""Seed the 10-MA smoke-regression baseline.

Deterministically picks the first 10 MAs (by sorted review_id, then analysis_number)
from Pairwise70 and writes the canonical (ma_id → per-row) mapping to a fixture.
Re-run only when the numerical contract intentionally changes.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from repro_floor_atlas.atlas import build_atlas, CSV_COLUMNS
from repro_floor_atlas.loader import load_directory

_ENV_VAR = "PAIRWISE70_DIR"
_env_val = os.environ.get(_ENV_VAR)
DATA_DIR = Path(_env_val) if _env_val else None
FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "smoke_10_mas.json"
TMP_CSV = Path(__file__).resolve().parent.parent / "outputs" / "smoke_10.csv"


def main() -> int:
    if DATA_DIR is None:
        sys.exit(f"{_ENV_VAR} env var is required (path to Pairwise70 .rda corpus).")
    if not DATA_DIR.is_dir():
        sys.exit(
            f"Pairwise70 corpus not found at {DATA_DIR}. Re-check {_ENV_VAR}."
        )
    mas = load_directory(DATA_DIR, max_reviews=None)
    mas_sorted = sorted(mas, key=lambda m: (m.review_id, m.analysis_number))[:10]
    TMP_CSV.parent.mkdir(parents=True, exist_ok=True)
    build_atlas(mas_sorted, TMP_CSV)

    # Read back the CSV and convert to a canonical JSON form
    import csv
    rows = []
    with TMP_CSV.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Normalize numeric fields for stable comparison
            for k in ("truth_pooled", "rounded_pooled", "delta"):
                r[k] = round(float(r[k]), 12)
            r["k"] = int(r["k"])
            r["declared_dp"] = int(r["declared_dp"])
            r["analysis_number"] = int(r["analysis_number"])
            rows.append(r)

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    with FIXTURE.open("w") as f:
        json.dump(
            {"columns": CSV_COLUMNS, "rows": rows, "ma_count": len(mas_sorted)},
            f,
            indent=2,
            sort_keys=True,
        )
    print(f"Wrote {len(rows)} rows ({len(mas_sorted)} MAs × 8) to {FIXTURE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
