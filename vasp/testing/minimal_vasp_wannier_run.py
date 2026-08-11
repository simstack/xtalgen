"""Minimal Fe VASP → Wannier90 helpers for cluster smoke tests."""

from simstack.core.context import context
from simstack.core.simstack_result import SimstackResult
from simstack.models import Parameters
from simstack.models.file_list import FileListModel
from simstack.models.files import FileStack
from vasp.lib.win import render_wannier90_win
from vasp.models.vasp_common import VaspIncarParams, VaspKpointsParams
from vasp.models.vasp_input import VaspJobInput
from vasp.models.vasp_wannier_minimal import VaspWannierMinimalInput
from vasp.models.wannier90_input import Wannier90RunInput, Wannier90WinParams
from vasp.nodes.vasp_wannier_minimal import vasp_wannier_minimal
from vasp.testing.minimal_vasp_run import fixture_poscar, fixture_potcar


def minimal_fe_win_params() -> Wannier90WinParams:
    """Tiny Fe ``d`` projection set for the 1-atom test cell."""
    return Wannier90WinParams(
        num_wann=5,
        num_bands=16,
        num_iter=50,
        guiding_centres=True,
        write_hr=True,
        write_xyz=True,
        write_tb=False,
        spinors=False,
        projections="Fe:d",
    )


def minimal_wannier90_win_stack(
    win: Wannier90WinParams | None = None,
) -> FileStack:
    """In-memory ``wannier90.win`` to stage into the VASP workdir."""
    params = win or minimal_fe_win_params()
    return FileStack.from_string(render_wannier90_win(params), "wannier90.win")


def minimal_vasp_wannier_job_input(
    *,
    poscar: FileStack | None = None,
    potcar: FileStack | None = None,
    potcar_autobuild: bool = True,
    win: Wannier90WinParams | None = None,
) -> VaspWannierMinimalInput:
    """
    Build Fe smoke inputs: VASP with ``LWANNIER90`` + staged ``wannier90.win``,
    then Wannier90 without regenerating the ``.win``.

    Default ``potcar_autobuild=True`` uses ``[*.program.vasp] potcar_dir``.
    """
    win_params = win or minimal_fe_win_params()
    win_stack = minimal_wannier90_win_stack(win_params)
    if potcar_autobuild:
        vasp = VaspJobInput(
            poscar=poscar or fixture_poscar(),
            potcar_autobuild=True,
            potcar=None,
            incar=VaspIncarParams(
                encut=300.0,
                ediff=1e-4,
                ismear=0,
                sigma=0.05,
                ispin=1,
                nsw=0,
                ibrion=-1,
                nelm=40,
                use_nbands=True,
                nbands=16,
                lwannier90=True,
                lwrite_mmn_amn=True,
                lwrite_unk=False,
                lsorbit=False,
            ),
            kpoints=VaspKpointsParams(nx=2, ny=2, nz=2),
            use_extra_files=True,
            extra_files=FileListModel(elements=[win_stack]),
        )
    else:
        vasp = VaspJobInput(
            poscar=poscar or fixture_poscar(),
            potcar_autobuild=False,
            potcar=potcar or fixture_potcar(),
            incar=VaspIncarParams(
                encut=300.0,
                ediff=1e-4,
                ismear=0,
                sigma=0.05,
                ispin=1,
                nsw=0,
                ibrion=-1,
                nelm=40,
                use_nbands=True,
                nbands=16,
                lwannier90=True,
                lwrite_mmn_amn=True,
                lwrite_unk=False,
                lsorbit=False,
            ),
            kpoints=VaspKpointsParams(nx=2, ny=2, nz=2),
            use_extra_files=True,
            extra_files=FileListModel(elements=[win_stack]),
        )
    wannier = Wannier90RunInput(
        channels="wannier90",
        win=win_params,
        write_win=False,
        use_win_files=False,
    )
    return VaspWannierMinimalInput(vasp=vasp, wannier=wannier)


async def submit_minimal_vasp_wannier_run(
    *,
    resource: str = "xtalgen-int-nano",
    force_rerun: bool = True,
    opts: VaspWannierMinimalInput | None = None,
) -> SimstackResult:
    """
    Initialize context and submit the Fe VASP → Wannier90 smoke chain.

    Requires ``vasp/testing/POTCAR``, ``wannier90.x`` on the resource, and
    ``[<resource>.program.vasp|wannier90]`` in ``config.toml``.
    """
    await context.initialize()
    parameters = Parameters(resource=resource, force_rerun=force_rerun)
    job = opts or minimal_vasp_wannier_job_input()
    return await vasp_wannier_minimal(job, parameters=parameters)


async def main() -> None:
    result = await submit_minimal_vasp_wannier_run()
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
