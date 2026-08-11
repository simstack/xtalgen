"""Render Wannier90 .win files for VASP workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vasp.models.wannier90_input import Wannier90WinParams


def _bool(v: bool) -> str:
    return "true" if v else "false"


def render_wannier90_win(params: Wannier90WinParams) -> str:
    """
    Build a Wannier90 ``.win`` body.

    Structure / kpoints blocks are usually written by VASP when ``LWANNIER90``
    is set; this renderer focuses on disentanglement, projections, and output
    flags needed for TB2J (``write_hr``, ``write_xyz``).
    """
    lines: list[str] = [
        f"num_wann = {params.num_wann}",
        f"num_bands = {params.num_bands}",
        f"num_iter = {params.num_iter}",
        f"guiding_centres = {_bool(params.guiding_centres)}",
        f"write_hr = {_bool(params.write_hr)}",
        f"write_xyz = {_bool(params.write_xyz)}",
        f"write_tb = {_bool(params.write_tb)}",
        f"spinors = {_bool(params.spinors)}",
    ]
    if params.dis_win_min is not None:
        lines.append(f"dis_win_min = {params.dis_win_min}")
    if params.dis_win_max is not None:
        lines.append(f"dis_win_max = {params.dis_win_max}")
    if params.dis_froz_min is not None:
        lines.append(f"dis_froz_min = {params.dis_froz_min}")
    if params.dis_froz_max is not None:
        lines.append(f"dis_froz_max = {params.dis_froz_max}")
    if params.exclude_bands.strip():
        lines.append(f"exclude_bands = {params.exclude_bands.strip()}")
    if params.mp_grid_x and params.mp_grid_y and params.mp_grid_z:
        lines.append(
            f"mp_grid = {params.mp_grid_x} {params.mp_grid_y} {params.mp_grid_z}"
        )
    if params.projections.strip():
        lines.append("begin projections")
        lines.append(params.projections.strip())
        lines.append("end projections")
    if params.extra_win.strip():
        lines.append(params.extra_win.strip())
    return "\n".join(lines) + "\n"
