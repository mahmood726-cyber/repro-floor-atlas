# Reproduction-Floor Atlas — Design Doc

- **Author:** Mahmood Arai (mahmood726-cyber)
- **Date:** 2026-04-15
- **Size classification:** Size S (1–2 sessions, E156 + dashboard only; no manuscript)
- **Status:** Approved (brainstorming), pending implementation plan

## 1. Problem statement & headline claim

Reproduction studies of meta-analyses typically ask *"can we re-run the analysis?"* With trial-level data available, the answer is trivially yes. The non-trivial question is: **given what a reader can actually extract from a published paper, is the claimed precision of the pooled effect achievable?**

Cochrane reviews publish per-trial numerics at finite precision (integer counts for binary, typically 1 dp for continuous means/SDs, 2 dp for log-effects on forest plots). A precision-sweep experiment on 2-trial synthetic pools established that rounding-induced error in the pooled estimate scales as `~10^(-dp)`. The SGLT2i-HFpEF ma-workbench demo hit that floor empirically (HR 0.81 vs Vaduganathan 0.80, `|Δ|=0.007`, above the `0.005` ship threshold).

**Headline claim to ship:** *"For X% of 6,229 Cochrane meta-analyses, re-pooling from per-trial numerics rounded to Cochrane's published precision produces a pooled-effect error exceeding the declared 2-dp precision — the published result is not independently reproducible to the precision claimed from aggregate data alone."*

**What this is NOT:**
- Not a claim about methodological error (DL vs REML, etc.)
- Not a claim about publication bias or P-hacking
- Not a general-purpose reproducibility audit in the Ioannidis sense
- Narrowly about **rounding-induced precision loss in aggregate-data re-pooling**

## 2. Architecture & components

### Location

New standalone repo at `C:\Projects\repro-floor-atlas\`. Imports MetaAudit (`C:\MetaAudit\metaaudit`) as an installed package dependency via editable install or path manipulation. Standalone (not a submodule of MetaAudit) because:

- MetaAudit is mid-BMJ submission; a new E156 must not contaminate its tree.
- Standalone gets its own Sentinel hook, own tests, own E156 workbook entry.
- Cleaner portfolio bookkeeping (separate INDEX.md row, separate `push_all_repos.py` entry).

### Pipeline

```
Pairwise70 .rda files (501 reviews, 6,229 MAs, C:\Projects\Pairwise70\data\)
    │
    ▼
[load]  loader.py
    │   (thin wrapper around metaaudit.loader.load_all_reviews)
    │   yields: AnalysisGroup with trial-level inputs at machine precision
    │
    ▼
[simulate_floor]  precision_floor.py      ← PURE, ZERO I/O, UNIT-TESTABLE
    │   Inputs:  (trial_inputs, precision_spec, scenario)
    │   Outputs: (truth_pooled, rounded_pooled, delta, delta_log)
    │
    ▼
[classify]  classifier.py                  ← PURE, ZERO I/O, USER-AUTHORED BODY
    │   Inputs:  (delta, declared_dp, threshold_mode)
    │   Outputs: {"fixed": bool, "adaptive": bool}
    │
    ▼
[orchestrate]  atlas.py                    ← ORCHESTRATOR ONLY, NO MATH
    │   For each (ma_id, scenario, rounding_mode):
    │     call precision_floor, call classifier
    │     emit atlas.csv row
    │
    ▼
[render]  report.py                        ← RENDERING ONLY, NO MATH
    │   Produces: dashboard.html + e156_paper.md
    │
    └──▶ atlas.csv (~50k rows = 6,229 MAs × 2 scenarios × 4 rounding modes
                     [adaptive + fixed-dp{1,2,3}])
         dashboard.html  (offline, no CDN)
         e156_paper.md   (7 sentences, ≤156 words)
