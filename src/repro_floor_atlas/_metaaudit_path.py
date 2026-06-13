"""Side-effect module: ensure MetaAudit is importable from any consumer.

MetaAudit lacks packaging metadata (no setup.py / pyproject.toml as of
2026-04-15), so it cannot be `pip install -e`'d. This shim makes its location
configurable via the METAAUDIT_DIR env var and inserts the package's parent
onto sys.path before any `import metaaudit` from within this package.

METAAUDIT_DIR must point at the `metaaudit/` package directory itself (the
folder containing `__init__.py`, `loader.py`, `recompute.py`). This matches
the semantics used by `scripts/prereq_check.py`. If the env var is unset, the
shim probes a list of known local clone layouts (the MetaAudit repo lives at
`C:\\Projects\\MetaAudit\\metaaudit`) so zero-config works on the dev boxes;
elsewhere, set the env var.

Every module that imports metaaudit must do this first:

    from repro_floor_atlas import _metaaudit_path  # noqa: F401
    from metaaudit.loader import ...

Failure mode: fails closed via `sys.exit` at import time with a remediation
message if the directory is missing — never silently skip.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Candidate clone layouts probed when METAAUDIT_DIR is unset. The MetaAudit
# repo is checked out at C:\Projects\MetaAudit on the dev boxes (case-variant
# C:\Projects\metaaudit on case-insensitive Windows). The legacy C:\MetaAudit
# default is kept last for backwards compatibility.
_CANDIDATES = [
    Path(r"C:\Projects\MetaAudit\metaaudit"),
    Path(r"C:\Projects\metaaudit\metaaudit"),
    Path(r"C:\MetaAudit\metaaudit"),
]


def _resolve_metaaudit_dir() -> Path:
    env = os.environ.get("METAAUDIT_DIR")
    if env:
        return Path(env)
    for cand in _CANDIDATES:
        if cand.exists():
            return cand
    # Nothing found; return the first candidate so the error message is concrete.
    return _CANDIDATES[0]


METAAUDIT_DIR = _resolve_metaaudit_dir()

if not METAAUDIT_DIR.exists():
    sys.exit(
        f"MetaAudit module not found at {METAAUDIT_DIR}. "
        f"Set METAAUDIT_DIR env var or install MetaAudit at one of: "
        f"{', '.join(str(c) for c in _CANDIDATES)}."
    )

if str(METAAUDIT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(METAAUDIT_DIR.parent))
