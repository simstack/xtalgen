"""Node: spinor / SOC Wannier90 → exchange parameters via wann2J.py."""

from pathlib import Path

from simstack.core.node import node
from simstack.core.simstack_result import SimstackResult
from tbj2.lib.cli import command_string, materialize_file_list, materialize_optional_file
from tbj2.lib.outputs import collect_tb2j_results
from tbj2.models.wannier_input import WannierSpinorInput


@node
async def tb2j_wannier_spinor(opts: WannierSpinorInput, **kwargs) -> SimstackResult:
    """
    Run ``wann2J.py --spinor`` for non-collinear / SOC Wannier90 Hamiltonians.

    SimstackResult:
        files (List[FileStack]): TB2J exchange-parameter output files
    """
    node_runner = kwargs["node_runner"]
    try:
        work = Path(opts.path)
        work.mkdir(parents=True, exist_ok=True)

        if opts.input_files is not None:
            materialize_file_list(opts.input_files, local_dir=work)

        pos = materialize_optional_file(opts.posfile, local_dir=work)
        posfile_name = str(pos) if pos is not None else None

        args = opts.cli_args(posfile_name=posfile_name)
        ok = node_runner.subprocess("wann2J_spinor", command_string(args))
        if not ok:
            return node_runner.fail("wann2J.py (spinor) failed")

        files = collect_tb2j_results(node_runner, opts.common.output_path)
        node_runner.files = files
        return node_runner.succeed()
    except Exception as exc:
        node_runner.error(f"tb2j_wannier_spinor: {exc}")
        return node_runner.fail(str(exc))