```

### Two reproduction scenarios (shared code path)

- **Scenario A — raw extraction**: a diligent reader re-enters per-trial inputs from the paper's data tables at their published precision.
  - Continuous: `(mean, SD)` rounded to 1–2 dp; `N` integer.
  - Binary: integer counts (effectively exact at extraction level).
  - GIV: `(yi, se)` rounded to 2–3 dp.
- **Scenario B — forest-plot extraction**: a realistic reader reads the per-trial log-effect and SE from the forest plot, which are always rounded to 2–3 dp regardless of underlying data type.

**Why both:** Scenario A is the charitable floor. Scenario B is the realistic floor. The headline contrast ("binary looks reproducible under A, degrades under B") is the paper's scaling story.

### Module isolation boundaries

| Module | Responsibility | I/O? | Depends on |
|---|---|---|---|
| `loader.py` | Load Pairwise70 .rda, yield `AnalysisGroup` | filesystem read | `metaaudit.loader` |
| `precision_floor.py` | Round-and-repool, return delta | **none** (pure) | `metaaudit.recompute`, `numpy` |
| `classifier.py` | `exceeds_threshold(delta, ma_row, mode)` | **none** (pure) | `numpy` |
| `atlas.py` | Orchestrate loader→floor→classifier, write CSV | filesystem write | above three |
| `report.py` | Render dashboard.html + e156_paper.md | filesystem read/write | `atlas.csv` only |

Each module answers three questions: (1) what does it do, (2) how do you use it, (3) what does it depend on — with no internal access needed from consumers.

## 3. Parameters & stratification

### (a) Precision grid

**Decision: adaptive + fixed scan, both.**

- **Adaptive per-MA**: round each MA's per-trial inputs to *that MA's actual Cochrane publication precision*:
  - Continuous: `(mean, SD)` to 1 dp, `N` integer
  - Binary: counts integer, `N` integer (no rounding at input level)
  - GIV: `(yi, se)` to 2 dp
- **Fixed scan**: also compute at `dp ∈ {1, 2, 3}` for the scaling demonstration plot (matches precision-sweep's G07 output format).

Reason for both: adaptive gives the realistic headline; fixed scan shows the `~10^(-dp)` scaling law holds at Cochrane scale, not just on synthetic 2-trial pools.

### (b) Reproduction threshold

**Decision: two thresholds reported in parallel.**

- **Fixed** `|Δ| > 0.005` — matches the SGLT2i-HFpEF ship threshold and Cochrane's typical 2-dp CI half-width.
- **Per-MA adaptive** `|Δ| > 0.5 × 10^(-declared_dp)` — uses each MA's own declared precision.

Both are emitted per row. The headline sentence uses the fixed 0.005 (stable across readers); the dashboard toggles between them.

### (c) Stratification axes

**Included:**
- `k` (trial count): bands `2`, `3–5`, `6–10`, `>10`
- `data_type`: `binary` / `continuous` / `GIV`
- `scenario`: `A` / `B`

**Explicitly skipped for S:**
- Effect-magnitude stratification (adds columns, doesn't change the claim)
- Domain stratification (cardio / oncology / etc.)
- Re-pooling model comparison (DL vs REML vs PM)
- Cross-link to Fragility Atlas or other MetaAudit detectors

## 4. Ship criteria — definition of "done"

D1-S is complete when and only when ALL of:

1. All five modules (`loader`, `precision_floor`, `classifier`, `atlas`, `report`) implemented; unit + integration + regression tests passing.
2. `atlas.csv` generated for all 6,229 MAs × 2 scenarios × 4 rounding modes, with columns at minimum: `ma_id`, `scenario`, `rounding_mode` (`adaptive` | `fixed_1dp` | `fixed_2dp` | `fixed_3dp`), `data_type`, `k`, `truth_pooled`, `rounded_pooled`, `delta`, `declared_dp`, `exceeds_fixed`, `exceeds_adaptive`.
3. `dashboard.html` deployed at `github.io/repro-floor-atlas/`, fully offline (no external CDN), with per-MA drill-down table, stratification toggles, and scenario A/B comparison.
4. `e156_paper.md`: 7 sentences, ≤156 words, single paragraph, primary estimand named, S1–S7 word-budget matches spec (22/20/20/30/22/22/20).
5. `rewrite-workbook.txt` entry added: CURRENT BODY populated, YOUR REWRITE empty, `SUBMITTED: [ ]`, total count incremented.
6. GitHub repo `mahmood726-cyber/repro-floor-atlas` public with:
   - README.md (claim + dashboard link + reproduction instructions)
   - `E156-PROTOCOL.md` (project name, dates, body, dashboard link)
   - GitHub Pages enabled and reachable
7. Sentinel pre-push hook installed; all 11 rules pass (no hardcoded paths in shipped HTML/JS; no placeholder HMAC; no committed `.claude/` configs).
8. Numerical baseline committed as fixture: `tests/fixtures/smoke_10_mas.json` — seed-locked 10-MA regression set. Future verifier runs fail closed if any of those 10 drift.
9. Registry reconciliation: INDEX.md row added, `push_all_repos.py` picks it up, `python C:\ProjectIndex\reconcile_counts.py` returns 0 (clean).

### Performance bounds (per rules.md defaults)

- Smoke / import verification: < 120 seconds
- Default verify path (10-MA smoke + unit tests): < 300 seconds
- Full 6,229-MA atlas generation: no explicit bound — runs offline, once; may take tens of minutes. Document actual runtime in README.

## 5. Explicit out-of-scope (for Size S)

Flagged for a possible Size M follow-up, **not included in D1-S**:

- Re-pooling with alternative methods (REML vs DL vs PM comparison)
- Cross-link to Fragility Atlas per-MA fragility indices
- Domain-stratified analysis (cardiology vs oncology etc.)
- Longer manuscript draft — E156 only for v1
- Scenario C: structured-data extraction from forest plots (IMG2EFFECT-style OCR)
- Bayesian re-analysis of reproduction floor

## 6. Open collaboration points (learning-mode contributions)

The user will contribute the following during implementation. Each is a genuine business-logic decision, not boilerplate:

### Contribution 1: `classifier.py :: exceeds_threshold()`

**Location:** `classifier.py`, function signature:

```python
def exceeds_threshold(
    delta: float,
    declared_dp: int,
    threshold_mode: Literal["fixed", "adaptive", "both"],
) -> dict[str, bool]:
    """Return whether a given reproduction |Δ| counts as non-reproducible.

    Shape of return: {"fixed": bool, "adaptive": bool} (keys present per mode).
    Called once per (ma_id, scenario, dp_level) row in atlas.py.
    """
    # TODO (user): encode the classification rule.
    ...
