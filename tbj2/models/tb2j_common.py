"""Shared TB2J calculation parameters (EmbeddedModel — composable, not inheritable)."""

from __future__ import annotations

from typing import Optional

from odmantic import EmbeddedModel, Field

from simstack.models import simstack_model


@simstack_model
class TB2JCommonParams(EmbeddedModel):
    """Parameters shared by wann2J / siesta2J style calculations."""

    elements: str = Field(
        "Fe",
        description="Space-separated magnetic elements (e.g. 'Fe Ni' or 'Fe_d')",
    )
    index_magnetic_atoms: str = Field(
        "",
        description="Optional 1-based magnetic atom indices (space-separated); overrides elements",
    )
    kmesh_x: int = Field(5, description="k-mesh along a*")
    kmesh_y: int = Field(5, description="k-mesh along b*")
    kmesh_z: int = Field(5, description="k-mesh along c*")
    emin: float = Field(-14.0, description="Lower energy bound relative to E_F (eV)")
    emax: float = Field(0.0, description="Upper energy bound relative to E_F (eV)")
    nz: int = Field(100, description="Contour integration points")
    np: int = Field(1, description="CPU cores for TB2J")
    rcut: Optional[float] = Field(
        None, description="Interaction cutoff (Angstrom); None = all R"
    )
    cutoff: float = Field(1e-5, description="Minimum |J| (eV) written to output")
    output_path: str = Field("TB2J_results", description="Output directory")
    description: str = Field(
        "Calculated with TB2J.", description="exchange.xml description"
    )
    use_cache: bool = Field(False, description="Disk-cache Hamiltonians to save RAM")
    orb_decomposition: bool = Field(
        False, description="Orbital decomposition (NC mode)"
    )
    ne: Optional[float] = Field(
        None, description="If set, adjust efermi to this electron count"
    )
