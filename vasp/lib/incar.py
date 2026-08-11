"""Render VASP INCAR from a parameter model."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vasp.models.vasp_common import VaspIncarParams


def _bool(v: bool) -> str:
    return ".TRUE." if v else ".FALSE."


def render_incar(params: "VaspIncarParams") -> str:
    """Return INCAR text (no trailing blank requirement)."""
    lines: list[str] = [
        "INCAR written by xtalgen.vasp",
        f" ENCUT = {params.encut}",
        f" EDIFF = {params.ediff:.2e}",
        f" ALGO = {params.algo}",
        f" PREC = {params.prec}",
        f" ISMEAR = {params.ismear}",
        f" SIGMA = {params.sigma}",
        f" ISPIN = {params.ispin}",
        f" NSW = {params.nsw}",
        f" IBRION = {params.ibrion}",
        f" ISIF = {params.isif}",
        f" NELM = {params.nelm}",
        f" LREAL = {_bool(params.lreal)}",
        f" LWANNIER90 = {_bool(params.lwannier90)}",
        f" LWRITE_MMN_AMN = {_bool(params.lwrite_mmn_amn)}",
        f" LWRITE_UNK = {_bool(params.lwrite_unk)}",
        f" LSORBIT = {_bool(params.lsorbit)}",
        f" NCORE = {params.ncore}",
        f" KPAR = {params.kpar}",
    ]
    if params.use_nbands and params.nbands is not None:
        lines.append(f" NBANDS = {params.nbands}")
    if params.gga:
        lines.append(f" GGA = {params.gga}")
    if params.magmom.strip():
        lines.append(f" MAGMOM = {params.magmom.strip()}")
    if params.ldau:
        lines.append(" LDAU = .TRUE.")
        lines.append(f" LDAUTYPE = {params.ldautype}")
        if params.ldaul.strip():
            lines.append(f" LDAUL = {params.ldaul.strip()}")
        if params.ldauu.strip():
            lines.append(f" LDAUU = {params.ldauu.strip()}")
        if params.ldauj.strip():
            lines.append(f" LDAUJ = {params.ldauj.strip()}")
        lines.append(f" LMAXMIX = {params.lmaxmix}")
    if params.extra_incar.strip():
        lines.append(params.extra_incar.strip())
    return "\n".join(lines) + "\n"
