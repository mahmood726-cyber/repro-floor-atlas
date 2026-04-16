"""Preflight check: verify Pairwise70 corpus + MetaAudit package are importable.

Fail closed per rules.md 'Verification readiness preflight'. Exits non-zero with
an actionable message if any prereq is absent.

Paths are env-driven (no hardcoded defaults, per Sentinel P0-hardcoded-local-path
and rules.md 'Do not hardcode one drive'):
  - PAIRWISE70_DIR: Pairwise70 .rda corpus directory
  - METAAUDIT_DIR: MetaAudit python package directory (the dir containing
    metaaudit/loader.py, metaaudit/recompute.py)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_PAIRWISE70_ENV = "PAIRWISE70_DIR"
_METAAUDIT_ENV = "METAAUDIT_DIR"


def _resolve(env_var: str) -> Path | None:
    val = os.environ.get(env_var)
    return Path(val) if val else None


def main() -> int:
    pairwise70_dir = _resolve(_PAIRWISE70_ENV)
    metaaudit_dir = _resolve(_METAAUDIT_ENV)

    failures: list[str] = []
    rda_files: list[Path] = []

    if pairwise70_dir is None:
        failures.append(
            f"{_PAIRWISE70_ENV} env var not set (point it at the Pairwise70 .rda corpus dir)"
        )
    elif not pairwise70_dir.is_dir():
        failures.append(
            f"Missing Pairwise70 data dir: {pairwise70_dir} "
            f"(re-check {_PAIRWISE70_ENV})"
        )
    else:
        rda_files = list(pairwise70_dir.glob("*.rda"))
        if len(rda_files) < 500:
            failures.append(
                f"Pairwise70 corpus under-populated: {len(rda_files)} .rda files "
                f"(expected >= 500)"
            )

    if metaaudit_dir is None:
        failures.append(
            f"{_METAAUDIT_ENV} env var not set (point it at the MetaAudit package dir, "
            f"e.g. the folder that contains metaaudit/loader.py)"
        )
    elif not metaaudit_dir.is_dir():
        failures.append(
            f"Missing MetaAudit package: {metaaudit_dir} (re-check {_METAAUDIT_ENV})"
        )
    else:
        try:
            sys.path.insert(0, str(metaaudit_dir.parent))
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
            f"  1. export {_PAIRWISE70_ENV}=<path to Pairwise70 .rda corpus>",
            file=sys.stderr,
        )
        print(
            f"  2. export {_METAAUDIT_ENV}=<path to MetaAudit package dir>",
            file=sys.stderr,
        )
        return 1

    print("PREFLIGHT OK")
    print(f"  Pairwise70: {len(rda_files)} .rda files at {pairwise70_dir}")
    print(f"  MetaAudit: importable from {metaaudit_dir.parent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