```

**Why it matters:** this 5–10-line function decides what the headline percentage is. Multiple valid approaches:

- Strict: `abs(delta) > 0.005` fixed; `abs(delta) > 0.5e-dp` adaptive.
- Strict with numerical guard: clamp `delta` to machine epsilon, compare with `>=` not `>` to avoid boundary artifacts.
- Stratified: different thresholds for HR/OR (log-scale) vs continuous (raw-scale).

**User input requested:** encode the rule that matches the paper's claim framing. I will scaffold the file + docstring + failing tests; you write the function body.

### Contribution 2: the E156 S4 sentence (the "Result" sentence, ~30 words)

The S4 sentence is the single-sentence public statement of the atlas's finding. It is not boilerplate — word choice here determines whether the paper lands as a methodological note, a reform argument, or a descriptive atlas.

**User input requested:** write S4 once the atlas.csv is populated and the actual percentage is known. I will draft S1–S3, S5–S7 and leave S4 as a clearly-marked `__PLACEHOLDER__` with word budget (~30 w) and the empirical number as a comment.

## 7. Known risks and mitigations

| Risk | Mitigation |
|---|---|
| MetaAudit recompute output format drifts | Pin MetaAudit to a tagged commit in `requirements.txt`; `test_integration_metaaudit_contract.py` fails closed on schema change (per lessons.md "Integration Contracts") |
| Pairwise70 .rda corpus missing on disk | `Task 0 — prereq check`: script verifies `C:\Projects\Pairwise70\data\*.rda` count ≥ 500 and a representative file loads, before any implementation work |
| `0.005` threshold disputed by reviewers | Dashboard ships both fixed and adaptive thresholds; paper footnote discloses both |
| Precision-sweep formula doesn't generalize beyond 2-trial pools | Integration test: known-floor cases from precision-sweep G07 must reproduce within 1e-10 |
| "Rounding loss" conflated with "measurement loss" | S7 (Boundary) sentence explicitly scopes claim to aggregate-data reproduction, not to IPD meta-analysis |

## 8. Dependencies and prerequisites

### Runtime

- Python 3.11+
- `metaaudit` package (from `C:\MetaAudit\`, editable install or path import)
- `pyreadr` (for .rda loading, already a MetaAudit dep)
- `numpy`, `scipy`, `pandas` (already MetaAudit deps)
- No network dependencies at runtime

### Data

- `C:\Projects\Pairwise70\data\*.rda` (501 files) — verified present 2026-04-15

### Tooling

- R 4.5.2 for any validation cross-checks (optional, not on critical path for S)
- Sentinel CLI for pre-push hook installation

## 9. References

- MetaAudit: `C:\MetaAudit\`, 6,229-MA Cochrane audit engine (BMJ target)
- Precision-sweep E156: `ma-workbench-precision-sweep`, quantifies `~10^(-dp)` scaling on 2-trial pools
- SGLT2i-HFpEF benchmark: shipped FAIL branch at `github.io/ma-workbench/sglt2i-hfpef-demo/`
- Pairwise70: `C:\Projects\Pairwise70\`, raw data corpus
- Lessons captured: `C:\Users\user\.claude\rules\rules.md` (verification-readiness preflight, numerical-baseline contract, integration contracts)
