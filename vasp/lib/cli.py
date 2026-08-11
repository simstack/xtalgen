"""CLI helpers for VASP / Wannier90 nodes."""

from __future__ import annotations

import os
import shlex
import shutil
from pathlib import Path
from typing import Literal

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


def attach_file(
    node_runner,
    path: Path | str,
    *,
    dest: Literal["info_files", "files"] = "info_files",
    in_memory: bool | None = None,
    secure_source: bool = True,
    is_hashable: bool = True,
) -> FileStack | None:
    """
    Attach an existing file to ``node_runner.info_files`` or ``node_runner.files``.

    Pipeline outputs (``dest="files"``) default to ``in_memory=False`` with
    ``secure_source=True``. Diagnostic / log outputs stay on ``info_files``
    and default to ``in_memory=True``.
    """
    p = Path(path)
    if not p.is_file():
        return None
    if in_memory is None:
        in_memory = dest == "info_files"
    stack = FileStack.from_local_file(
        str(p),
        in_memory=in_memory,
        is_hashable=is_hashable,
        secure_source=secure_source,
    )
    if dest == "files":
        node_runner.files.append(stack)
    else:
        node_runner.info_files.append(stack)
    return stack
