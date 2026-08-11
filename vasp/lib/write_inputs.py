"""Write VASP input files (plain helper — not a @node)."""

from __future__ import annotations

from pathlib import Path

from simstack.models.files import FileStack
from vasp.lib.cli import attach_file, materialize_optional_file
from vasp.models.vasp_input import VaspJobInput


def write_vasp_inputs(
    job: VaspJobInput,
    *,
    node_runner=None,
    work_dir: Path | str | None = None,
) -> list[FileStack]:
    """
    Materialize INCAR / KPOINTS / POSCAR / POTCAR (+ optional extras).

    Raises ``ValueError`` when required FileStacks are missing.
    """
    work = Path(work_dir) if work_dir is not None else Path(".")
    work.mkdir(parents=True, exist_ok=True)
    collected: list[FileStack] = []

    if job.use_incar_file:
        path = materialize_optional_file(
            job.incar_file, local_dir=work, preferred_name="INCAR"
        )
        if path is None:
            raise ValueError("use_incar_file set but incar_file missing")
    else:
        path = work / "INCAR"
        path.write_text(job.incar_text(), encoding="utf-8")

    if node_runner is not None:
        stack = attach_file(node_runner, path)
        if stack:
            collected.append(stack)

    if job.use_kpoints_file:
        path = materialize_optional_file(
            job.kpoints_file, local_dir=work, preferred_name="KPOINTS"
        )
        if path is None:
            raise ValueError("use_kpoints_file set but kpoints_file missing")
    else:
        path = work / "KPOINTS"
        path.write_text(job.kpoints_text(), encoding="utf-8")

    if node_runner is not None:
        stack = attach_file(node_runner, path)
        if stack:
            collected.append(stack)

    pos = materialize_optional_file(job.poscar, local_dir=work, preferred_name="POSCAR")
    if pos is None:
        raise ValueError("poscar FileStack failed to materialize")
    if node_runner is not None:
        stack = attach_file(node_runner, pos)
        if stack:
            collected.append(stack)

    pot = materialize_optional_file(job.potcar, local_dir=work, preferred_name="POTCAR")
    if pot is None:
        raise ValueError("potcar FileStack failed to materialize")
    if node_runner is not None:
        stack = attach_file(node_runner, pot)
        if stack:
            collected.append(stack)

    if job.use_extra_files and job.extra_files is not None:
        staged = list(job.extra_files)
        for fs in staged:
            path = materialize_optional_file(fs, local_dir=work)
            if path is not None and node_runner is not None:
                stack = attach_file(node_runner, path)
                if stack:
                    collected.append(stack)

    return collected
