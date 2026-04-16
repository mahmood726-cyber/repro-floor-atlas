"""CLI: run the full reproduction-floor atlas over Pairwise70."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from repro_floor_atlas.atlas import build_atlas
from repro_floor_atlas.loader import load_directory

_ENV_VAR = "PAIRWISE70_DIR"


def _resolve_default_data_dir() -> Path | None:
    """Resolve Pairwise70 dir from env var. No hardcoded default (Sentinel P0)."""
    val = os.environ.get(_ENV_VAR)
    return Path(val) if val else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=_resolve_default_data_dir(),
        help=(
            "Pairwise70 .rda directory "
            f"(required unless {_ENV_VAR} env var is set)"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("outputs") / "atlas.csv",
        help="Output CSV path (relative to repo root)",
    )
    parser.add_argument(
        "--max-reviews",
        type=int,
        default=None,
        help="Limit the number of reviews (for smoke testing)",
    )
    args = parser.parse_args(argv)

    if args.data_dir is None:
        print(
            f"ERROR: --data-dir is required (or set the {_ENV_VAR} env var)",
            file=sys.stderr,
        )
        return 1
    if not args.data_dir.is_dir():
        print(
            f"ERROR: data dir not found: {args.data_dir} "
            f"(set {_ENV_VAR} env var or pass --data-dir)",
            file=sys.stderr,
        )
        return 1

    t0 = time.time()
    print(f"Loading reviews from {args.data_dir}...")
    mas = load_directory(args.data_dir, max_reviews=args.max_reviews)
    print(f"  loaded {len(mas)} MAs in {time.time() - t0:.1f}s")

    t1 = time.time()
    n = build_atlas(mas, args.out)
    print(f"Wrote {n} rows to {args.out} in {time.time() - t1:.1f}s")
    print(f"Total elapsed: {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
