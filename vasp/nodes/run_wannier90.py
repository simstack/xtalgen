"""Node: write Wannier90 .win (optional) then run via config.toml ``program.wannier90``."""

from pathlib import Path
import shlex

from simstack.core.context import context
from simstack.core.node import node
from simstack.core.simstack_result import SimstackResult
from simstack.models.files import FileStack
from vasp.lib.cli import attach_file
from vasp.lib.write_win import write_wannier90_wins
from vasp.models.wannier90_input import Wannier90RunInput


@node
async def wannier90_run(opts: Wannier90RunInput, **kwargs) -> SimstackResult:
    """
    Optionally write ``{seed}.win``, then run ``program.wannier90`` for each channel.

    Binary / launcher come from ``config.toml``
    (``[<resource>.program.wannier90] run_command``); each seedname is appended
    as the Wannier90 seed argument. After a successful VASP ``LWANNIER90`` run,
    ``.mmn`` / ``.amn`` / ``.eig`` must be present. Produces ``*_hr.dat`` and
    ``*_centres.xyz`` for TB2J.

    SimstackResult:
        files (List[FileStack]): Wannier90 ``*_hr.dat`` / ``*_centres.xyz`` (and related) outputs
    """
    node_runner = kwargs["node_runner"]
    try:
        program = context.resource_config.get_program("wannier90")
        run_command = program.get("run_command")
        if not run_command:
            return node_runner.fail(
                "Missing run_command for [*.program.wannier90] in config.toml "
                f"(resource={getattr(context.resource_config, '_resource', '?')})"
            )

        seeds = opts.seednames()
        if not seeds:
            return node_runner.fail("channels is empty")

        work = Path(".")
        collected: list[FileStack] = []

        if opts.use_win_files or opts.write_win:
            try:
                collected.extend(
                    write_wannier90_wins(
                        seeds,
                        opts.win,
                        win_files=opts.win_files if opts.use_win_files else None,
                        node_runner=node_runner,
                        work_dir=work,
                    )
                )
            except ValueError as exc:
                return node_runner.fail(str(exc))

        for seed in seeds:
            # Append seed to configured launcher (may include module load … && binary).
            cmd = f"{run_command} {shlex.quote(seed)}"
            ok = node_runner.subprocess(f"wannier90_{seed}", cmd)
            if not ok:
                return node_runner.fail(
                    f"wannier90 failed for seedname={seed} "
                    f"(run_command={run_command!r})"
                )

            for suffix in ("_hr.dat", "_centres.xyz", "_tb.dat", ".wout"):
                stack = attach_file(node_runner, f"{seed}{suffix}")
                if stack:
                    collected.append(stack)

            hr = Path(f"{seed}_hr.dat")
            if not hr.is_file():
                return node_runner.fail(f"missing {hr} after wannier90")

        node_runner.files = collected
        return node_runner.succeed()
    except Exception as exc:
        node_runner.error(f"wannier90_run: {exc}")
        return node_runner.fail(error_message=str(exc))
