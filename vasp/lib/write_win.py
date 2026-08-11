"""Write Wannier90 .win files (plain helper — not a @node)."""

from __future__ import annotations

from pathlib import Path

from simstack.models.file_list import FileListIO
from simstack.models.files import FileStack
from vasp.lib.cli import attach_file, materialize_optional_file
from vasp.lib.win import render_wannier90_win
from vasp.models.wannier90_input import Wannier90WinParams


def _win_with_spinors(win: Wannier90WinParams, *, spinors: bool) -> Wannier90WinParams:
    """Return a Wannier90WinParams copy with ``spinors`` overridden."""
    return Wannier90WinParams(
        num_wann=win.num_wann,
        num_bands=win.num_bands,
        num_iter=win.num_iter,
        guiding_centres=win.guiding_centres,
        write_hr=win.write_hr,
        write_xyz=win.write_xyz,
        write_tb=win.write_tb,
        spinors=spinors,
        dis_win_min=win.dis_win_min,
        dis_win_max=win.dis_win_max,
        dis_froz_min=win.dis_froz_min,
        dis_froz_max=win.dis_froz_max,
        exclude_bands=win.exclude_bands,
        mp_grid_x=win.mp_grid_x,
        mp_grid_y=win.mp_grid_y,
        mp_grid_z=win.mp_grid_z,
        projections=win.projections,
        extra_win=win.extra_win,
    )


def write_wannier90_wins(
    channels: list[str],
    win: Wannier90WinParams,
    *,
    win_files: FileListIO | None = None,
    node_runner=None,
    work_dir: Path | str | None = None,
) -> list[FileStack]:
    """
    Write ``{seed}.win`` for each seedname in ``channels``.

    If ``win_files`` is provided, stage those FileStacks instead of generating.
    When generating, set ``spinors=True`` for seed ``wannier90`` (SOC/spinor).
    """
    work = Path(work_dir) if work_dir is not None else Path(".")
    work.mkdir(parents=True, exist_ok=True)
    collected: list[FileStack] = []

    if win_files is not None and win_files.file_list:
        for fs in win_files.file_list:
            path = materialize_optional_file(fs, local_dir=work)
            if path is None:
                continue
            if node_runner is not None:
                stack = attach_file(node_runner, path)
                if stack:
                    collected.append(stack)
        return collected

    if not channels:
        raise ValueError("channels is empty")

    for seed in channels:
        params = win
        if seed == "wannier90" and not win.spinors:
            params = _win_with_spinors(win, spinors=True)
        path = work / f"{seed}.win"
        path.write_text(render_wannier90_win(params), encoding="utf-8")
        if node_runner is not None:
            stack = attach_file(node_runner, path)
            if stack:
                collected.append(stack)

    return collected
