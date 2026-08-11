"""TB2J_rotate.py input model."""

from __future__ import annotations

from typing import Optional

from odmantic import Field, Model

from simstack.models import FileStack, simstack_model
from tbj2.lib.cli import append_flag


@simstack_model
class TB2JRotateInput(Model):
    """Options for ``TB2J_rotate.py`` (structure rotate-and-merge prep)."""

    field_name: str = "TB2JRotateInput"
    structure: Optional[FileStack] = Field(
        None, description="Input structure FileStack (staged if provided)"
    )
    structure_path: str = Field(
        "POSCAR",
        description="Structure path when structure FileStack is unset",
    )
    ftype: str = Field("vasp", description="ASE/output format (vasp, xyz, …)")
    noncollinear: bool = Field(
        False,
        description="Generate 6 structures (full Jani) instead of 3",
    )

    def cli_args(self, *, structure_name: str | None = None) -> list[str]:
        args = ["TB2J_rotate.py", structure_name or self.structure_path]
        append_flag(args, "--ftype", self.ftype)
        append_flag(args, "--noncollinear", self.noncollinear)
        return args
