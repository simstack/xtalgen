"""CLI helpers for VASP / Wannier90 nodes."""

from __future__ import annotations

import os
import shlex
import shutil
from pathlib import Path

from simstack.models.files import FileStack


def command_string(args: list[str]) -> str:
    """Shell-escape a CLI argv list for ``node_runner.subprocess``."""
    return " ".join(shlex.quote(part) for part in args)


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


def attach_file(node_runner, path: Path | str) -> FileStack | None:
    """Attach an existing file to ``node_runner.info_files`` if present."""
    p = Path(path)
    if not p.is_file():
        return None
    stack = FileStack.from_local_file(
        str(p), in_memory=True, is_hashable=True, secure_source=True
    )
    node_runner.info_files.append(stack)
    return stack
