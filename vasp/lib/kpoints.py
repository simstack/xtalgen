"""Render VASP KPOINTS mesh file."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vasp.models.vasp_input import VaspKpointsParams


def render_kpoints(params: VaspKpointsParams) -> str:
    """Automatic mesh KPOINTS (Gamma or Monkhorst)."""
    style = params.style.value if hasattr(params.style, "value") else str(params.style)
    return (
        "KPOINTS written by xtalgen.vasp\n"
        "0\n"
        f"{style}\n"
        f"{params.nx} {params.ny} {params.nz}\n"
        f"{params.shift_x} {params.shift_y} {params.shift_z}\n"
    )
