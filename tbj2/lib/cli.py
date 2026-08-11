"""CLI argv builders and FileStack staging for TB2J nodes."""

from __future__ import annotations

import os
import shlex
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

from simstack.models.files import FileStack

if TYPE_CHECKING:
    from tbj2.models.tb2j_common import TB2JCommonParams


def command_string(args: list[str]) -> str:
    """Shell-escape a CLI argv list for ``node_runner.subprocess``."""
    return " ".join(shlex.quote(part) for part in args)


def split_tokens(value: str | None) -> list[str]:
    """Split a space-separated CLI token string; empty → []."""
    if not value or not str(value).strip():
        return []
    return str(value).split()


def materialize_optional_file(
    file_stack: FileStack | None,
    *,
    local_dir: Path | None = None,
    preferred_name: str | None = None,
) -> Path | None:
    """Copy ``file_stack`` into ``local_dir`` (cwd by default); return path or None."""
    if file_stack is None:
        return None
    cwd = Path.cwd() if local_dir is None else Path(local_dir)
    local_file = Path(file_stack.get(local_dir=cwd))
    target_name = preferred_name or local_file.name
    target = cwd / target_name

    if local_file.resolve() == target.resolve():
        return target

    if target.exists():
        try:
            if os.path.samefile(local_file, target):
                return target
        except OSError:
            pass

    shutil.copy2(local_file, target)
    return target


def materialize_file_list(
    files: Iterable[FileStack] | None,
    *,
    local_dir: Path | None = None,
) -> list[Path]:
    """Stage each FileStack under ``local_dir``; return local paths."""
    if not files:
        return []
    paths: list[Path] = []
    for stack in files:
        path = materialize_optional_file(stack, local_dir=local_dir)
        if path is not None:
            paths.append(path)
    return paths


def append_flag(args: list[str], flag: str, value: object | None) -> None:
    """Append ``flag`` / ``flag value`` when ``value`` is set (bool → flag only)."""
    if value is None:
        return
    if isinstance(value, bool):
        if value:
            args.append(flag)
        return
    args.extend([flag, str(value)])


def append_common_args(args: list[str], params: TB2JCommonParams) -> None:
    """Append shared TB2J calculation flags from ``TB2JCommonParams``."""
    elements = split_tokens(params.elements)
    if elements:
        args.append("--elements")
        args.extend(elements)

    index_atoms = split_tokens(params.index_magnetic_atoms)
    if index_atoms:
        args.append("--index_magnetic_atoms")
        args.extend(index_atoms)

    args.extend(
        [
            "--kmesh",
            str(params.kmesh_x),
            str(params.kmesh_y),
            str(params.kmesh_z),
        ]
    )
    append_flag(args, "--emin", params.emin)
    append_flag(args, "--emax", params.emax)
    append_flag(args, "--nz", params.nz)
    append_flag(args, "--np", params.np)
    append_flag(args, "--rcut", params.rcut)
    append_flag(args, "--cutoff", params.cutoff)
    append_flag(args, "--output_path", params.output_path)
    append_flag(args, "--description", params.description)
    append_flag(args, "--use_cache", params.use_cache)
    append_flag(args, "--orb_decomposition", params.orb_decomposition)
    append_flag(args, "--ne", params.ne)
