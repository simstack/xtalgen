"""Top-level VASP job input model."""

from typing import Optional

from odmantic import Field, Model, Reference
from pydantic import model_validator

from simstack.models import FileStack, simstack_model
from simstack.models.file_list import FileListModel
from simstack.util.cleaned_json_schema import cleaned_json_schema
from simstack.util.generate_ui_schema import generate_ui_schema
from vasp.lib.incar import render_incar
from vasp.lib.kpoints import render_kpoints
from vasp.models.vasp_common import VaspIncarParams, VaspKpointsParams


def _unwrap_optional_schema(schema: dict | None) -> dict | None:
    """Drop ``anyOf`` [T, null] so RJSF does not render a null/object dropdown."""
    if schema is None:
        return None
    if "anyOf" not in schema:
        return schema
    non_null = [s for s in schema["anyOf"] if s.get("type") != "null"]
    if len(non_null) != 1:
        return schema
    out = dict(non_null[0])
    for key in ("title", "description"):
        if key in schema:
            out[key] = schema[key]
    return out


@simstack_model
class VaspJobInput(Model):
    """
    Inputs for a VASP working directory (cwd).

    ``poscar`` is required. ``potcar`` is required unless ``potcar_autobuild``
    is True (then POTCAR is built from POSCAR species using
    ``[*.program.vasp] potcar_dir``).

    Set ``use_incar_file`` / ``use_kpoints_file`` to bypass generated content.
    Set ``use_extra_files`` to stage additional files (e.g. wannier90*.win).

    The VASP binary / launcher come from ``config.toml``
    (``[<resource>.program.vasp] run_command``). MPI ranks come from
    ``kwargs["parent_parameters"].slurm_parameters`` via the job allocation.
    """

    field_name: str = "VaspJobInput"
    incar: VaspIncarParams = Field(default_factory=VaspIncarParams)
    kpoints: VaspKpointsParams = Field(default_factory=VaspKpointsParams)
    poscar: FileStack = Reference()
    potcar_autobuild: bool = Field(
        False,
        json_schema_extra={"title": "Autobuild POTCAR from POSCAR"},
        description=(
            "Build POTCAR from POSCAR species using "
            "[*.program.vasp] potcar_dir (no potcar upload)"
        ),
    )
    potcar: Optional[FileStack] = Field(
        None, description="POTCAR FileStack (required when potcar_autobuild is False)"
    )
    use_incar_file: bool = Field(
        False,
        json_schema_extra={"title": "Use pre-built INCAR file"},
        description="Use incar_file instead of generating",
    )
    incar_file: Optional[FileStack] = Field(None, description="Pre-built INCAR")
    use_kpoints_file: bool = Field(
        False,
        json_schema_extra={"title": "Use pre-built KPOINTS file"},
        description="Use kpoints_file instead of generating",
    )
    kpoints_file: Optional[FileStack] = Field(None, description="Pre-built KPOINTS")
    use_extra_files: bool = Field(
        False,
        json_schema_extra={"title": "Stage extra files"},
        description="Stage additional files into the VASP working directory",
    )
    extra_files: Optional[FileListModel] = Field(
        None, description="Additional files to stage (e.g. wannier90*.win)"
    )

    @model_validator(mode="before")
    @classmethod
    def sync_optional_toggles(cls, data):
        """Infer UI toggles from existing docs; clear optionals when toggles are off."""
        if not isinstance(data, dict):
            return data

        if "field_name" not in data:
            data["field_name"] = cls.__name__

        if "potcar_autobuild" not in data:
            # Legacy docs always had potcar; treat missing flag as upload mode.
            data["potcar_autobuild"] = data.get("potcar") is None
        if data.get("potcar_autobuild"):
            data["potcar"] = None

        if "use_incar_file" not in data:
            data["use_incar_file"] = data.get("incar_file") is not None
        if not data.get("use_incar_file"):
            data["incar_file"] = None

        if "use_kpoints_file" not in data:
            data["use_kpoints_file"] = data.get("kpoints_file") is not None
        if not data.get("use_kpoints_file"):
            data["kpoints_file"] = None

        if "use_extra_files" not in data:
            extras = data.get("extra_files")
            has_extras = extras is not None and (
                getattr(extras, "elements", None)
                or (isinstance(extras, dict) and extras.get("elements"))
            )
            data["use_extra_files"] = bool(has_extras)
        if not data.get("use_extra_files"):
            data["extra_files"] = None

        return data

    @model_validator(mode="after")
    def require_potcar_or_autobuild(self):
        if not self.potcar_autobuild and self.potcar is None:
            raise ValueError("potcar is required when potcar_autobuild is False")
        return self

    def incar_text(self) -> str:
        return render_incar(self.incar)

    def kpoints_text(self) -> str:
        return render_kpoints(self.kpoints)

    @classmethod
    def json_schema(cls, recursive=True):
        """
        JSON schema with optional file inputs gated by use_* / potcar_autobuild.

        When ``potcar_autobuild`` is True, hide ``potcar``; when False, show it.
        """
        schema = cleaned_json_schema(cls)
        schema["title"] = cls.__name__

        prop_schemas = schema["properties"]

        incar_schema = prop_schemas.pop("incar", None)
        incar_file_schema = _unwrap_optional_schema(
            prop_schemas.pop("incar_file", None)
        )
        kpoints_schema = prop_schemas.pop("kpoints", None)
        kpoints_file_schema = _unwrap_optional_schema(
            prop_schemas.pop("kpoints_file", None)
        )
        potcar_schema = _unwrap_optional_schema(prop_schemas.pop("potcar", None))
        extra_files_schema = _unwrap_optional_schema(
            prop_schemas.pop("extra_files", None)
        )

        if "dependencies" not in schema:
            schema["dependencies"] = {}

        schema["dependencies"].update(
            {
                "potcar_autobuild": {
                    "oneOf": [
                        {
                            "properties": {
                                "potcar_autobuild": {"const": False},
                                "potcar": potcar_schema,
                            }
                        },
                        {
                            "properties": {
                                "potcar_autobuild": {"const": True},
                            }
                        },
                    ]
                },
                "use_incar_file": {
                    "oneOf": [
                        {
                            "properties": {
                                "use_incar_file": {"const": False},
                                "incar": incar_schema,
                            }
                        },
                        {
                            "properties": {
                                "use_incar_file": {"const": True},
                                "incar_file": incar_file_schema,
                            }
                        },
                    ]
                },
                "use_kpoints_file": {
                    "oneOf": [
                        {
                            "properties": {
                                "use_kpoints_file": {"const": False},
                                "kpoints": kpoints_schema,
                            }
                        },
                        {
                            "properties": {
                                "use_kpoints_file": {"const": True},
                                "kpoints_file": kpoints_file_schema,
                            }
                        },
                    ]
                },
                "use_extra_files": {
                    "oneOf": [
                        {
                            "properties": {
                                "use_extra_files": {"const": False},
                            }
                        },
                        {
                            "properties": {
                                "use_extra_files": {"const": True},
                                "extra_files": extra_files_schema,
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

        ui_schema["potcar_autobuild"] = {
            "ui:widget": "checkbox",
            "ui:title": "Autobuild POTCAR from POSCAR",
        }
        ui_schema.setdefault("potcar", {})["ui:condition"] = {
            "potcar_autobuild": False
        }

        ui_schema["use_incar_file"] = {
            "ui:widget": "checkbox",
            "ui:title": "Use pre-built INCAR file",
        }
        # Merge condition into FileField / GenericFormField — do not replace.
        ui_schema.setdefault("incar", {})["ui:condition"] = {"use_incar_file": False}
        ui_schema.setdefault("incar_file", {})["ui:condition"] = {
            "use_incar_file": True
        }

        ui_schema["use_kpoints_file"] = {
            "ui:widget": "checkbox",
            "ui:title": "Use pre-built KPOINTS file",
        }
        ui_schema.setdefault("kpoints", {})["ui:condition"] = {
            "use_kpoints_file": False
        }
        ui_schema.setdefault("kpoints_file", {})["ui:condition"] = {
            "use_kpoints_file": True
        }

        ui_schema["use_extra_files"] = {
            "ui:widget": "checkbox",
            "ui:title": "Stage extra files",
        }
        ui_schema.setdefault("extra_files", {})["ui:condition"] = {
            "use_extra_files": True
        }

        ui_schema["ui:order"] = [
            "poscar",
            "potcar_autobuild",
            "potcar",
            "use_incar_file",
            "incar",
            "incar_file",
            "use_kpoints_file",
            "kpoints",
            "kpoints_file",
            "use_extra_files",
            "extra_files",
            "id",
        ]
        if "ui:options" not in ui_schema:
            ui_schema["ui:options"] = {}
        ui_schema["ui:options"]["ui:foldable"] = True

        return ui_schema
