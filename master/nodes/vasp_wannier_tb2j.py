"""Master node: VASP → Wannier90 → TB2J exchange parameters."""

from simstack.core.definitions import TaskStatus
from simstack.core.node import node
from simstack.core.simstack_result import SimstackResult
from simstack.models import FloatData
from tbj2.models.wannier_input import WannierCollinearInput, WannierSpinorInput
from tbj2.nodes.wannier_collinear import tb2j_wannier_collinear
from tbj2.nodes.wannier_spinor import tb2j_wannier_spinor
from vasp.models.wannier90_input import StageWannierForTB2JInput, Wannier90RunInput
from vasp.nodes.run_vasp import vasp_run
from vasp.nodes.run_wannier90 import wannier90_run
from vasp.nodes.stage_tb2j import vasp_stage_wannier_for_tb2j

from master.models.workflow_input import VaspWannierTB2JInput


def _ok(result: SimstackResult) -> bool:
    return getattr(result, "status", None) == TaskStatus.COMPLETED


def _err(result: SimstackResult, fallback: str) -> str:
    return getattr(result, "error_message", None) or fallback


def _efermi_value(efermi: FloatData | float | None) -> float | None:
    if efermi is None:
        return None
    if isinstance(efermi, FloatData):
        return efermi.value
    return float(efermi)


def _wannier_opts(opts: VaspWannierTB2JInput) -> Wannier90RunInput:
    """Align Wannier channels / spinors with collinear vs SOC mode."""
    wannier = opts.wannier.model_copy()
    if opts.collinear:
        wannier.channels = f"{opts.prefix_up} {opts.prefix_down}"
        wannier.win = wannier.win.model_copy(update={"spinors": False})
    else:
        wannier.channels = opts.prefix_spinor
        wannier.win = wannier.win.model_copy(update={"spinors": True})
    return wannier


@node
async def vasp_wannier_tb2j(opts: VaspWannierTB2JInput, **kwargs) -> SimstackResult:
    """
    Run the collinear or spinor magnetism pipeline end-to-end.

    1. ``vasp_run`` (expects ``LWANNIER90`` / interface files)
    2. ``wannier90_run``
    3. ``vasp_stage_wannier_for_tb2j`` (sets ``efermi`` as ``FloatData``)
    4. ``tb2j_wannier_collinear`` or ``tb2j_wannier_spinor``

    SimstackResult:
        files (List[FileStack]): Aggregated files from VASP, Wannier90, and TB2J steps
        efermi (FloatData): Fermi energy (eV) used for TB2J
    """
    node_runner = kwargs["node_runner"]
    try:
        vasp_result = await vasp_run(opts.vasp, **kwargs)
        if not _ok(vasp_result):
            return node_runner.fail(_err(vasp_result, "vasp_run failed"))

        wannier_result = await wannier90_run(_wannier_opts(opts), **kwargs)
        if not _ok(wannier_result):
            return node_runner.fail(_err(wannier_result, "wannier90_run failed"))

        stage_opts = StageWannierForTB2JInput(
            collinear=opts.collinear,
            prefix_up=opts.prefix_up,
            prefix_down=opts.prefix_down,
            prefix_spinor=opts.prefix_spinor,
            parse_efermi_from_outcar=opts.efermi is None,
            efermi=opts.efermi,
        )
        stage_result = await vasp_stage_wannier_for_tb2j(stage_opts, **kwargs)
        if not _ok(stage_result):
            return node_runner.fail(
                _err(stage_result, "vasp_stage_wannier_for_tb2j failed")
            )

        efermi = _efermi_value(getattr(stage_result, "efermi", None))
        if efermi is None:
            efermi = opts.efermi
        if efermi is None:
            return node_runner.fail("efermi unknown after staging")

        efermi_data = FloatData(field_name="efermi", value=efermi)
        node_runner.efermi = efermi_data

        if opts.collinear:
            tb2j_opts = WannierCollinearInput(
                common=opts.tb2j,
                efermi=efermi,
                path=".",
                prefix_up=opts.prefix_up,
                prefix_down=opts.prefix_down,
                posfile=opts.posfile,
            )
            tb2j_result = await tb2j_wannier_collinear(tb2j_opts, **kwargs)
            step = "tb2j_wannier_collinear"
        else:
            tb2j_opts = WannierSpinorInput(
                common=opts.tb2j,
                efermi=efermi,
                path=".",
                prefix_spinor=opts.prefix_spinor,
                groupby=opts.groupby,
                posfile=opts.posfile,
            )
            tb2j_result = await tb2j_wannier_spinor(tb2j_opts, **kwargs)
            step = "tb2j_wannier_spinor"

        if not _ok(tb2j_result):
            return node_runner.fail(_err(tb2j_result, f"{step} failed"))

        collected = []
        for part in (vasp_result, wannier_result, stage_result, tb2j_result):
            files = getattr(part, "files", None) or []
            collected.extend(files)
        node_runner.files = collected
        node_runner.info(f"vasp_wannier_tb2j done; efermi={efermi}")
        return node_runner.succeed()
    except Exception as exc:
        node_runner.error(f"vasp_wannier_tb2j: {exc}")
        return node_runner.fail(str(exc))
