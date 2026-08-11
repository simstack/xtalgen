"""Siesta → TB2J input model."""

from __future__ import annotations

from typing import Optional

from odmantic import Field, Model

from simstack.models import FileStack, simstack_model
from simstack.models.file_list import FileListModel
from tbj2.lib.cli import append_common_args, append_flag
from tbj2.models.tb2j_common import TB2JCommonParams


@simstack_model
class SiestaInput(Model):
    """Options for ``siesta2J.py``."""

    field_name: str = "SiestaInput"
    common: TB2JCommonParams = Field(default_factory=TB2JCommonParams)
    fdf_fname: Optional[FileStack] = Field(
        None, description="Siesta .fdf input (staged to cwd if provided)"
    )
    fdf_path: str = Field(
        "./",
        description="Path passed to --fdf_fname when fdf_fname FileStack is unset",
    )
    fname: str = Field("exchange.xml", description="Output XML filename inside results")
    split_soc: bool = Field(False, description="Read SOC from a separate Siesta file")
    efermi: Optional[float] = Field(
        None, description="Optional E_F override; usually read from Siesta output"
    )
    input_files: Optional[FileListModel] = Field(
        None, description="HS / NetCDF / related Siesta outputs to stage into cwd"
    )

    def cli_args(self, *, fdf_name: str | None = None) -> list[str]:
        args = ["siesta2J.py"]
        append_flag(args, "--fdf_fname", fdf_name or self.fdf_path)
        append_flag(args, "--fname", self.fname)
        append_flag(args, "--split_soc", self.split_soc)
        append_flag(args, "--efermi", self.efermi)
        append_common_args(args, self.common)
        return args
