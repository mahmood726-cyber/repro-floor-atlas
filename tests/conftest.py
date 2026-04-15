"""Shared pytest fixtures."""

from __future__ import annotations

import sys
sys.path.insert(0, r"C:\MetaAudit")

from pathlib import Path

import pytest

PAIRWISE70_DIR = Path(r"C:\Projects\Pairwise70\data")


@pytest.fixture(scope="session")
def pairwise70_dir() -> Path:
    """Path to Pairwise70 .rda corpus. Skip tests if absent."""
    if not PAIRWISE70_DIR.is_dir():
        pytest.skip(f"Pairwise70 corpus not found at {PAIRWISE70_DIR}")
    return PAIRWISE70_DIR


@pytest.fixture(scope="session")
def small_rda_file(pairwise70_dir: Path) -> Path:
    """Return one .rda file for integration tests. Picks lexicographically first."""
    files = sorted(pairwise70_dir.glob("*.rda"))
    if not files:
        pytest.skip("No .rda files in Pairwise70 corpus")
    return files[0]
