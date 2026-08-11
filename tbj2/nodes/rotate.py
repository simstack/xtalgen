"""Node: prepare rotated structures via TB2J_rotate.py."""

from pathlib import Path

from simstack.core.node import node
from simstack.core.simstack_result import SimstackResult
from simstack.models.files import FileStack
from tbj2.lib.cli import command_string, materialize_optional_file
from tbj2.models.rotate_input import TB2JRotateInput


@node
async def tb2j_rotate(opts: TB2JRotateInput, **kwargs) -> SimstackResult:
    """
    Run ``TB2J_rotate.py`` to generate rotated crystal structures.

    SimstackResult:
        files (List[FileStack]): Rotated ``atoms_*`` structure files
    """
    node_runner = kwargs["node_runner"]
    try:
        structure = materialize_optional_file(opts.structure, local_dir=Path("."))
        structure_name = str(structure) if structure is not None else None

        args = opts.cli_args(structure_name=structure_name)
        ok = node_runner.subprocess("TB2J_rotate", command_string(args))
        if not ok:
            return node_runner.fail("TB2J_rotate.py failed")

        collected: list[FileStack] = []
        # Collinear → atoms_0..2; noncollinear → atoms_0..5 (files or dirs).
        n_structures = 6 if opts.noncollinear else 3
        for i in range(n_structures):
            for candidate in (Path(f"atoms_{i}"), Path(f"atoms_{i}.{opts.ftype}")):
                if candidate.is_file():
                    stack = FileStack.from_local_file(
                        str(candidate),
                        in_memory=True,
                        is_hashable=True,
                        secure_source=True,
                    )
                    node_runner.info_files.append(stack)
                    collected.append(stack)
                elif candidate.is_dir():
                    for path in candidate.rglob("*"):
                        if path.is_file():
                            stack = FileStack.from_local_file(
                                str(path),
                                in_memory=True,
                                is_hashable=True,
                                secure_source=True,
                            )
                            node_runner.info_files.append(stack)
                            collected.append(stack)

        if not collected:
            return node_runner.fail("TB2J_rotate.py produced no atoms_* outputs")

        node_runner.files = collected
        return node_runner.succeed()
    except Exception as exc:
        node_runner.error(f"tb2j_rotate: {exc}")
        return node_runner.fail(str(exc))
