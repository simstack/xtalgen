"""Node: stage / verify Wannier90 outputs for TB2J wann2J nodes."""

from pathlib import Path

from simstack.core.node import node
from simstack.core.simstack_result import SimstackResult
from simstack.models import FloatData
from simstack.models.files import FileStack
from vasp.lib.cli import attach_file
from vasp.lib.outcar import parse_efermi
from vasp.models.wannier90_input import StageWannierForTB2JInput


def _require(prefix: str) -> list[str]:
    return [f"{prefix}_hr.dat", f"{prefix}_centres.xyz"]


@node
async def vasp_stage_wannier_for_tb2j(
    opts: StageWannierForTB2JInput, **kwargs
) -> SimstackResult:
    """
    Confirm TB2J-ready Wannier files exist and expose ``efermi`` for wann2J.

    Collinear: ``prefix_up`` / ``prefix_down``. Spinor: ``prefix_spinor``.
    Hand off to ``tbj2.tb2j_wannier_collinear`` / ``tbj2_wannier_spinor``.

    SimstackResult:
        files (List[FileStack]): Staged Wannier90 Hamiltonian / centres files for TB2J
        efermi (FloatData): Fermi energy (eV) for wann2J
    """
    node_runner = kwargs["node_runner"]
    try:
        required: list[str] = []
        if opts.collinear:
            required.extend(_require(opts.prefix_up))
            required.extend(_require(opts.prefix_down))
        else:
            required.extend(_require(opts.prefix_spinor))

        missing = [name for name in required if not Path(name).is_file()]
        if missing:
            return node_runner.fail(f"missing Wannier outputs: {', '.join(missing)}")

        collected: list[FileStack] = []
        for name in required:
            stack = attach_file(node_runner, name)
            if stack:
                collected.append(stack)

        efermi = opts.efermi
        if opts.parse_efermi_from_outcar:
            parsed = parse_efermi(opts.outcar_path)
            if parsed is not None:
                efermi = parsed

        if efermi is None:
            return node_runner.fail(
                "efermi unknown: provide StageWannierForTB2JInput.efermi or OUTCAR"
            )

        node_runner.efermi = FloatData(field_name="efermi", value=efermi)
        node_runner.files = collected
        node_runner.info(f"staged Wannier for TB2J; efermi={efermi}")
        return node_runner.succeed()
    except Exception as exc:
        node_runner.error(f"vasp_stage_wannier_for_tb2j: {exc}")
        return node_runner.fail(str(exc))
