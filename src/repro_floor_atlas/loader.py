"""Thin wrapper over MetaAudit's Pairwise70 .rda loader.

Converts MetaAudit's AnalysisGroup objects into plain-dataclass MAInputs with
typed per-trial numpy arrays for each data type. No math here.
"""

from __future__ import annotations

from repro_floor_atlas import _metaaudit_path  # noqa: F401  (ensures metaaudit on sys.path)

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
