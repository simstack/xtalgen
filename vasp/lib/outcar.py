"""Parse Fermi energy from VASP OUTCAR."""

from __future__ import annotations

import re
from pathlib import Path


_EFERMI_RE = re.compile(
    r"E-fermi\s*:\s*([-+]?\d+\.?\d*(?:[Ee][-+]?\d+)?)",
    re.IGNORECASE,
)


def parse_efermi(outcar_path: str | Path = "OUTCAR") -> float | None:
    """
    Return the last ``E-fermi`` value found in OUTCAR, or None if missing.

    VASP prints E-fermi multiple times; the last occurrence is the converged value.
    """
    path = Path(outcar_path)
    if not path.is_file():
        return None
    last: float | None = None
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = _EFERMI_RE.search(line)
            if match:
                last = float(match.group(1))
    return last
