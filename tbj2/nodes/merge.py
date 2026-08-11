"""Node: merge rotated TB2J results via TB2J_merge.py."""

from __future__ import annotations

from simstack.core.node import node
from simstack.core.simstack_result import SimstackResult
from tbj2.lib.cli import command_string
from tbj2.lib.outputs import collect_tb2j_results
from tbj2.models.merge_input import TB2JMergeInput


@node
async def tb2j_merge(opts: TB2JMergeInput, **kwargs) -> SimstackResult:
    """Run ``TB2J_merge.py`` on rotated TB2J result directories."""
    node_runner = kwargs["node_runner"]
    try:
        args = opts.cli_args()
        ok = node_runner.subprocess("TB2J_merge", command_string(args))
        if not ok:
            return node_runner.fail("TB2J_merge.py failed")

        try:
            files = collect_tb2j_results(
                node_runner, opts.output_path, required_any=False
            )
            if files:
                node_runner.files = files
        except FileNotFoundError:
            pass
        return node_runner.succeed()
    except Exception as exc:
        node_runner.error(f"tb2j_merge: {exc}")
        return node_runner.fail(error_message=str(exc))
