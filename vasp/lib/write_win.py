"""Write Wannier90 .win files (plain helper — not a @node)."""

from __future__ import annotations

from pathlib import Path

from simstack.models.file_list import FileListModel
from simstack.models.files import FileStack
from vasp.lib.cli import attach_file, materialize_optional_file
from vasp.lib.win import render_wannier90_win
from vasp.models.wannier90_input import Wannier90WinParams


def _win_with_spinors(win: Wannier90WinParams, *, spinors: bool) -> Wannier90WinParams:
    """Return a Wannier90WinParams copy with ``spinors`` overridden."""
    return win.model_copy(update={"spinors": spinors})


def write_wannier90_wins(
    channels: list[str],
    win: Wannier90WinParams,
    *,
    win_files: FileListModel | None = None,
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

    if win_files is not None:
        staged = list(win_files)
        if staged:
            for fs in staged:
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
