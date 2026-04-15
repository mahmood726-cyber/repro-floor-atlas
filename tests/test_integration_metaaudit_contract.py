"""Guard the MetaAudit → repro_floor_atlas contract.

If MetaAudit renames columns, changes DataType enum, or alters compute_log_or /
compute_md signatures, this test fails loudly BEFORE atlas.py returns a silent
garbage output.
"""

from __future__ import annotations

from repro_floor_atlas import _metaaudit_path  # noqa: F401  (ensures metaaudit on sys.path)

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
