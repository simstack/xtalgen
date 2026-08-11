"""VASP INCAR / KPOINTS parameter models (EmbeddedModel composition)."""

from enum import Enum
from typing import Optional

from odmantic import EmbeddedModel, Field
from pydantic import model_validator

from simstack.models import simstack_model
from simstack.util.cleaned_json_schema import cleaned_json_schema
from simstack.util.generate_ui_schema import generate_ui_schema


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
    use_nbands: bool = Field(
        False,
        json_schema_extra={"title": "Set NBANDS"},
        description="Expose NBANDS override",
    )
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

    @model_validator(mode="before")
    @classmethod
    def sync_optional_toggles(cls, data):
        """Infer UI toggles from existing docs; clear optionals when toggles are off."""
        if not isinstance(data, dict):
            return data

        if "use_nbands" not in data:
            data["use_nbands"] = data.get("nbands") is not None
        if not data.get("use_nbands"):
            data["nbands"] = None

        return data

    @classmethod
    def json_schema(cls, recursive=True):
        schema = cleaned_json_schema(cls)
        schema["title"] = cls.__name__

        prop_schemas = schema["properties"]
        nbands_schema = prop_schemas.pop("nbands", None)
        if nbands_schema is not None and "anyOf" in nbands_schema:
            nbands_schema = {
                "type": "integer",
                "title": nbands_schema.get("title", "nbands"),
                "description": nbands_schema.get("description", "Number of bands"),
            }

        if "dependencies" not in schema:
            schema["dependencies"] = {}

        schema["dependencies"]["use_nbands"] = {
            "oneOf": [
                {
                    "properties": {
                        "use_nbands": {"const": False},
                    }
                },
                {
                    "properties": {
                        "use_nbands": {"const": True},
                        "nbands": nbands_schema,
                    }
                },
            ]
        }

        return schema

    @classmethod
    def ui_schema(cls):
        ui_schema = generate_ui_schema(cls)

        ui_schema["use_nbands"] = {
            "ui:widget": "checkbox",
            "ui:title": "Set NBANDS",
        }
        ui_schema.setdefault("nbands", {})["ui:condition"] = {"use_nbands": True}

        ui_schema["ui:order"] = [
            "encut",
            "ediff",
            "algo",
            "prec",
            "ismear",
            "sigma",
            "ispin",
            "nsw",
            "ibrion",
            "isif",
            "nelm",
            "lreal",
            "use_nbands",
            "nbands",
            "gga",
            "magmom",
            "ldau",
            "ldautype",
            "ldaul",
            "ldauu",
            "ldauj",
            "lmaxmix",
            "lwannier90",
            "lwrite_mmn_amn",
            "lwrite_unk",
            "lsorbit",
            "ncore",
            "kpar",
            "extra_incar",
        ]
        if "ui:options" not in ui_schema:
            ui_schema["ui:options"] = {}
        ui_schema["ui:options"]["ui:foldable"] = True

        return ui_schema


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
