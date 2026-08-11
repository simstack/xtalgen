"""Wannier90 → TB2J input models."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from odmantic import Field, Model

from simstack.models import FileStack, simstack_model
from simstack.models.file_list import FileListIO
from tbj2.lib.cli import append_common_args, append_flag
from tbj2.models.tb2j_common import TB2JCommonParams


class WannierGroupBy(str, Enum):
    SPIN = "spin"
    ORBITAL = "orbital"


@simstack_model
class WannierCollinearInput(Model):
    """Options for collinear ``wann2J.py`` (spin-up / spin-down Wannier90)."""

    field_name: str = "WannierCollinearInput"
    common: TB2JCommonParams = Field(default_factory=TB2JCommonParams)
    efermi: float = Field(..., description="Fermi energy (eV) from DFT; required for Wannier")
    path: str = Field("./", description="Directory containing Wannier90 files")
    prefix_up: str = Field("wannier90.up", description="Spin-up Wannier90 prefix")
    prefix_down: str = Field("wannier90.dn", description="Spin-down Wannier90 prefix")
    posfile: Optional[FileStack] = Field(
        None, description="Optional structure file (POSCAR, .pwi, …)"
    )
    input_files: Optional[FileListIO] = Field(
        None, description="Wannier90 outputs to stage into path (hr/centres/tb/win)"
    )

    def cli_args(self, *, posfile_name: str | None = None) -> list[str]:
        args = ["wann2J.py", "--path", self.path]
        append_flag(args, "--prefix_up", self.prefix_up)
        append_flag(args, "--prefix_down", self.prefix_down)
        append_flag(args, "--efermi", self.efermi)
        if posfile_name:
            append_flag(args, "--posfile", posfile_name)
        append_common_args(args, self.common)
        return args


@simstack_model
class WannierSpinorInput(Model):
    """Options for non-collinear / SOC ``wann2J.py --spinor``."""

    field_name: str = "WannierSpinorInput"
    common: TB2JCommonParams = Field(default_factory=TB2JCommonParams)
    efermi: float = Field(..., description="Fermi energy (eV) from DFT; required for Wannier")
    path: str = Field("./", description="Directory containing Wannier90 files")
    prefix_spinor: str = Field("wannier90", description="Spinor Wannier90 prefix")
    groupby: WannierGroupBy = Field(
        WannierGroupBy.SPIN,
        description="Basis ordering: spin or orbital",
    )
    posfile: Optional[FileStack] = Field(
        None, description="Optional structure file (POSCAR, .pwi, …)"
    )
    input_files: Optional[FileListIO] = Field(
        None, description="Wannier90 outputs to stage into path"
    )

    def cli_args(self, *, posfile_name: str | None = None) -> list[str]:
        args = [
            "wann2J.py",
            "--spinor",
            "--path",
            self.path,
            "--groupby",
            self.groupby.value,
        ]
        append_flag(args, "--prefix_spinor", self.prefix_spinor)
        append_flag(args, "--efermi", self.efermi)
        if posfile_name:
            append_flag(args, "--posfile", posfile_name)
        append_common_args(args, self.common)
        return args
