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
