"""Master input model for VASP → Wannier90 → TB2J workflows."""

from __future__ import annotations

from typing import Optional

from odmantic import Field, Model, Reference
from pydantic import model_validator

from simstack.models import FileStack, simstack_model
from simstack.util.cleaned_json_schema import cleaned_json_schema
from simstack.util.generate_ui_schema import generate_ui_schema
from tbj2.models.tb2j_common import TB2JCommonParams
from tbj2.models.wannier_input import WannierGroupBy
from vasp.models.vasp_input import VaspJobInput
from vasp.models.wannier90_input import Wannier90RunInput


@simstack_model
class VaspWannierTB2JInput(Model):
    """
    End-to-end crystal magnetism workflow:

    ``vasp_run`` → ``wannier90_run`` → ``vasp_stage_wannier_for_tb2j`` →
    ``tb2j_wannier_collinear`` or ``tb2j_wannier_spinor``.

    Crystal unit cell: set ``vasp.poscar`` (POSCAR FileStack). That is the
    structure VASP (and the rest of the pipeline) calculates.

    Set ``collinear=False`` (and ``LSORBIT`` / ``vasp_ncl`` via config) for SOC.
    ``efermi`` is taken from OUTCAR unless ``override_efermi`` is set.
    """

    field_name: str = "VaspWannierTB2JInput"
    collinear: bool = Field(
        True, description="Collinear up/down Wannier vs spinor/SOC"
    )
    vasp: VaspJobInput = Reference()
    wannier: Wannier90RunInput = Reference()
    tb2j: TB2JCommonParams = Field(default_factory=TB2JCommonParams)
    efermi: Optional[float] = Field(
        None,
        description="Override Fermi energy (eV); otherwise parse OUTCAR",
    )
    prefix_up: str = Field("wannier90.up", description="Spin-up Wannier90 seedname")
    prefix_down: str = Field("wannier90.dn", description="Spin-down Wannier90 seedname")
    prefix_spinor: str = Field("wannier90", description="Spinor Wannier90 seedname")
    groupby: WannierGroupBy = Field(
        WannierGroupBy.SPIN,
        description="Spinor basis ordering (spin or orbital)",
    )
    posfile: Optional[FileStack] = Field(
        None, description="Optional structure file for wann2J (--posfile)"
    )

    # UI persistence toggles (real fields so they are saved to the DB)
    override_efermi: bool = Field(
        False, json_schema_extra={"title": "Override Fermi energy"}
    )
    use_posfile: bool = Field(
        False, json_schema_extra={"title": "Provide TB2J structure file"}
    )

    @model_validator(mode="before")
    @classmethod
    def sync_optional_toggles(cls, data):
        """Infer UI toggles from existing docs; clear optionals when toggles are off."""
        if not isinstance(data, dict):
            return data

        if "field_name" not in data:
            data["field_name"] = cls.__name__

        if "override_efermi" not in data:
            data["override_efermi"] = data.get("efermi") is not None
        if not data.get("override_efermi"):
            data["efermi"] = None

        if "use_posfile" not in data:
            data["use_posfile"] = data.get("posfile") is not None
        if not data.get("use_posfile"):
            data["posfile"] = None

        return data

    @classmethod
    def json_schema(cls, recursive=True):
        """
        JSON schema with optional / mode-dependent fields gated by dependencies.

        :param recursive: Reserved for API parity with other simstack models.
        """
        schema = cleaned_json_schema(cls)
        schema["title"] = cls.__name__

        prop_schemas = schema["properties"]

        # Optional overrides
        efermi_schema = prop_schemas.pop("efermi", None)
        posfile_schema = prop_schemas.pop("posfile", None)

        # Collinear vs spinor seednames / groupby
        prefix_up_schema = prop_schemas.pop("prefix_up", None)
        prefix_down_schema = prop_schemas.pop("prefix_down", None)
        prefix_spinor_schema = prop_schemas.pop("prefix_spinor", None)
        groupby_schema = prop_schemas.pop("groupby", None)

        # Force plain number for Optional[float] (avoid anyOf null dropdown)
        if efermi_schema is not None and "anyOf" in efermi_schema:
            efermi_schema = {
                "type": "number",
                "title": efermi_schema.get("title", "efermi"),
                "description": efermi_schema.get(
                    "description", "Override Fermi energy (eV)"
                ),
            }

        # Drop anyOf [FileStack, null] so RJSF does not show a null/object dropdown
        if posfile_schema is not None and "anyOf" in posfile_schema:
            non_null = [
                s for s in posfile_schema["anyOf"] if s.get("type") != "null"
            ]
            if len(non_null) == 1:
                unwrapped = dict(non_null[0])
                for key in ("title", "description"):
                    if key in posfile_schema:
                        unwrapped[key] = posfile_schema[key]
                posfile_schema = unwrapped

        if "dependencies" not in schema:
            schema["dependencies"] = {}

        schema["dependencies"].update(
            {
                "override_efermi": {
                    "oneOf": [
                        {
                            "properties": {
                                "override_efermi": {"const": False},
                            }
                        },
                        {
                            "properties": {
                                "override_efermi": {"const": True},
                                "efermi": efermi_schema,
                            }
                        },
                    ]
                },
                "use_posfile": {
                    "oneOf": [
                        {
                            "properties": {
                                "use_posfile": {"const": False},
                            }
                        },
                        {
                            "properties": {
                                "use_posfile": {"const": True},
                                "posfile": posfile_schema,
                            }
                        },
                    ]
                },
                "collinear": {
                    "oneOf": [
                        {
                            "properties": {
                                "collinear": {"const": True},
                                "prefix_up": prefix_up_schema,
                                "prefix_down": prefix_down_schema,
                            }
                        },
                        {
                            "properties": {
                                "collinear": {"const": False},
                                "prefix_spinor": prefix_spinor_schema,
                                "groupby": groupby_schema,
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

        ui_schema["override_efermi"] = {
            "ui:widget": "checkbox",
            "ui:title": "Override Fermi energy",
        }
        ui_schema.setdefault("efermi", {})["ui:condition"] = {"override_efermi": True}

        ui_schema["use_posfile"] = {
            "ui:widget": "checkbox",
            "ui:title": "Provide TB2J structure file",
        }
        # Preserve FileField from generate_ui_schema; only add the condition.
        ui_schema.setdefault("posfile", {})["ui:condition"] = {"use_posfile": True}

        ui_schema.setdefault("prefix_up", {})["ui:condition"] = {"collinear": True}
        ui_schema.setdefault("prefix_down", {})["ui:condition"] = {"collinear": True}
        ui_schema.setdefault("prefix_spinor", {})["ui:condition"] = {"collinear": False}
        ui_schema.setdefault("groupby", {})["ui:condition"] = {"collinear": False}

        ui_schema["ui:order"] = [
            "vasp",
            "collinear",
            "prefix_up",
            "prefix_down",
            "prefix_spinor",
            "groupby",
            "wannier",
            "tb2j",
            "override_efermi",
            "efermi",
            "use_posfile",
            "posfile",
            "id",
        ]
        if "ui:options" not in ui_schema:
            ui_schema["ui:options"] = {}
        ui_schema["ui:options"]["ui:foldable"] = True

        return ui_schema
