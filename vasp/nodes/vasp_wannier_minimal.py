"""Smoke node: ``vasp_run`` then ``wannier90_run`` in one workdir."""

from simstack.core.definitions import TaskStatus
from simstack.core.node import node
from simstack.core.simstack_result import SimstackResult
from vasp.models.vasp_wannier_minimal import VaspWannierMinimalInput
from vasp.nodes.run_vasp import vasp_run
from vasp.nodes.run_wannier90 import wannier90_run


def _ok(result: SimstackResult) -> bool:
    return getattr(result, "status", None) == TaskStatus.COMPLETED


def _err(result: SimstackResult, fallback: str) -> str:
    return getattr(result, "error_message", None) or fallback


@node
async def vasp_wannier_minimal(
    opts: VaspWannierMinimalInput, **kwargs
) -> SimstackResult:
    """
    Run a minimal VASP (``LWANNIER90``) step, then Wannier90 on its interface files.

    Both steps share the node workdir so ``wannier90*.mmn`` / ``.amn`` / ``.eig``
    from ``vasp_run`` are visible to ``wannier90_run``.

    SimstackResult:
        files (List[FileStack]): Pipeline files from VASP and Wannier90
        info_files (List[FileStack]): Diagnostic files from both steps
        efermi (FloatData): Fermi energy from VASP when present
    """
    node_runner = kwargs["node_runner"]
    try:
        vasp_result = await vasp_run(opts.vasp, **kwargs)
        if not _ok(vasp_result):
            return node_runner.fail(_err(vasp_result, "vasp_run failed"))

        wannier_result = await wannier90_run(opts.wannier, **kwargs)
        if not _ok(wannier_result):
            return node_runner.fail(_err(wannier_result, "wannier90_run failed"))

        collected = []
        for part in (vasp_result, wannier_result):
            collected.extend(getattr(part, "files", None) or [])
        node_runner.files = collected

        efermi = getattr(vasp_result, "efermi", None)
        if efermi is not None:
            node_runner.efermi = efermi

        node_runner.info("vasp_wannier_minimal completed")
        return node_runner.succeed()
    except Exception as exc:
        node_runner.error(f"vasp_wannier_minimal: {exc}")
        return node_runner.fail(str(exc))
