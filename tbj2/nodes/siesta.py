"""Node: Siesta HS → exchange parameters via siesta2J.py."""

from pathlib import Path

from simstack.core.node import node
from simstack.core.simstack_result import SimstackResult
from tbj2.lib.cli import command_string, materialize_file_list, materialize_optional_file
from tbj2.lib.outputs import collect_tb2j_results
from tbj2.models.siesta_input import SiestaInput


@node
async def tb2j_siesta(opts: SiestaInput, **kwargs) -> SimstackResult:
    """
    Run ``siesta2J.py`` on Siesta Hamiltonian / overlap output.

    SimstackResult:
        files (List[FileStack]): TB2J exchange-parameter output files
    """
    node_runner = kwargs["node_runner"]
    try:
        work = Path(".")
        if opts.input_files is not None:
            materialize_file_list(opts.input_files, local_dir=work)

        fdf = materialize_optional_file(opts.fdf_fname, local_dir=work)
        fdf_name = str(fdf) if fdf is not None else None

        args = opts.cli_args(fdf_name=fdf_name)
        ok = node_runner.subprocess("siesta2J", command_string(args))
        if not ok:
            return node_runner.fail("siesta2J.py failed")

        files = collect_tb2j_results(node_runner, opts.common.output_path)
        node_runner.files = files
        return node_runner.succeed()
    except Exception as exc:
        node_runner.error(f"tb2j_siesta: {exc}")
        return node_runner.fail(str(exc))
