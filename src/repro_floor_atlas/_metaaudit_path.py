"""Side-effect module: ensure MetaAudit is importable from any consumer.

MetaAudit lacks packaging metadata (no setup.py / pyproject.toml as of
2026-04-15), so it cannot be `pip install -e`'d. This shim makes its location
configurable via the METAAUDIT_DIR env var and inserts the package's parent
onto sys.path before any `import metaaudit` from within this package.

METAAUDIT_DIR must point at the `metaaudit/` package directory itself (the
folder containing `__init__.py`, `loader.py`, `recompute.py`). This matches
the semantics used by `scripts/prereq_check.py`. Default is
`C:\\MetaAudit\\metaaudit` — Mahmood's local MetaAudit clone layout — so
zero-config works on the primary dev box; elsewhere, set the env var.

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

_DEFAULT_METAAUDIT = Path(r"C:\MetaAudit\metaaudit")
METAAUDIT_DIR = Path(os.environ.get("METAAUDIT_DIR", _DEFAULT_METAAUDIT))

if not METAAUDIT_DIR.exists():
    sys.exit(
        f"MetaAudit module not found at {METAAUDIT_DIR}. "
        f"Set METAAUDIT_DIR env var or install MetaAudit at {_DEFAULT_METAAUDIT}."
    )

if str(METAAUDIT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(METAAUDIT_DIR.parent))
