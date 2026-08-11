"""Minimal VASP fixtures and a helper to submit ``vasp_run``."""

from __future__ import annotations

import os
from pathlib import Path

from simstack.core.context import context
from simstack.core.simstack_result import SimstackResult
from simstack.models import Parameters
from simstack.models.files import FileStack
from vasp.models.vasp_common import VaspIncarParams, VaspKpointsParams
from vasp.models.vasp_input import VaspJobInput
from vasp.nodes.run_vasp import vasp_run

_FIXTURE_DIR = Path(__file__).resolve().parent
POSCAR_PATH = _FIXTURE_DIR / "POSCAR"
# Optional on-disk location (gitignored); stub content lives in code.
POTCAR_PATH = _FIXTURE_DIR / "POTCAR"

# Not a licensed PAW potential — staging / unit tests only.
_POTCAR_STUB = """\
  TEST_STUB Fe — not a licensed VASP PAW potential; staging / unit tests only
   8.0000000000000000
 parameters from PSCTR are:
   VRHFIN =Fe: TEST
   LEXCH  = PE
   EATOM  =    0.0000 eV,    0.0000 Ry
 END of PSCTR-controll parameters
   0.00000000
END of TEST_STUB POTCAR for Fe
"""


def fixture_poscar(*, in_memory: bool = True) -> FileStack:
    """Load the bundled 1-atom Fe test POSCAR as a FileStack."""
    return FileStack.from_local_file(
        str(POSCAR_PATH), in_memory=in_memory, is_hashable=True
    )


def fixture_potcar(*, in_memory: bool = True) -> FileStack:
    """
    Load a POTCAR FileStack for tests.

    Prefer (in order):
    1. ``vasp/testing/POTCAR`` on disk (gitignored — copy a real PAW file there)
    2. ``$VASP_POTCAR`` / ``$VASP_PP_PATH`` Fe potential (``potpaw_PBE.54/Fe/POTCAR``)
    3. Embedded stub (unit tests only — VASP will EOF on a real run)
    """
    if POTCAR_PATH.is_file() and POTCAR_PATH.stat().st_size > 200:
        return FileStack.from_local_file(
            str(POTCAR_PATH), in_memory=in_memory, is_hashable=True
        )

    for env in ("VASP_POTCAR", "VASP_PP_PATH"):
        root = Path(os.environ[env]) if env in os.environ else None
        if root is None or not root.is_dir():
            continue
        for rel in (
            "potpaw_PBE.54/Fe/POTCAR",
            "potpaw_PBE/Fe/POTCAR",
            "potpaw_PBE.52/Fe/POTCAR",
            "Fe/POTCAR",
        ):
            candidate = root / rel
            if candidate.is_file():
                return FileStack.from_local_file(
                    str(candidate), in_memory=in_memory, is_hashable=True
                )

    if in_memory:
        return FileStack.from_string(_POTCAR_STUB, "POTCAR")
    POTCAR_PATH.write_text(_POTCAR_STUB, encoding="utf-8")
    return FileStack.from_local_file(
        str(POTCAR_PATH), in_memory=False, is_hashable=True
    )


def minimal_vasp_job_input(
    *,
    poscar: FileStack | None = None,
    potcar: FileStack | None = None,
    incar: VaspIncarParams | None = None,
    kpoints: VaspKpointsParams | None = None,
) -> VaspJobInput:
    """Build a small static ``VaspJobInput`` using test fixtures by default."""
    return VaspJobInput(
        poscar=poscar or fixture_poscar(),
        potcar=potcar or fixture_potcar(),
        incar=incar
        or VaspIncarParams(
            encut=200.0,
            ediff=1e-4,
            ismear=0,
            sigma=0.05,
            ispin=1,
            nsw=0,
            ibrion=-1,
            nelm=40,
            lwannier90=False,
            lwrite_mmn_amn=False,
            lwrite_unk=False,
            lsorbit=False,
        ),
        kpoints=kpoints or VaspKpointsParams(nx=1, ny=1, nz=1),
    )


async def submit_minimal_vasp_run(
    *,
    resource: str = "local",
    force_rerun: bool = True,
    opts: VaspJobInput | None = None,
) -> SimstackResult:
    """
    Initialize context and submit a minimal ``vasp_run`` job.

    Uses ``vasp/testing/POSCAR`` and the POTCAR test stub unless ``opts`` is
    provided. Requires ``[<resource>.program.vasp] run_command`` in config.toml
    and a VASP binary on PATH (or via the configured launcher).
    """
    await context.initialize()
    parameters = Parameters(resource=resource, force_rerun=force_rerun)
    job = opts or minimal_vasp_job_input()
    return await vasp_run(job, parameters=parameters)


async def main() -> None:
    result = await submit_minimal_vasp_run()
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
