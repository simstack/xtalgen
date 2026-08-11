"""Shared VASP / Wannier helpers."""

from vasp.lib.cli import command_string, materialize_optional_file
from vasp.lib.incar import render_incar
from vasp.lib.kpoints import render_kpoints
from vasp.lib.outcar import parse_efermi
from vasp.lib.potcar import (
    build_potcar,
    build_potcar_from_poscar,
    parse_poscar_elements,
    potcar_dir_from_program,
)
from vasp.lib.win import render_wannier90_win

__all__ = [
    "command_string",
    "materialize_optional_file",
    "render_incar",
    "render_kpoints",
    "parse_efermi",
    "parse_poscar_elements",
    "build_potcar",
    "build_potcar_from_poscar",
    "potcar_dir_from_program",
    "render_wannier90_win",
    "write_vasp_inputs",
    "write_wannier90_wins",
]


def __getattr__(name: str):
    # Lazy exports to avoid circular imports with models.
    if name == "write_vasp_inputs":
        from vasp.lib.write_inputs import write_vasp_inputs

        return write_vasp_inputs
    if name == "write_wannier90_wins":
        from vasp.lib.write_win import write_wannier90_wins

        return write_wannier90_wins
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
