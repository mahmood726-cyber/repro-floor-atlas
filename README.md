# Reproduction-Floor Atlas

> Does every Cochrane meta-analysis publish results a reader can actually reproduce to the precision claimed? We measured this for all 7545 MAs (Scenario-B, adaptive rounding) in the Pairwise70 corpus.

## Headline finding

Under Scenario B (a reader reconstructs per-trial effects from the forest plot), re-pooling at Cochrane's published precision produces |Δ| > 0.005 in **14.3%** of 7545 MAs — the declared two-decimal-place precision is mathematically unreachable from published aggregate data.

Under the per-MA adaptive threshold (|Δ| > 0.5 × 10^(-declared_dp)), the failure rate is **14.3%**.

**Live dashboard:** https://mahmood726-cyber.github.io/repro-floor-atlas/

## Quick start

```bash
pip install -e .
pip install -r requirements.txt
python scripts/prereq_check.py     # verify Pairwise70 + MetaAudit
python scripts/run_atlas.py        # produces outputs/atlas.csv
pytest -v                          # all tests must pass
```

Set the `METAAUDIT_DIR` env var to the MetaAudit `metaaudit/` package directory (the folder containing `__init__.py`, `loader.py`, `recompute.py`). MetaAudit lacks PyPI packaging; the path shim at `src/repro_floor_atlas/_metaaudit_path.py` defaults to `C:\MetaAudit\metaaudit` and fails closed if the directory is missing. Set the `PAIRWISE70_DIR` env var to the Pairwise70 `.rda` corpus directory — all scripts require it.

## Reproduction

- Source data: Pairwise70 Cochrane corpus, 595 reviews / 7,545 MAs (path via `PAIRWISE70_DIR` env var)
- Pooling engine: MetaAudit `metaaudit.recompute` (inverse-variance fixed-effect)
- Rounding scenarios: raw extraction (A) and forest-plot extraction (B)
- Regression baseline: `tests/fixtures/smoke_10_mas.json` — re-running the pipeline must bit-match this file

## What this is NOT

- Not a methodological audit (DL vs REML etc.)
- Not a publication-bias claim
- Narrowly: rounding-induced precision loss in aggregate-data re-pooling

## E156 micro-paper

See `e156-submission/e156_paper.md`. Protocol: `E156-PROTOCOL.md`.

## Verification status

- pytest: 21 passed (2026-04-16)
- Sentinel scan: PASS (0 BLOCK, 0 WARN) after env-var fix

## License

MIT. See `LICENSE`.
