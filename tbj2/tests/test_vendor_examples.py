"""Optional smoke: vendor examples tree is present (no DFT/TB2J run)."""

from __future__ import annotations

from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parents[2] / "vendor" / "TB2J_examples"


@pytest.mark.skipif(not EXAMPLES.is_dir(), reason="TB2J_examples submodule not checked out")
def test_vendor_examples_layout():
    assert (EXAMPLES / "Wannier").is_dir() or (EXAMPLES / "Siesta").is_dir()
