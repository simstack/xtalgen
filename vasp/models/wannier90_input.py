"""Wannier90 input / run models for VASP workflows."""

from enum import Enum
from typing import Optional

from odmantic import EmbeddedModel, Field, Model
from pydantic import model_validator

from simstack.models import FileStack, simstack_model
from simstack.models.file_list import FileListModel
from simstack.util.cleaned_json_schema import cleaned_json_schema
from simstack.util.generate_ui_schema import generate_ui_schema
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
    use_dis_params: bool = Field(
        False,
        json_schema_extra={"title": "Disentanglement windows"},
        description="Expose dis_win_* / dis_froz_* parameters",
    )
    dis_win_min: Optional[float] = Field(
        None, description="Outer window min (eV, absolute)"
    )
    dis_win_max: Optional[float] = Field(
        None, description="Outer window max (eV, absolute)"
    )
    dis_froz_min: Optional[float] = Field(None, description="Frozen window min (eV)")
    dis_froz_max: Optional[float] = Field(None, description="Frozen window max (eV)")
    exclude_bands: str = Field("", description="exclude_bands list")
    use_grid: bool = Field(
        False,
        json_schema_extra={"title": "Override mp_grid"},
        description="Expose mp_grid_x / mp_grid_y / mp_grid_z",
    )
    mp_grid_x: Optional[int] = Field(None, description="Optional mp_grid x")
    mp_grid_y: Optional[int] = Field(None, description="Optional mp_grid y")
    mp_grid_z: Optional[int] = Field(None, description="Optional mp_grid z")
    projections: str = Field(
        "Mn: d\nO: p",
        description="Body of begin projections … end projections",
    )
    extra_win: str = Field("", description="Raw extra .win lines")

    @model_validator(mode="before")
    @classmethod
    def sync_optional_toggles(cls, data):
        """Infer UI toggles from existing docs; clear optionals when toggles are off."""
        if not isinstance(data, dict):
            return data

        dis_fields = ("dis_win_min", "dis_win_max", "dis_froz_min", "dis_froz_max")
        if "use_dis_params" not in data:
            data["use_dis_params"] = any(data.get(f) is not None for f in dis_fields)
        if not data.get("use_dis_params"):
            for f in dis_fields:
                data[f] = None

        grid_fields = ("mp_grid_x", "mp_grid_y", "mp_grid_z")
        if "use_grid" not in data:
            data["use_grid"] = any(data.get(f) is not None for f in grid_fields)
        if not data.get("use_grid"):
            for f in grid_fields:
                data[f] = None

        return data

    @classmethod
    def json_schema(cls, recursive=True):
        schema = cleaned_json_schema(cls)
        schema["title"] = cls.__name__

        prop_schemas = schema["properties"]
        dis_fields = ("dis_win_min", "dis_win_max", "dis_froz_min", "dis_froz_max")
        grid_fields = ("mp_grid_x", "mp_grid_y", "mp_grid_z")

        dis_schemas = {
            f: prop_schemas.pop(f) for f in dis_fields if f in prop_schemas
        }
        grid_schemas = {
            f: prop_schemas.pop(f) for f in grid_fields if f in prop_schemas
        }

        # Plain number/integer for Optional scalars (avoid anyOf null dropdown)
        for name, sub in list(dis_schemas.items()):
            if sub is not None and "anyOf" in sub:
                dis_schemas[name] = {
                    "type": "number",
                    "title": sub.get("title", name),
                    "description": sub.get("description", ""),
                }
        for name, sub in list(grid_schemas.items()):
            if sub is not None and "anyOf" in sub:
                grid_schemas[name] = {
                    "type": "integer",
                    "title": sub.get("title", name),
                    "description": sub.get("description", ""),
                }

        if "dependencies" not in schema:
            schema["dependencies"] = {}

        schema["dependencies"].update(
            {
                "use_dis_params": {
                    "oneOf": [
                        {
                            "properties": {
                                "use_dis_params": {"const": False},
                            }
                        },
                        {
                            "properties": {
                                "use_dis_params": {"const": True},
                                **dis_schemas,
                            }
                        },
                    ]
                },
                "use_grid": {
                    "oneOf": [
                        {
                            "properties": {
                                "use_grid": {"const": False},
                            }
                        },
                        {
                            "properties": {
                                "use_grid": {"const": True},
                                **grid_schemas,
                            }
                        },
                    ]
                },
            }
        )

        return schema

    @classmethod
    def ui_schema(cls):
        ui_schema = generate_ui_schema(cls)

        ui_schema["use_dis_params"] = {
            "ui:widget": "checkbox",
            "ui:title": "Disentanglement windows",
        }
        for field in ("dis_win_min", "dis_win_max", "dis_froz_min", "dis_froz_max"):
            ui_schema[field] = {"ui:condition": {"use_dis_params": True}}

        ui_schema["use_grid"] = {
            "ui:widget": "checkbox",
            "ui:title": "Override mp_grid",
        }
        for field in ("mp_grid_x", "mp_grid_y", "mp_grid_z"):
            ui_schema[field] = {"ui:condition": {"use_grid": True}}

        ui_schema["ui:order"] = [
            "num_wann",
            "num_bands",
            "num_iter",
            "guiding_centres",
            "write_hr",
            "write_xyz",
            "write_tb",
            "spinors",
            "use_dis_params",
            "dis_win_min",
            "dis_win_max",
            "dis_froz_min",
            "dis_froz_max",
            "exclude_bands",
            "use_grid",
            "mp_grid_x",
            "mp_grid_y",
            "mp_grid_z",
            "projections",
            "extra_win",
        ]
        if "ui:options" not in ui_schema:
            ui_schema["ui:options"] = {}
        ui_schema["ui:options"]["ui:foldable"] = True

        return ui_schema


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
    write_win: bool = Field(
        True,
        json_schema_extra={"title": "Generate .win files"},
        description="Generate/stage .win before wannier90.x",
    )
    use_win_files: bool = Field(
        False,
        json_schema_extra={"title": "Use pre-built .win files"},
        description="Stage win_files instead of generating from win params",
    )
    win_files: Optional[FileListModel] = Field(
        None,
        description="Pre-built .win FileStacks (used instead of generating when set)",
    )

    @model_validator(mode="before")
    @classmethod
    def sync_optional_toggles(cls, data):
        """Infer UI toggles from existing docs; clear optionals when toggles are off."""
        if not isinstance(data, dict):
            return data

        if "field_name" not in data:
            data["field_name"] = cls.__name__

        if "use_win_files" not in data:
            win_files = data.get("win_files")
            has_files = win_files is not None and (
                getattr(win_files, "elements", None)
                or (isinstance(win_files, dict) and win_files.get("elements"))
                or (
                    hasattr(win_files, "__iter__")
                    and not isinstance(win_files, (str, bytes, dict))
                    and any(True for _ in win_files)
                )
            )
            data["use_win_files"] = bool(has_files)
        if not data.get("use_win_files"):
            data["win_files"] = None

        return data

    def seednames(self) -> list[str]:
        return [tok for tok in self.channels.split() if tok.strip()]

    @classmethod
    def json_schema(cls, recursive=True):
        """
        JSON schema with optional .win inputs gated by use_* / write_win.

        ``use_win_files`` shows ``win_files`` and hides generated ``win`` params.
        ``write_win`` (when not using pre-built files) shows ``win``.
        """
        schema = cleaned_json_schema(cls)
        schema["title"] = cls.__name__

        prop_schemas = schema["properties"]
        win_schema = prop_schemas.pop("win", None)
        win_files_schema = prop_schemas.pop("win_files", None)
        # Drop anyOf [FileListModel, null] so RJSF does not show a null/object dropdown
        if win_files_schema is not None and "anyOf" in win_files_schema:
            non_null = [
                s for s in win_files_schema["anyOf"] if s.get("type") != "null"
            ]
            if len(non_null) == 1:
                unwrapped = dict(non_null[0])
                for key in ("title", "description"):
                    if key in win_files_schema:
                        unwrapped[key] = win_files_schema[key]
                win_files_schema = unwrapped

        if "dependencies" not in schema:
            schema["dependencies"] = {}

        schema["dependencies"].update(
            {
                "use_win_files": {
                    "oneOf": [
                        {
                            "properties": {
                                "use_win_files": {"const": False},
                            }
                        },
                        {
                            "properties": {
                                "use_win_files": {"const": True},
                                "win_files": win_files_schema,
                            }
                        },
                    ]
                },
                "write_win": {
                    "oneOf": [
                        {
                            "properties": {
                                "write_win": {"const": False},
                            }
                        },
                        {
                            "properties": {
                                "write_win": {"const": True},
                                "win": win_schema,
                            }
                        },
                    ]
                },
            }
        )

        return schema

    @classmethod
    def ui_schema(cls):
        ui_schema = generate_ui_schema(cls)

        ui_schema["field_name"] = {"ui:widget": "hidden"}

        ui_schema["use_win_files"] = {
            "ui:widget": "checkbox",
            "ui:title": "Use pre-built .win files",
        }
        ui_schema.setdefault("win_files", {})["ui:condition"] = {"use_win_files": True}

        ui_schema["write_win"] = {
            "ui:widget": "checkbox",
            "ui:title": "Generate .win files",
            "ui:condition": {"use_win_files": False},
        }
        ui_schema.setdefault("win", {})["ui:condition"] = {
            "write_win": True,
            "use_win_files": False,
        }

        ui_schema["ui:order"] = [
            "channels",
            "use_win_files",
            "win_files",
            "write_win",
            "win",
            "id",
        ]
        if "ui:options" not in ui_schema:
            ui_schema["ui:options"] = {}
        ui_schema["ui:options"]["ui:foldable"] = True

        return ui_schema


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
        True,
        description="Parse E-fermi from OUTCAR into node_runner.efermi as FloatData",
    )
    outcar_path: str = Field("OUTCAR", description="OUTCAR path for E_F")
    efermi: Optional[float] = Field(
        None,
        description="Explicit E_F (eV); used if OUTCAR parse is off or fails",
    )
