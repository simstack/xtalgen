"""VASP INCAR / KPOINTS parameter models (EmbeddedModel composition)."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from odmantic import EmbeddedModel, Field

from simstack.models import simstack_model


class KpointsStyle(str, Enum):
    GAMMA = "Gamma"
    MONKHORST = "Monkhorst"


@simstack_model
class VaspIncarParams(EmbeddedModel):
    """Common INCAR tags for ground-state + Wannier90 interface runs."""

    encut: float = Field(520.0, description="Plane-wave cutoff (eV)")
    ediff: float = Field(1e-7, description="Electronic convergence")
    algo: str = Field("Normal", description="Electronic minimizer")
    prec: str = Field("Normal", description="Precision")
    ismear: int = Field(-5, description="Smearing method")
    sigma: float = Field(0.1, description="Smearing width (eV)")
    ispin: int = Field(2, description="1 = non-spin, 2 = collinear spin")
    nsw: int = Field(0, description="Ionic steps (0 = static)")
    ibrion: int = Field(-1, description="Ionic algorithm (-1 with NSW=0)")
    isif: int = Field(2, description="Stress/relax degrees of freedom")
    nelm: int = Field(100, description="Max SCF steps")
    lreal: bool = Field(False, description="Real-space projection")
    nbands: Optional[int] = Field(None, description="Number of bands")
    gga: str = Field("PE", description="GGA functional tag (e.g. PE, PS)")
    magmom: str = Field("", description="MAGMOM line (raw INCAR tokens)")
    ldau: bool = Field(False, description="Enable DFT+U")
    ldautype: int = Field(2, description="LDAUTYPE")
    ldaul: str = Field("", description="LDAUL values")
    ldauu: str = Field("", description="LDAUU values (eV)")
    ldauj: str = Field("", description="LDAUJ values (eV)")
    lmaxmix: int = Field(4, description="LMAXMIX for +U")
    lwannier90: bool = Field(True, description="Write Wannier90 interface files")
    lwrite_mmn_amn: bool = Field(True, description="Write .mmn / .amn")
    lwrite_unk: bool = Field(False, description="Write UNK files")
    lsorbit: bool = Field(False, description="Spin-orbit (requires vasp_ncl)")
    ncore: int = Field(1, description="NCORE")
    kpar: int = Field(1, description="KPAR")
    extra_incar: str = Field("", description="Raw extra INCAR lines")


@simstack_model
class VaspKpointsParams(EmbeddedModel):
    """Automatic k-mesh KPOINTS."""

    style: KpointsStyle = Field(KpointsStyle.GAMMA, description="Gamma or Monkhorst")
    nx: int = Field(8, description="Mesh along a*")
    ny: int = Field(8, description="Mesh along b*")
    nz: int = Field(8, description="Mesh along c*")
    shift_x: float = Field(0.0, description="Mesh shift a*")
    shift_y: float = Field(0.0, description="Mesh shift b*")
    shift_z: float = Field(0.0, description="Mesh shift c*")
