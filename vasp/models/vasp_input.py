"""Top-level VASP job input model."""

from __future__ import annotations

from typing import Optional

from odmantic import Field, Model

from simstack.models import FileStack, simstack_model
from simstack.models.file_list import FileListIO
from vasp.lib.incar import render_incar
from vasp.lib.kpoints import render_kpoints
from vasp.models.vasp_common import VaspIncarParams, VaspKpointsParams


@simstack_model
class VaspJobInput(Model):
    """
    Inputs for a VASP working directory (cwd).

    Provide ``poscar`` and ``potcar`` FileStacks (or stage them upstream).
    Set ``use_incar_file`` / ``use_kpoints_file`` to bypass generated content.

    The VASP binary / launcher come from ``config.toml``
    (``[<resource>.program.vasp] run_command``). MPI ranks come from
    ``kwargs["parent_parameters"].slurm_parameters`` via the job allocation.
    """

    field_name: str = "VaspJobInput"
    incar: VaspIncarParams = Field(default_factory=VaspIncarParams)
    kpoints: VaspKpointsParams = Field(default_factory=VaspKpointsParams)
    poscar: Optional[FileStack] = Field(None, description="POSCAR FileStack")
    potcar: Optional[FileStack] = Field(None, description="POTCAR FileStack (licensed)")
    use_incar_file: bool = Field(False, description="Use incar_file instead of generating")
    incar_file: Optional[FileStack] = Field(None, description="Pre-built INCAR")
    use_kpoints_file: bool = Field(
        False, description="Use kpoints_file instead of generating"
    )
    kpoints_file: Optional[FileStack] = Field(None, description="Pre-built KPOINTS")
    extra_files: Optional[FileListIO] = Field(
        None, description="Additional files to stage (e.g. wannier90*.win)"
    )

    def incar_text(self) -> str:
        return render_incar(self.incar)

    def kpoints_text(self) -> str:
        return render_kpoints(self.kpoints)
