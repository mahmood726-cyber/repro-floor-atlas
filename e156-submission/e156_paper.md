# Reproduction-Floor Atlas — E156

Primary estimand: proportion of Cochrane MAs for which |Δ| > 0.005 under
Scenario-B adaptive rounding.

**S1 (Question, ~22w):** Can a Cochrane meta-analysis be reproduced to its
published precision using only the per-trial numerics a reader extracts from
the paper?

**S2 (Dataset, ~20w):** Pairwise70 corpus: 595 Cochrane reviews comprising
7,545 meta-analyses spanning binary, continuous, and generic-inverse-variance
outcomes, with trial-level inputs at machine precision.

**S3 (Method, ~20w):** We re-pooled each MA at machine precision and after
rounding per-trial inputs to Cochrane's adaptive precision plus fixed 1-3 dp.

**S4 (Result, ~30w):** Across 7,545 Cochrane MAs, 14.3% had reproduction
error |Δ| > 0.005 under forest-plot extraction; the failure rate was 12.9% for
binary outcomes but 25-27% for continuous and GIV outcomes.

**S5 (Robustness, ~22w):** The scaling relation |Δ| ~ 10^(-dp) held across
binary, continuous, and GIV strata, and was stable under both raw-extraction
and forest-plot framings.

**S6 (Interpretation, ~22w):** Published two-decimal-place precision in pooled
effects exceeds the information content extractable per-trial; this is a
structural limit, not a method flaw.

**S7 (Boundary, ~20w):** Claim scope: aggregate-data reproduction with
fixed-effect pooling; does not apply to individual-patient-data re-analysis or
to random-effects estimators outside this simulation.
