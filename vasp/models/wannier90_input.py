"""Wannier90 input / run models for VASP workflows."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from odmantic import EmbeddedModel, Field, Model

from simstack.models import FileStack, simstack_model
from simstack.models.file_list import FileListIO
from vasp.lib.win import render_wannier90_win


class Wannier90Channel(str, Enum):
    """Which .win / seedname to write or run."""

    UP = "wannier90.up"
    DOWN = "wannier90.dn"
    SPINOR = "wannier90"


@simstack_model
class Wannier90WinParams(EmbeddedModel):
    """Parameters for a Wannier90 ``.win`` (projections + disentanglement)."""

    num_wann: int = Field(28, description="Number of Wannier functions")
    num_bands: int = Field(48, description="Number of bands (match VASP NBANDS)")
    num_iter: int = Field(300, description="MLWF iterations")
    guiding_centres: bool = Field(True, description="guiding_centres")
    write_hr: bool = Field(True, description="Write *_hr.dat (needed for TB2J)")
    write_xyz: bool = Field(True, description="Write *_centres.xyz")
    write_tb: bool = Field(True, description="Write *_tb.dat")
    spinors: bool = Field(False, description="spinors = true for SOC / NC")
    dis_win_min: Optional[float] = Field(
        None, description="Outer window min (eV, absolute)"
    )
    dis_win_max: Optional[float] = Field(
        None, description="Outer window max (eV, absolute)"
    )
    dis_froz_min: Optional[float] = Field(None, description="Frozen window min (eV)")
    dis_froz_max: Optional[float] = Field(None, description="Frozen window max (eV)")
    exclude_bands: str = Field("", description="exclude_bands list")
    mp_grid_x: Optional[int] = Field(None, description="Optional mp_grid x")
    mp_grid_y: Optional[int] = Field(None, description="Optional mp_grid y")
    mp_grid_z: Optional[int] = Field(None, description="Optional mp_grid z")
    projections: str = Field(
        "Mn: d\nO: p",
        description="Body of begin projections … end projections",
    )
    extra_win: str = Field("", description="Raw extra .win lines")


@simstack_model
class Wannier90WinInput(Model):
    """Single-channel .win description (helper / tests; not a @node)."""

    field_name: str = "Wannier90WinInput"
    channel: Wannier90Channel = Field(
        Wannier90Channel.UP,
        description="Seedname: wannier90.up / wannier90.dn / wannier90",
    )
    win: Wannier90WinParams = Field(default_factory=Wannier90WinParams)
    use_win_file: bool = Field(False, description="Stage win_file instead of generating")
    win_file: Optional[FileStack] = Field(None, description="Pre-built .win FileStack")

    def filename(self) -> str:
        seed = (
            self.channel.value
            if isinstance(self.channel, Wannier90Channel)
            else str(self.channel)
        )
        return f"{seed}.win"

    def win_text(self) -> str:
        return render_wannier90_win(self.win)


@simstack_model
class Wannier90RunInput(Model):
    """Write ``.win`` files (optional) then run ``wannier90.x`` for each seed."""

    field_name: str = "Wannier90RunInput"
    channels: str = Field(
        "wannier90.up wannier90.dn",
        description="Space-separated seednames (no .win suffix)",
    )
    win: Wannier90WinParams = Field(default_factory=Wannier90WinParams)
    write_win: bool = Field(True, description="Generate/stage .win before wannier90.x")
    win_files: Optional[FileListIO] = Field(
        None,
        description="Pre-built .win FileStacks (used instead of generating when set)",
    )
    binary: str = Field("wannier90.x", description="Wannier90 executable on PATH")
    work_dir: str = Field(".", description="Working directory")

    def seednames(self) -> list[str]:
        return [tok for tok in self.channels.split() if tok.strip()]

    def cli_args_for(self, seedname: str) -> list[str]:
        return [self.binary, seedname]


@simstack_model
class StageWannierForTB2JInput(Model):
    """
    Verify / collect Wannier90 outputs expected by ``tbj2`` wann2J nodes.

    Collinear needs ``{prefix_up,prefix_down}_hr.dat`` (+ centres).
    Spinor needs ``{prefix_spinor}_hr.dat`` (+ centres).
    """

    field_name: str = "StageWannierForTB2JInput"
    collinear: bool = Field(True, description="Collinear up/down vs spinor")
    prefix_up: str = Field("wannier90.up", description="Spin-up seedname")
    prefix_down: str = Field("wannier90.dn", description="Spin-down seedname")
    prefix_spinor: str = Field("wannier90", description="Spinor seedname")
    parse_efermi_from_outcar: bool = Field(
        True, description="Parse E-fermi from OUTCAR into node_runner.efermi"
    )
    outcar_path: str = Field("OUTCAR", description="OUTCAR path for E_F")
    efermi: Optional[float] = Field(
        None,
        description="Explicit E_F (eV); used if OUTCAR parse is off or fails",
    )
