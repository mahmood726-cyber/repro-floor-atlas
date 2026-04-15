# Reproduction-Floor Atlas — E156

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
7545; adaptive_pct = 14.3; fixed_pct = 14.3) -->

**S5 (Robustness, ~22w):** The scaling relation |Δ| ~ 10^(-dp) held across
fixed-precision cuts in binary, continuous, and GIV strata; patterns were
stable under Scenario-A (raw extraction) and Scenario-B (forest-plot) framings.

**S6 (Interpretation, ~22w):** Published two-decimal-place precision in pooled
effects exceeds the information content of the extractable per-trial numerics
for a non-trivial share of MAs; this is a structural limit, not a method flaw.

**S7 (Boundary, ~20w):** Claim scope: aggregate-data reproduction with
fixed-effect pooling; does not apply to individual-patient-data re-analysis or
to random-effects estimators outside this simulation.
