"""Side-effect module: ensure MetaAudit is importable from any consumer.

MetaAudit lacks packaging metadata (no setup.py / pyproject.toml as of
2026-04-15), so it cannot be `pip install -e`'d. This shim makes its location
configurable via the METAAUDIT_DIR env var (default C:/MetaAudit) and inserts
the path before any `import metaaudit` from within this package.

Every module that imports metaaudit must do this first:

    from repro_floor_atlas import _metaaudit_path  # noqa: F401
    from metaaudit.loader import ...

Failure mode: raises RuntimeError at import time with a remediation message
if the directory is missing — fail closed, never silently skip.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_DEFAULT = r"C:\MetaAudit"
METAAUDIT_DIR = Path(os.environ.get("METAAUDIT_DIR", _DEFAULT))

if not METAAUDIT_DIR.is_dir():
    raise RuntimeError(
        f"MetaAudit not found at {METAAUDIT_DIR}. "
        f"Set the METAAUDIT_DIR environment variable to the MetaAudit repo root, "
        f"or place MetaAudit at {_DEFAULT}."
    )

_path_str = str(METAAUDIT_DIR)
if _path_str not in sys.path:
    sys.path.insert(0, _path_str)
