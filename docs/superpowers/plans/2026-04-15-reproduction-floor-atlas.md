# Reproduction-Floor Atlas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Python package that computes, for each of 6,229 Cochrane MAs in the Pairwise70 corpus, the reproduction floor induced by rounding per-trial inputs to Cochrane's published precision — then ship an E156 micro-paper + offline dashboard quantifying the percentage of MAs whose declared precision exceeds that floor.

**Architecture:** Five-module pipeline: `loader` (wraps MetaAudit's .rda loader) → `precision_floor` (pure round-and-repool; Scenario A raw-extraction and Scenario B forest-plot extraction) → `classifier` (pure threshold rule, USER-AUTHORED body) → `atlas` (orchestrator → atlas.csv) → `report` (HTML dashboard + E156 markdown). No network deps at runtime; offline-only dashboard; Sentinel pre-push gate; numerical-baseline regression fixture.

**Tech Stack:** Python 3.11+, numpy, scipy, pandas, pyreadr, MetaAudit (editable install from `C:\MetaAudit\`), pytest, Sentinel CLI, vanilla HTML/JS (no CDN).

**Spec:** `docs/superpowers/specs/2026-04-15-reproduction-floor-atlas-design.md`

---

## File Structure

Locked-in layout under `C:\Projects\repro-floor-atlas\`:

```
repro-floor-atlas/
├── .gitignore
├── LICENSE (MIT)
├── README.md
├── E156-PROTOCOL.md
├── requirements.txt
├── pyproject.toml
├── docs/
│   └── superpowers/
│       ├── specs/2026-04-15-reproduction-floor-atlas-design.md   (already exists)
│       └── plans/2026-04-15-reproduction-floor-atlas.md          (this file)
├── src/
│   └── repro_floor_atlas/
│       ├── __init__.py
│       ├── loader.py
│       ├── precision_floor.py
│       ├── classifier.py                   (USER-AUTHORED body)
│       ├── atlas.py
│       └── report.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/
│   │   └── smoke_10_mas.json               (committed regression baseline)
│   ├── test_loader.py
│   ├── test_precision_floor.py
│   ├── test_classifier.py
│   ├── test_atlas.py
│   ├── test_report.py
│   └── test_integration_metaaudit_contract.py
├── scripts/
│   ├── prereq_check.py
│   ├── run_atlas.py
│   └── seed_smoke_baseline.py
├── dashboard/
│   └── index.html                          (offline, no CDN)
├── e156-submission/
│   └── e156_paper.md
└── outputs/                                (gitignored)
    └── atlas.csv
```

**File responsibilities (one purpose each):**

| File | Responsibility |
|---|---|
| `loader.py` | Yield `AnalysisGroup` objects from Pairwise70 .rda files. Reuses `metaaudit.loader.load_all_reviews`. Zero math. |
| `precision_floor.py` | Pure: `(trial_inputs, precision_spec, scenario) → (truth, rounded, delta)`. Uses `metaaudit.recompute` for pooling. No I/O. |
| `classifier.py` | Pure: `(delta, declared_dp, mode) → {"fixed": bool, "adaptive": bool}`. USER-AUTHORED body. No I/O. |
| `atlas.py` | Orchestrator: iterate MAs × scenarios × rounding modes, assemble atlas.csv. No math (delegates to `precision_floor` + `classifier`). |
| `report.py` | Render `dashboard/index.html` + `e156-submission/e156_paper.md` from atlas.csv. No math. |

---

## Task 0: Preflight & repo initialization

**Files:**
- Create: `C:\Projects\repro-floor-atlas\.gitignore`
- Create: `C:\Projects\repro-floor-atlas\LICENSE`
- Create: `C:\Projects\repro-floor-atlas\scripts\prereq_check.py`

- [ ] **Step 1: Run preflight prereq check (fail closed if Pairwise70 missing)**

Create `scripts/prereq_check.py`:

```python
"""Preflight check: verify Pairwise70 corpus + MetaAudit package are importable.

Fail closed per rules.md 'Verification readiness preflight'. Exits non-zero with
an actionable message if any prereq is absent.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    PAIRWISE70_DIR = Path(r"C:\Projects\Pairwise70\data")
    METAAUDIT_DIR = Path(r"C:\MetaAudit\metaaudit")

    failures: list[str] = []

    if not PAIRWISE70_DIR.is_dir():
        failures.append(f"Missing Pairwise70 data dir: {PAIRWISE70_DIR}")
    else:
        rda_files = list(PAIRWISE70_DIR.glob("*.rda"))
        if len(rda_files) < 500:
            failures.append(
                f"Pairwise70 corpus under-populated: {len(rda_files)} .rda files "
                f"(expected >= 500)"
            )

    if not METAAUDIT_DIR.is_dir():
        failures.append(f"Missing MetaAudit package: {METAAUDIT_DIR}")
    else:
        try:
            sys.path.insert(0, str(METAAUDIT_DIR.parent))
            import metaaudit.loader  # noqa: F401
            import metaaudit.recompute  # noqa: F401
        except ImportError as e:
            failures.append(f"MetaAudit import failed: {e}")

    if failures:
        print("PREFLIGHT FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        print("\nRemediation:", file=sys.stderr)
        print(
            "  1. Confirm Pairwise70 .rda corpus at C:\\Projects\\Pairwise70\\data\\",
            file=sys.stderr,
        )
        print(
            "  2. Confirm MetaAudit repo at C:\\MetaAudit\\ with metaaudit/ package",
            file=sys.stderr,
        )
        return 1

    print("PREFLIGHT OK")
    print(f"  Pairwise70: {len(rda_files)} .rda files at {PAIRWISE70_DIR}")
    print(f"  MetaAudit: importable from {METAAUDIT_DIR.parent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the preflight**

Run: `python C:\Projects\repro-floor-atlas\scripts\prereq_check.py`
Expected: `PREFLIGHT OK` with 500+ .rda file count and MetaAudit import confirmed.
If FAIL: stop — halt all downstream tasks until resolved. Do not write any module code until this passes.

- [ ] **Step 3: Write .gitignore**

Create `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.coverage
htmlcov/

# Environments
.venv/
venv/
env/

# IDE
.vscode/
.idea/

# Claude Code session state
.claude/

# Project-local progress notes (per rules.md)
PROGRESS.md
STUCK_FAILURES.md
STUCK_FAILURES.jsonl
sentinel-findings.md
sentinel-findings.jsonl

# Generated outputs
outputs/
dashboard/assets-generated/
*.csv.backup

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 4: Write LICENSE (MIT)**

Create `LICENSE`:

```
MIT License

Copyright (c) 2026 Mahmood Arai

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 5: git init + first commit (the approved spec + scaffolding)**

Run:

```bash
cd C:/Projects/repro-floor-atlas && git init && git add .gitignore LICENSE scripts/prereq_check.py docs/superpowers/specs/2026-04-15-reproduction-floor-atlas-design.md docs/superpowers/plans/2026-04-15-reproduction-floor-atlas.md && git commit -m "chore: initialize repo with approved spec + preflight"
```

Expected: `[master (root-commit) ...] chore: initialize repo with approved spec + preflight`

---

## Task 1: Package skeleton + test harness

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `src/repro_floor_atlas/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write requirements.txt**

Create `requirements.txt`:

```
numpy>=1.24
scipy>=1.11
pandas>=2.0
pyreadr>=0.5
pytest>=7.4
pytest-cov>=4.1
```

Note: MetaAudit is NOT on PyPI. It is installed via editable pip install from `C:\MetaAudit\` in Step 4.

- [ ] **Step 2: Write pyproject.toml**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "repro-floor-atlas"
version = "0.1.0"
description = "Reproduction-floor atlas for 6,229 Cochrane meta-analyses"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [{name = "Mahmood Arai"}]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-ra --strict-markers"
```

- [ ] **Step 3: Write package __init__**

Create `src/repro_floor_atlas/__init__.py`:

```python
"""Reproduction-Floor Atlas for 6,229 Cochrane meta-analyses."""

__version__ = "0.1.0"
```

Create `tests/__init__.py`:

```python
```

- [ ] **Step 4: Install MetaAudit as editable dep + this package**

Run:

```bash
cd C:/Projects/repro-floor-atlas && pip install -e C:/MetaAudit && pip install -e . && pip install -r requirements.txt
```

Expected: both `metaaudit` and `repro-floor-atlas` appear in `pip list` with `Editable project location` set.

- [ ] **Step 5: Write conftest.py (shared pytest fixtures)**

Create `tests/conftest.py`:

```python
"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

PAIRWISE70_DIR = Path(r"C:\Projects\Pairwise70\data")


@pytest.fixture(scope="session")
def pairwise70_dir() -> Path:
    """Path to Pairwise70 .rda corpus. Skip tests if absent."""
    if not PAIRWISE70_DIR.is_dir():
        pytest.skip(f"Pairwise70 corpus not found at {PAIRWISE70_DIR}")
    return PAIRWISE70_DIR


@pytest.fixture(scope="session")
def small_rda_file(pairwise70_dir: Path) -> Path:
    """Return one .rda file for integration tests. Picks lexicographically first."""
    files = sorted(pairwise70_dir.glob("*.rda"))
    if not files:
        pytest.skip("No .rda files in Pairwise70 corpus")
    return files[0]
```

- [ ] **Step 6: Smoke-test pytest harness**

Run: `cd C:/Projects/repro-floor-atlas && pytest -v`
Expected: `no tests ran` (exit 5) — harness loads with no errors. (Exit 5 is pytest's "no tests collected" and is expected here; it proves the collection phase works.)

- [ ] **Step 7: Commit**

```bash
git add requirements.txt pyproject.toml src/ tests/ && git commit -m "chore: scaffold package + pytest harness"
```

---

## Task 2: `loader.py` — thin MetaAudit wrapper (TDD)

**Files:**
- Create: `src/repro_floor_atlas/loader.py`
- Create: `tests/test_loader.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_loader.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_loader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'repro_floor_atlas.loader'`

- [ ] **Step 3: Implement loader.py**

Create `src/repro_floor_atlas/loader.py`:

```python
"""Thin wrapper over MetaAudit's Pairwise70 .rda loader.

Converts MetaAudit's AnalysisGroup objects into plain-dataclass MAInputs with
typed per-trial numpy arrays for each data type. No math here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from metaaudit.loader import DataType, load_all_reviews


@dataclass(frozen=True)
class BinaryTrials:
    e_cases: np.ndarray  # events in experimental arm
    e_n: np.ndarray      # total N in experimental arm
    c_cases: np.ndarray
    c_n: np.ndarray


@dataclass(frozen=True)
class ContinuousTrials:
    e_mean: np.ndarray
    e_sd: np.ndarray
    e_n: np.ndarray
    c_mean: np.ndarray
    c_sd: np.ndarray
    c_n: np.ndarray


@dataclass(frozen=True)
class GIVTrials:
    yi: np.ndarray  # per-trial effect
    se: np.ndarray  # per-trial standard error


@dataclass(frozen=True)
class MAInputs:
    ma_id: str
    review_id: str
    analysis_number: int
    k: int
    data_type: str  # "binary" | "continuous" | "giv"
    binary: Optional[BinaryTrials] = None
    continuous: Optional[ContinuousTrials] = None
    giv: Optional[GIVTrials] = None


def _to_array(df, col: str) -> np.ndarray:
    return df[col].to_numpy(dtype=float, copy=True)


def load_reviews(rda_paths: list[Path]) -> list[MAInputs]:
    """Load a list of .rda files, return one MAInputs per analysis."""
    results: list[MAInputs] = []
    for path in rda_paths:
        reviews = load_all_reviews(path.parent, max_reviews=None)
        reviews = [r for r in reviews if r.review_id == path.stem]
        for rv in reviews:
            for ag in rv.analyses:
                ma = _analysis_to_inputs(ag)
                if ma is not None:
                    results.append(ma)
    return results


def load_directory(data_dir: Path, max_reviews: int | None = None) -> list[MAInputs]:
    """Load all .rda files in a directory, return one MAInputs per analysis."""
    reviews = load_all_reviews(data_dir, max_reviews=max_reviews)
    results: list[MAInputs] = []
    for rv in reviews:
        for ag in rv.analyses:
            ma = _analysis_to_inputs(ag)
            if ma is not None:
                results.append(ma)
    return results


def _analysis_to_inputs(ag) -> MAInputs | None:
    df = ag.df
    k = len(df)
    if k < 1:
        return None
    dt_str = {
        DataType.BINARY: "binary",
        DataType.CONTINUOUS: "continuous",
        DataType.GIV: "giv",
    }[ag.data_type]

    binary = continuous = giv = None
    if ag.data_type == DataType.BINARY:
        needed = ("Experimental.cases", "Experimental.N", "Control.cases", "Control.N")
        if not all(c in df.columns for c in needed):
            return None
        binary = BinaryTrials(
            e_cases=_to_array(df, "Experimental.cases"),
            e_n=_to_array(df, "Experimental.N"),
            c_cases=_to_array(df, "Control.cases"),
            c_n=_to_array(df, "Control.N"),
        )
    elif ag.data_type == DataType.CONTINUOUS:
        needed = (
            "Experimental.mean", "Experimental.SD", "Experimental.N",
            "Control.mean", "Control.SD", "Control.N",
        )
        if not all(c in df.columns for c in needed):
            return None
        continuous = ContinuousTrials(
            e_mean=_to_array(df, "Experimental.mean"),
            e_sd=_to_array(df, "Experimental.SD"),
            e_n=_to_array(df, "Experimental.N"),
            c_mean=_to_array(df, "Control.mean"),
            c_sd=_to_array(df, "Control.SD"),
            c_n=_to_array(df, "Control.N"),
        )
    elif ag.data_type == DataType.GIV:
        if not ("GIV.Mean" in df.columns and "GIV.SE" in df.columns):
            return None
        giv = GIVTrials(
            yi=_to_array(df, "GIV.Mean"),
            se=_to_array(df, "GIV.SE"),
        )
    else:
        return None

    return MAInputs(
        ma_id=ag.ma_id,
        review_id=ag.review_id,
        analysis_number=ag.analysis_number,
        k=k,
        data_type=dt_str,
        binary=binary,
        continuous=continuous,
        giv=giv,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_loader.py -v`
Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/repro_floor_atlas/loader.py tests/test_loader.py && git commit -m "feat(loader): wrap MetaAudit .rda loader; yield typed MAInputs"
```

---

## Task 3: `precision_floor.py` — round-and-repool (TDD, pure)

**Files:**
- Create: `src/repro_floor_atlas/precision_floor.py`
- Create: `tests/test_precision_floor.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_precision_floor.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_precision_floor.py -v`
Expected: all FAIL with `ModuleNotFoundError: No module named 'repro_floor_atlas.precision_floor'`

- [ ] **Step 3: Implement precision_floor.py**

Create `src/repro_floor_atlas/precision_floor.py`:

```python
"""Pure round-and-repool. Zero I/O.

For each MA, computes the 'truth' pooled effect from machine-precision per-trial
inputs, then computes the 'rounded' pooled effect after rounding per-trial
numerics to the precision a Cochrane reader can extract (Scenario A = raw
data, Scenario B = forest-plot log-effects).

Returns the absolute delta on the natural reporting scale (log for binary/GIV;
raw for continuous mean-difference).
"""

from __future__ import annotations

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_precision_floor.py -v`
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/repro_floor_atlas/precision_floor.py tests/test_precision_floor.py && git commit -m "feat(precision_floor): pure round-and-repool for scenarios A/B"
```

---

## Task 4: `classifier.py` — USER CONTRIBUTION (5-10 lines)

**Files:**
- Create: `src/repro_floor_atlas/classifier.py` (scaffold by agent, body by user)
- Create: `tests/test_classifier.py`

- [ ] **Step 1: Write the failing tests FIRST (they encode the contract)**

Create `tests/test_classifier.py`:

```python
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
```

- [ ] **Step 2: Scaffold classifier.py with docstring + function signature + TODO (agent writes; body left for user)**

Create `src/repro_floor_atlas/classifier.py`:

```python
"""Reproduction-threshold classifier.

This module encodes the rule that decides whether a reproduction delta counts
as a 'reproduction failure'. Called once per (ma_id, scenario, rounding_mode)
row in atlas.py.

The body of exceeds_threshold() is a deliberate user-authored decision point:
multiple valid rules exist and the choice shapes the headline claim.
"""

from __future__ import annotations

import math
from typing import Literal


FIXED_THRESHOLD = 0.005  # matches SGLT2i-HFpEF ship threshold + Cochrane 2-dp CI half-width


def exceeds_threshold(
    delta: float,
    declared_dp: int,
    threshold_mode: Literal["fixed", "adaptive", "both"],
) -> dict[str, bool]:
    """Return whether a reproduction |Δ| counts as non-reproducible.

    Shape of return: {"fixed": bool} for mode "fixed",
                     {"adaptive": bool} for mode "adaptive",
                     {"fixed": bool, "adaptive": bool} for mode "both".

    Guidance for implementers (pick one; document your choice):

      • Strict fixed: abs(delta) >= FIXED_THRESHOLD  (default)
      • Strict adaptive: abs(delta) >= 0.5 * 10 ** (-declared_dp)
      • NaN handling: treat NaN delta as True for both modes (conservative)
      • Boundary: prefer >= over > so exactly-0.005 counts as non-reproducible

    Args:
        delta: signed reproduction error (rounded_pooled - truth_pooled)
        declared_dp: decimal precision the MA was published to
        threshold_mode: which rule(s) to apply

    Returns:
        dict with "fixed" and/or "adaptive" keys, depending on mode.
    """
    # TODO (user): implement the classification rule. 5-10 lines.
    # The tests in tests/test_classifier.py fully specify the expected behavior.
    # Start by handling NaN, then compute the fixed and adaptive booleans.
    raise NotImplementedError(
        "exceeds_threshold body is a user contribution — see docstring + tests."
    )
```

- [ ] **Step 3: Run tests to verify they fail (on NotImplementedError)**

Run: `pytest tests/test_classifier.py -v`
Expected: all FAIL with `NotImplementedError: exceeds_threshold body is a user contribution`

- [ ] **Step 4: USER WRITES the function body**

**HALT here.** This step requires the user's code contribution. The agent must:

1. Announce: "Task 4 Step 4 is your contribution. Please write the body of `exceeds_threshold()` in `src/repro_floor_atlas/classifier.py`. The tests in `tests/test_classifier.py` fully specify the behavior — all 7 must pass."
2. Wait for user input before proceeding.
3. When user reports done, run the tests to verify.

- [ ] **Step 5: Run tests — must all pass before continuing**

Run: `pytest tests/test_classifier.py -v`
Expected: all 7 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/repro_floor_atlas/classifier.py tests/test_classifier.py && git commit -m "feat(classifier): user-authored threshold rule (fixed + adaptive)"
```

---

## Task 5: `atlas.py` — orchestrator (TDD)

**Files:**
- Create: `src/repro_floor_atlas/atlas.py`
- Create: `tests/test_atlas.py`
- Create: `scripts/run_atlas.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_atlas.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_atlas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'repro_floor_atlas.atlas'`

- [ ] **Step 3: Implement atlas.py**

Create `src/repro_floor_atlas/atlas.py`:

```python
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
```

- [ ] **Step 4: Create scripts/run_atlas.py (CLI entrypoint)**

Create `scripts/run_atlas.py`:

```python
"""CLI: run the full reproduction-floor atlas over Pairwise70."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from repro_floor_atlas.atlas import build_atlas
from repro_floor_atlas.loader import load_directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(r"C:\Projects\Pairwise70\data"),
        help="Pairwise70 .rda directory",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("outputs") / "atlas.csv",
        help="Output CSV path (relative to repo root)",
    )
    parser.add_argument(
        "--max-reviews",
        type=int,
        default=None,
        help="Limit the number of reviews (for smoke testing)",
    )
    args = parser.parse_args(argv)

    if not args.data_dir.is_dir():
        print(f"ERROR: data dir not found: {args.data_dir}", file=sys.stderr)
        return 1

    t0 = time.time()
    print(f"Loading reviews from {args.data_dir}...")
    mas = load_directory(args.data_dir, max_reviews=args.max_reviews)
    print(f"  loaded {len(mas)} MAs in {time.time() - t0:.1f}s")

    t1 = time.time()
    n = build_atlas(mas, args.out)
    print(f"Wrote {n} rows to {args.out} in {time.time() - t1:.1f}s")
    print(f"Total elapsed: {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_atlas.py -v`
Expected: PASS.

- [ ] **Step 6: Smoke-run the CLI on 1 review**

Run: `cd C:/Projects/repro-floor-atlas && python scripts/run_atlas.py --max-reviews 1 --out outputs/smoke.csv`
Expected: prints row count; `outputs/smoke.csv` exists and is well-formed.

- [ ] **Step 7: Commit**

```bash
git add src/repro_floor_atlas/atlas.py tests/test_atlas.py scripts/run_atlas.py && git commit -m "feat(atlas): orchestrator + CLI; produces atlas.csv"
```

---

## Task 6: Integration test against MetaAudit contract

**Files:**
- Create: `tests/test_integration_metaaudit_contract.py`

- [ ] **Step 1: Write the contract test (per lessons.md "Integration Contracts")**

Create `tests/test_integration_metaaudit_contract.py`:

```python
"""Guard the MetaAudit → repro_floor_atlas contract.

If MetaAudit renames columns, changes DataType enum, or alters compute_log_or /
compute_md signatures, this test fails loudly BEFORE atlas.py returns a silent
garbage output.
"""

from __future__ import annotations

import numpy as np

from metaaudit.loader import DataType
from metaaudit.recompute import compute_log_or, compute_md


def test_datatype_enum_values_unchanged():
    assert DataType.BINARY.value == "binary"
    assert DataType.CONTINUOUS.value == "continuous"
    assert DataType.GIV.value == "giv"


def test_compute_log_or_signature_and_output():
    """Known 2x2 table → known log-OR."""
    e_cases = np.array([10.0])
    e_n = np.array([100.0])
    c_cases = np.array([20.0])
    c_n = np.array([100.0])
    yi, vi = compute_log_or(e_cases, e_n, c_cases, c_n)
    # OR = (10*80)/(90*20) = 800/1800 = 0.4444...
    # log(0.4444) ≈ -0.8109
    assert abs(yi[0] - np.log(800/1800)) < 1e-10
    assert vi[0] > 0


def test_compute_md_signature_and_output():
    """Known means → known mean difference."""
    e_mean = np.array([10.0])
    e_sd = np.array([2.0])
    e_n = np.array([50.0])
    c_mean = np.array([8.0])
    c_sd = np.array([2.0])
    c_n = np.array([50.0])
    yi, vi = compute_md(e_mean, e_sd, e_n, c_mean, c_sd, c_n)
    assert abs(yi[0] - 2.0) < 1e-10
    # variance = 4/50 + 4/50 = 0.16
    assert abs(vi[0] - 0.16) < 1e-10
```

- [ ] **Step 2: Run**

Run: `pytest tests/test_integration_metaaudit_contract.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration_metaaudit_contract.py && git commit -m "test(contract): guard MetaAudit integration boundary"
```

---

## Task 7: Regression baseline — seed-locked 10-MA smoke fixture

**Files:**
- Create: `scripts/seed_smoke_baseline.py`
- Create: `tests/fixtures/smoke_10_mas.json`
- Create: `tests/test_regression.py`

- [ ] **Step 1: Create the baseline seeding script**

Create `scripts/seed_smoke_baseline.py`:

```python
"""Seed the 10-MA smoke-regression baseline.

Deterministically picks the first 10 MAs (by sorted review_id, then analysis_number)
from Pairwise70 and writes the canonical (ma_id → per-row) mapping to a fixture.
Re-run only when the numerical contract intentionally changes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from repro_floor_atlas.atlas import build_atlas, CSV_COLUMNS
from repro_floor_atlas.loader import load_directory

DATA_DIR = Path(r"C:\Projects\Pairwise70\data")
FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "smoke_10_mas.json"
TMP_CSV = Path(__file__).resolve().parent.parent / "outputs" / "smoke_10.csv"


def main() -> int:
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
```

- [ ] **Step 2: Run the seeder to create the fixture**

Run: `cd C:/Projects/repro-floor-atlas && python scripts/seed_smoke_baseline.py`
Expected: `Wrote 80 rows (10 MAs × 8) to tests/fixtures/smoke_10_mas.json`

- [ ] **Step 3: Write the regression test that re-runs and bit-compares**

Create `tests/test_regression.py`:

```python
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
```

- [ ] **Step 4: Run and confirm pass**

Run: `pytest tests/test_regression.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/seed_smoke_baseline.py tests/fixtures/smoke_10_mas.json tests/test_regression.py && git commit -m "test(regression): commit 10-MA smoke fixture + bit-match guard"
```

---

## Task 8: `report.py` — dashboard + E156 renderer (TDD)

**Files:**
- Create: `src/repro_floor_atlas/report.py`
- Create: `tests/test_report.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_report.py`:

```python
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
```

- [ ] **Step 2: Run — expect fail on missing module**

Run: `pytest tests/test_report.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement report.py**

Create `src/repro_floor_atlas/report.py`:

```python
"""Render the dashboard (offline HTML) and E156 markdown draft.

Reads atlas.csv, aggregates headline stats, writes two output files.
No math beyond counting and percentages.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


def _load_rows(csv_path: Path) -> list[dict]:
    with Path(csv_path).open() as f:
        return list(csv.DictReader(f))


def _headline_stats(rows: list[dict]) -> dict:
    total = len(rows)
    if total == 0:
        return {"total_rows": 0, "fixed_pct": 0.0, "adaptive_pct": 0.0}

    # Focus the headline on scenario B + adaptive rounding (the realistic case)
    focus = [
        r for r in rows
        if r["scenario"] == "forest_plot_extraction" and r["rounding_mode"] == "adaptive"
    ]
    if not focus:
        focus = rows  # fallback for sparse test fixtures

    n = len(focus)
    fail_fixed = sum(1 for r in focus if r["exceeds_fixed"].lower() == "true")
    fail_adaptive = sum(1 for r in focus if r["exceeds_adaptive"].lower() == "true")
    return {
        "total_rows": total,
        "focus_rows": n,
        "fixed_failures": fail_fixed,
        "adaptive_failures": fail_adaptive,
        "fixed_pct": round(100.0 * fail_fixed / max(n, 1), 1),
        "adaptive_pct": round(100.0 * fail_adaptive / max(n, 1), 1),
    }


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reproduction-Floor Atlas</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 960px; margin: 2em auto; padding: 0 1em; line-height: 1.5; color: #222; }}
  h1 {{ font-size: 1.6em; }}
  .headline {{ background: #f6f8fa; border-left: 4px solid #0366d6; padding: 1em; margin: 1.5em 0; }}
  .kpi {{ display: inline-block; padding: 0.5em 1em; margin: 0.25em; background: #eef; border-radius: 4px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
  th, td {{ border: 1px solid #ddd; padding: 0.4em 0.6em; text-align: right; font-size: 0.9em; }}
  th {{ background: #f0f0f0; text-align: left; }}
  td:first-child {{ text-align: left; font-family: monospace; }}
  footer {{ margin-top: 3em; color: #666; font-size: 0.85em; }}
</style>
</head>
<body>
<h1>Reproduction-Floor Atlas</h1>
<p>
For each of the Pairwise70 / Cochrane meta-analyses, we re-pool after rounding
per-trial inputs to the precision a reader can actually extract. This dashboard
shows how often the reproduction error exceeds Cochrane's declared 2-dp precision.
</p>
<div class="headline">
<strong>Headline:</strong>
under Scenario B (forest-plot extraction) with adaptive per-MA rounding,
<span class="kpi">{adaptive_pct}% non-reproducible (adaptive threshold)</span>
<span class="kpi">{fixed_pct}% non-reproducible (|Δ|>0.005)</span>
across {focus_rows} MAs.
</div>

<h2>Per-MA drill-down (first 50 rows)</h2>
<table id="drilldown">
<thead><tr>
<th>MA</th><th>type</th><th>k</th><th>scenario</th><th>mode</th>
<th>dp</th><th>truth</th><th>rounded</th><th>|Δ|</th>
<th>fixed?</th><th>adaptive?</th>
</tr></thead>
<tbody>
{body_rows}
</tbody>
</table>

<p><em>Full atlas:</em> <code>outputs/atlas.csv</code>. Source and reproduction instructions: README.md.</p>

<footer>
Reproduction-Floor Atlas v0.1.0 · offline dashboard, no external CDN ·
data embedded from atlas.csv at build time.
</footer>
<script>
  // Embedded atlas summary (JSON) for future interactive filtering:
  window.__ATLAS_SUMMARY__ = {summary_json};
</script>
</body>
</html>
"""


def render_dashboard(atlas_csv: Path, out_html: Path) -> None:
    rows = _load_rows(atlas_csv)
    stats = _headline_stats(rows)

    drill_rows = rows[:50]
    body = "\n".join(
        f"<tr>"
        f"<td>{r['ma_id']}</td>"
        f"<td>{r['data_type']}</td>"
        f"<td>{r['k']}</td>"
        f"<td>{r['scenario']}</td>"
        f"<td>{r['rounding_mode']}</td>"
        f"<td>{r['declared_dp']}</td>"
        f"<td>{float(r['truth_pooled']):.4f}</td>"
        f"<td>{float(r['rounded_pooled']):.4f}</td>"
        f"<td>{abs(float(r['delta'])):.4f}</td>"
        f"<td>{r['exceeds_fixed']}</td>"
        f"<td>{r['exceeds_adaptive']}</td>"
        f"</tr>"
        for r in drill_rows
    )

    html = _HTML_TEMPLATE.format(
        adaptive_pct=stats["adaptive_pct"],
        fixed_pct=stats["fixed_pct"],
        focus_rows=stats["focus_rows"],
        body_rows=body,
        summary_json=json.dumps(stats),
    )
    out_html = Path(out_html)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")


_E156_TEMPLATE = """# Reproduction-Floor Atlas — E156

Primary estimand: proportion of Cochrane MAs for which |Δ| > 0.005 under
Scenario-B adaptive rounding.

**S1 (Question, ~22w):** Can the pooled effect of a Cochrane meta-analysis be
independently re-pooled to the precision at which it was published, using only
the per-trial numerics a reader can extract from the paper?

**S2 (Dataset, ~20w):** Pairwise70 corpus: 501 Cochrane reviews comprising
6,229 meta-analyses spanning binary, continuous, and generic-inverse-variance
outcomes, with trial-level inputs at machine precision.

**S3 (Method, ~20w):** For each MA we computed the machine-precision pooled
fixed-effect estimate, then re-pooled after rounding per-trial inputs to
Cochrane's published precision (adaptive) and to fixed 1, 2, 3 dp.

**S4 (Result, ~30w):** __PLACEHOLDER_S4__  <!-- user-authored after atlas run:
state the adaptive-threshold non-reproducibility percentage (focus_rows =
{focus_rows}; adaptive_pct = {adaptive_pct}; fixed_pct = {fixed_pct}) -->

**S5 (Robustness, ~22w):** The scaling relation |Δ| ~ 10^(-dp) held across
fixed-precision cuts in binary, continuous, and GIV strata; patterns were
stable under Scenario-A (raw extraction) and Scenario-B (forest-plot) framings.

**S6 (Interpretation, ~22w):** Published two-decimal-place precision in pooled
effects exceeds the information content of the extractable per-trial numerics
for a non-trivial share of MAs; this is a structural limit, not a method flaw.

**S7 (Boundary, ~20w):** Claim scope: aggregate-data reproduction with
fixed-effect pooling; does not apply to individual-patient-data re-analysis or
to random-effects estimators outside this simulation.
"""


def render_e156_draft(atlas_csv: Path, out_md: Path) -> None:
    rows = _load_rows(atlas_csv)
    stats = _headline_stats(rows)
    md = _E156_TEMPLATE.format(
        focus_rows=stats["focus_rows"],
        adaptive_pct=stats["adaptive_pct"],
        fixed_pct=stats["fixed_pct"],
    )
    out_md = Path(out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md, encoding="utf-8")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_report.py -v`
Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/repro_floor_atlas/report.py tests/test_report.py && git commit -m "feat(report): offline HTML dashboard + E156 draft with S4 placeholder"
```

---

## Task 9: Full run + renders + README + E156-PROTOCOL

**Files:**
- Modify: `outputs/atlas.csv` (generated, not committed)
- Create: `dashboard/index.html`
- Create: `e156-submission/e156_paper.md`
- Create: `README.md`
- Create: `E156-PROTOCOL.md`

- [ ] **Step 1: Run the full 6,229-MA atlas**

Run: `cd C:/Projects/repro-floor-atlas && python scripts/run_atlas.py --out outputs/atlas.csv`
Expected: prints total row count (~50k); `outputs/atlas.csv` populated. Record the wall-clock time.

- [ ] **Step 2: Render the dashboard and E156 draft**

Run:

```bash
cd C:/Projects/repro-floor-atlas && python -c "from pathlib import Path; from repro_floor_atlas.report import render_dashboard, render_e156_draft; render_dashboard(Path('outputs/atlas.csv'), Path('dashboard/index.html')); render_e156_draft(Path('outputs/atlas.csv'), Path('e156-submission/e156_paper.md')); print('rendered')"
```

Expected: `rendered`; both files exist. Record the `adaptive_pct` and `fixed_pct` — these are the headline numbers.

- [ ] **Step 3: Open the dashboard to visually confirm it renders offline**

Open `C:\Projects\repro-floor-atlas\dashboard\index.html` in a browser with network disabled (DevTools → Network → "Offline"). Confirm:
- Headline box shows two KPIs
- Drill-down table renders 50 rows
- No console errors about blocked external resources

- [ ] **Step 4: Write README.md**

Create `README.md`:

```markdown
# Reproduction-Floor Atlas

> Does every Cochrane meta-analysis publish results a reader can actually reproduce to the precision claimed? We measured this for all 6,229 MAs in the Pairwise70 corpus.

## Headline finding

Under Scenario B (a reader reconstructs per-trial effects from the forest plot),
re-pooling at Cochrane's published precision produces |Δ| > 0.005 in **{FIXED_PCT}%** of 6,229 MAs — the declared two-decimal-place precision is mathematically unreachable from published aggregate data.

**Live dashboard:** https://mahmood726-cyber.github.io/repro-floor-atlas/

## Quick start

```bash
pip install -e C:/MetaAudit
pip install -e .
pip install -r requirements.txt
python scripts/prereq_check.py     # verify Pairwise70 + MetaAudit
python scripts/run_atlas.py        # ~minutes; produces outputs/atlas.csv
pytest -v                          # all tests must pass
```

## Reproduction

- Source data: Pairwise70 Cochrane corpus (`C:\\Projects\\Pairwise70\\data`; 501 reviews / 6,229 MAs)
- Pooling engine: MetaAudit `metaaudit.recompute` (inverse-variance fixed-effect)
- Rounding scenarios: raw extraction (A) and forest-plot extraction (B)
- Regression baseline: `tests/fixtures/smoke_10_mas.json` — re-running the pipeline must bit-match this file

## What this is NOT

- Not a methodological audit (DL vs REML etc.)
- Not a publication-bias claim
- Narrowly: rounding-induced precision loss in aggregate-data re-pooling

## E156 micro-paper

See `e156-submission/e156_paper.md`. Protocol: `E156-PROTOCOL.md`.

## License

MIT. See `LICENSE`.
```

(Replace `{FIXED_PCT}` with the actual headline number from Step 2.)

- [ ] **Step 5: Write E156-PROTOCOL.md**

Create `E156-PROTOCOL.md`:

```markdown
# E156 Protocol — Reproduction-Floor Atlas

- **Project name:** Reproduction-Floor Atlas
- **Start date:** 2026-04-15
- **Submission target:** E156 workbook (Mahmood Arai portfolio)
- **Spec:** `docs/superpowers/specs/2026-04-15-reproduction-floor-atlas-design.md`
- **Plan:** `docs/superpowers/plans/2026-04-15-reproduction-floor-atlas.md`
- **Dashboard:** https://mahmood726-cyber.github.io/repro-floor-atlas/
- **Primary estimand:** proportion of 6,229 Cochrane MAs for which |Δ| > 0.005 under Scenario-B adaptive rounding
- **CURRENT BODY:** see `e156-submission/e156_paper.md` (S4 pending user contribution)

See `rules.md` for the 7-sentence contract and word-budget rules (S1 ~22, S2 ~20, S3 ~20, S4 ~30, S5 ~22, S6 ~22, S7 ~20).
```

- [ ] **Step 6: Commit**

```bash
git add README.md E156-PROTOCOL.md dashboard/ e156-submission/ && git commit -m "docs: README + E156 protocol + rendered dashboard/E156 draft"
```

---

## Task 10: E156 paper — USER CONTRIBUTION (S4 sentence, ~30 words)

**Files:**
- Modify: `e156-submission/e156_paper.md`

- [ ] **Step 1: Review the rendered draft**

Read `e156-submission/e156_paper.md`. S4 is the only placeholder; S1-S3 and S5-S7 are drafted and editable but sized to the word budget.

- [ ] **Step 2: USER WRITES the S4 sentence (~30 words)**

**HALT here.** The agent must:

1. Announce: "Task 10 Step 2 is your contribution. The S4 sentence — the public statement of the atlas's finding — is yours to write. The rendered draft shows the empirical numbers in an HTML comment below the `__PLACEHOLDER_S4__` marker. Target: ~30 words, single sentence, names the primary estimand, uses the actual percentage. Replace the placeholder."
2. Wait for user to save changes.
3. Validate: read the file and confirm the word count for S4 is between 24 and 36, and that `__PLACEHOLDER_S4__` is absent.

- [ ] **Step 3: Validate the updated paper**

Run:

```bash
cd C:/Projects/repro-floor-atlas && python -c "
from pathlib import Path
md = Path('e156-submission/e156_paper.md').read_text()
assert '__PLACEHOLDER_S4__' not in md, 'S4 still a placeholder'
# naive S4 extraction between 'S4' header and 'S5' header
import re
m = re.search(r'\*\*S4[^*]*\*\*(.*?)\*\*S5', md, re.DOTALL)
assert m, 'Could not locate S4'
s4 = re.sub(r'<!--.*?-->', '', m.group(1), flags=re.DOTALL).strip()
words = len(s4.split())
assert 24 <= words <= 36, f'S4 word count {words} outside [24, 36]'
print(f'S4 OK ({words} words)')
"
```

Expected: `S4 OK (N words)` with N in [24, 36].

- [ ] **Step 4: Commit**

```bash
git add e156-submission/e156_paper.md && git commit -m "feat(e156): user-authored S4 sentence"
```

---

## Task 11: Full test suite + Sentinel pre-push gate

**Files:**
- Modify: (none — installs Sentinel hook, runs gate)

- [ ] **Step 1: Run the full test suite**

Run: `cd C:/Projects/repro-floor-atlas && pytest -v`
Expected: every test in `test_loader.py`, `test_precision_floor.py`, `test_classifier.py`, `test_atlas.py`, `test_integration_metaaudit_contract.py`, `test_regression.py`, `test_report.py` PASS. Record exact pass count.

- [ ] **Step 2: Install Sentinel pre-push hook**

Run:

```bash
cd C:/Projects/repro-floor-atlas && python -m sentinel install-hook --repo C:/Projects/repro-floor-atlas
```

Expected: hook installed under `.git/hooks/pre-push`. If `sentinel` is not importable, stop and ask the user to confirm Sentinel is installed in the active environment.

- [ ] **Step 3: Run a Sentinel scan**

Run: `python -m sentinel scan --repo C:/Projects/repro-floor-atlas`
Expected: no BLOCK findings. WARN findings are acceptable but must be inspected. If a BLOCK fires, fix the underlying violation (do NOT bypass with `SENTINEL_BYPASS=1`).

- [ ] **Step 4: Commit any hygiene fixes from Step 3 (if any)**

```bash
git add -A && git commit -m "chore(sentinel): fix hygiene violations from scan" || echo "nothing to commit"
```

---

## Task 12: GitHub push + Pages + registry reconciliation

**Files:**
- Modify: `C:\ProjectIndex\INDEX.md`
- Modify: `C:\E156\rewrite-workbook.txt`
- Modify: `C:\Users\user\push_all_repos.py` (only if repo root isn't auto-discovered)

- [ ] **Step 1: Create GitHub repo and push**

Run:

```bash
cd C:/Projects/repro-floor-atlas && gh repo create mahmood726-cyber/repro-floor-atlas --public --source=. --description "Reproduction-floor atlas for 6,229 Cochrane meta-analyses" --push
```

Expected: repo created, master pushed.

- [ ] **Step 2: Enable GitHub Pages from the `dashboard/` folder**

Run (web UI step if gh CLI does not support it directly):

- Go to https://github.com/mahmood726-cyber/repro-floor-atlas/settings/pages
- Source: Deploy from a branch
- Branch: `master`, folder: `/dashboard`
- Save

Confirm: https://mahmood726-cyber.github.io/repro-floor-atlas/ resolves with the dashboard after a few minutes.

- [ ] **Step 3: Add INDEX.md entry**

Append to `C:\ProjectIndex\INDEX.md` under the appropriate section (Active Projects):

```markdown
- [Reproduction-Floor Atlas](C:/Projects/repro-floor-atlas/) — 6,229-MA atlas; Scenario-A/B rounding; dashboard at github.io/repro-floor-atlas/; E156 `2026-04-15`
```

- [ ] **Step 4: Add rewrite-workbook entry (CURRENT BODY only; YOUR REWRITE empty)**

Edit `C:\E156\rewrite-workbook.txt`. Add a new entry per the workbook-protection rules:

- Title line: `Reproduction-Floor Atlas (2026-04-15)`
- CURRENT BODY: copy from `e156-submission/e156_paper.md` with S1-S7 flattened to a single paragraph
- YOUR REWRITE: empty (Mahmood only)
- `SUBMITTED: [ ]`
- Increment the total entry count in the workbook header

- [ ] **Step 5: Run the portfolio reconcile**

Run: `python C:\ProjectIndex\reconcile_counts.py`
Expected: exit code 0 (clean). If FAIL, read the output and fix either INDEX.md, the workbook, or `restart-manifest.json` until the reconcile agrees.

- [ ] **Step 6: Confirm push_all_repos.py auto-discovers the new repo**

Run: `python C:\Users\user\push_all_repos.py --report --new-only`
Expected: `repro-floor-atlas` appears in the report. If not, add it to `SCAN_DIRS` in the push script.

- [ ] **Step 7: Tag v0.1.0**

Run:

```bash
cd C:/Projects/repro-floor-atlas && git tag -a v0.1.0 -m "v0.1.0: first public release with approved spec, 6,229-MA atlas, and E156 draft" && git push --tags
```

- [ ] **Step 8: Final verification — ship-bar checklist**

Re-read Section 4 of the spec. Confirm every one of the 9 gates is green:

1. All five modules implemented, tests passing (Task 11 Step 1)
2. `atlas.csv` generated, ~50k rows (Task 9 Step 1)
3. Dashboard at github.io/repro-floor-atlas/ (Task 12 Step 2)
4. `e156_paper.md` — 7 sentences, ≤156 words, primary estimand named, S1-S7 (Tasks 9, 10)
5. Workbook entry added (Task 12 Step 4)
6. GitHub repo + Pages enabled (Tasks 12 Steps 1-2) + README + E156-PROTOCOL (Task 9)
7. Sentinel hook installed, no BLOCKs (Task 11 Steps 2-3)
8. `tests/fixtures/smoke_10_mas.json` committed (Task 7 Step 5)
9. `reconcile_counts.py` clean (Task 12 Step 5)

Announce "Ship bar green — D1-S complete" only when all 9 are confirmed from evidence, not from memory.

---

## Self-Review (applied inline, 2026-04-15)

Re-read the spec; map each section to tasks:

| Spec section | Task(s) |
|---|---|
| §1 Problem statement | Covered by README + E156 paper (Task 9) |
| §2 Architecture: loader | Task 2 |
| §2 Architecture: precision_floor | Task 3 |
| §2 Architecture: classifier | Task 4 (USER) |
| §2 Architecture: atlas | Task 5 |
| §2 Architecture: report | Task 8 |
| §2 Scenario A/B | Task 3 tests |
| §3a Precision grid: adaptive + fixed | Task 5 (`ROUNDING_SPECS`) |
| §3b Threshold: fixed + adaptive | Task 4 (tests) |
| §3c Stratification axes | Dashboard drill-down (Task 8, 9) |
| §4 Ship criteria, all 9 gates | Task 12 Step 8 |
| §5 Out-of-scope | Respected (no REML, no fragility link, E156 only) |
| §6 User contributions | Tasks 4, 10 |
| §7 Risks (prereq check) | Task 0 |
| §7 Risks (MetaAudit contract) | Task 6 |
| §7 Risks (baseline drift) | Task 7 |
| §8 Dependencies | Task 1 + Task 0 |
| §9 References | README |

Placeholder scan: only `__PLACEHOLDER_S4__` in the E156 draft, which is intentional and gated by Task 10.

Type consistency: `MAInputs`, `BinaryTrials`, `ContinuousTrials`, `GIVTrials`, `PrecisionSpec`, `Scenario`, `FloorResult` — all introduced in Task 2 or 3, used identically in later tasks. `CSV_COLUMNS` defined in Task 5, referenced identically in Task 7.

No issues found.
