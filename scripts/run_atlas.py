"""CLI: run the full reproduction-floor atlas over Pairwise70."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from repro_floor_atlas.atlas import build_atlas
from repro_floor_atlas.loader import load_directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(r"C:\Projects\Pairwise70\data"),
        help="Pairwise70 .rda directory",
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

    if not args.data_dir.is_dir():
        print(f"ERROR: data dir not found: {args.data_dir}", file=sys.stderr)
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
