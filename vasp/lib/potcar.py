"""Build POTCAR from POSCAR species and a PAW library directory."""

from pathlib import Path


def _is_number(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False


def parse_poscar_elements(poscar: Path | str) -> list[str]:
    """
    Return species symbols from a VASP POSCAR (order preserved).

    Expects a modern POSCAR with an element line before the counts line.
    """
    path = Path(poscar)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) < 7:
        raise ValueError(f"POSCAR too short ({len(lines)} lines): {path}")

    # line 0: comment, 1: scale, 2-4: lattice, 5: species or counts
    species_tokens = lines[5].split()
    if not species_tokens:
        raise ValueError(f"POSCAR missing species/counts line: {path}")
    if all(_is_number(t) for t in species_tokens):
        raise ValueError(
            f"POSCAR has no element names on line 6 (only counts); "
            f"cannot autobuild POTCAR: {path}"
        )
    return species_tokens


def resolve_potcar_file(potcar_dir: Path | str, element: str) -> Path:
    """
    Locate ``{potcar_dir}/{element}/POTCAR``.

    ``element`` may already be a VASP potcar flavor (e.g. ``Fe_pv``).
    """
    root = Path(potcar_dir)
    candidate = root / element / "POTCAR"
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(
        f"No POTCAR for species {element!r} under {root} "
        f"(expected {candidate})"
    )


def build_potcar(
    elements: list[str],
    potcar_dir: Path | str,
    dest: Path | str,
) -> Path:
    """
    Concatenate PAW ``POTCAR`` files for ``elements`` into ``dest``.

    Species order must match the POSCAR element line.
    """
    if not elements:
        raise ValueError("elements is empty")
    root = Path(potcar_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"potcar_dir is not a directory: {root}")

    out = Path(dest)
    out.parent.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    for el in elements:
        pot = resolve_potcar_file(root, el)
        text = pot.read_text(encoding="utf-8", errors="replace")
        if text and not text.endswith("\n"):
            text += "\n"
        parts.append(text)
    out.write_text("".join(parts), encoding="utf-8")
    return out


def build_potcar_from_poscar(
    poscar: Path | str,
    potcar_dir: Path | str,
    dest: Path | str,
) -> tuple[Path, list[str]]:
    """Parse POSCAR species and write a concatenated POTCAR; return path + elements."""
    elements = parse_poscar_elements(poscar)
    path = build_potcar(elements, potcar_dir, dest)
    return path, elements


def potcar_dir_from_program(program: dict | None) -> Path:
    """
    Read the PAW library path from ``[*.program.vasp]``.

    Accepts ``potcar_dir`` (preferred) or ``poscar_dir`` (alias).
    """
    prog = program or {}
    raw = prog.get("potcar_dir") or prog.get("poscar_dir")
    if not raw:
        raise ValueError(
            "potcar_autobuild requires [*.program.vasp] potcar_dir "
            "(PAW library, e.g. /shared/software/chem/vasp/potpaw_PBE.54)"
        )
    return Path(str(raw).strip())
