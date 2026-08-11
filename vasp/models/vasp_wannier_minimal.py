"""Minimal Fe VASP → Wannier90 smoke input (shared workdir chain)."""

from odmantic import Model, Reference

from simstack.models import simstack_model
from vasp.models.vasp_input import VaspJobInput
from vasp.models.wannier90_input import Wannier90RunInput


@simstack_model
class VaspWannierMinimalInput(Model):
    """
    Smoke-test input: ``vasp_run`` (with ``LWANNIER90``) then ``wannier90_run``.

    Build defaults via ``vasp.testing.minimal_vasp_wannier_input``.
    """

    field_name: str = "VaspWannierMinimalInput"
    vasp: VaspJobInput = Reference()
    wannier: Wannier90RunInput = Reference()
