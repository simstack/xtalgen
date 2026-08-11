"""Node: write Wannier90 .win (optional) then run wannier90.x."""

from __future__ import annotations

from pathlib import Path

from simstack.core.node import node
from simstack.core.simstack_result import SimstackResult
from simstack.models.files import FileStack
from vasp.lib.cli import attach_file, command_string
from vasp.lib.write_win import write_wannier90_wins
from vasp.models.wannier90_input import Wannier90RunInput


@node
async def wannier90_run(opts: Wannier90RunInput, **kwargs) -> SimstackResult:
    """
    Optionally write ``{seed}.win``, then run ``wannier90.x <seed>`` for each channel.

    After a successful VASP ``LWANNIER90`` run, ``.mmn`` / ``.amn`` / ``.eig``
    must be present. Produces ``*_hr.dat`` and ``*_centres.xyz`` for TB2J.
    """
    node_runner = kwargs["node_runner"]
    try:
        seeds = opts.seednames()
        if not seeds:
            return node_runner.fail("channels is empty")

        work = Path(opts.work_dir)
        collected: list[FileStack] = []

        if opts.write_win or (
            opts.win_files is not None and opts.win_files.file_list
        ):
            try:
                collected.extend(
                    write_wannier90_wins(
                        seeds,
                        opts.win,
                        win_files=opts.win_files,
                        node_runner=node_runner,
                        work_dir=work,
                    )
                )
            except ValueError as exc:
                return node_runner.fail(str(exc))

        for seed in seeds:
            ok = node_runner.subprocess(
                f"wannier90_{seed}", command_string(opts.cli_args_for(seed))
            )
            if not ok:
                return node_runner.fail(f"wannier90.x failed for seedname={seed}")

            for suffix in ("_hr.dat", "_centres.xyz", "_tb.dat", ".wout"):
                stack = attach_file(node_runner, f"{seed}{suffix}")
                if stack:
                    collected.append(stack)

            hr = Path(f"{seed}_hr.dat")
            if not hr.is_file():
                return node_runner.fail(f"missing {hr} after wannier90.x")

        node_runner.files = collected
        return node_runner.succeed()
    except Exception as exc:
        node_runner.error(f"wannier90_run: {exc}")
        return node_runner.fail(error_message=str(exc))
