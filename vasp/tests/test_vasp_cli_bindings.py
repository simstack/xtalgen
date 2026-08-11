"""Smoke checks for VASP / Wannier90 input renderers and write helpers."""

from pathlib import Path

from vasp.lib.incar import render_incar
from vasp.lib.kpoints import render_kpoints
from vasp.lib.outcar import parse_efermi
from vasp.lib.win import render_wannier90_win
from vasp.lib.write_inputs import write_vasp_inputs
from vasp.lib.write_win import write_wannier90_wins
from vasp.models.vasp_common import KpointsStyle, VaspIncarParams, VaspKpointsParams
from vasp.models.vasp_input import VaspJobInput
from vasp.models.wannier90_input import (
    Wannier90Channel,
    Wannier90RunInput,
    Wannier90WinInput,
    Wannier90WinParams,
)


def test_render_incar_wannier_flags():
    text = render_incar(
        VaspIncarParams(lwannier90=True, lwrite_mmn_amn=True, lsorbit=False, encut=400)
    )
    assert "LWANNIER90 = .TRUE." in text
    assert "LWRITE_MMN_AMN = .TRUE." in text
    assert "LSORBIT = .FALSE." in text
    assert "ENCUT = 400" in text


def test_render_kpoints_gamma():
    text = render_kpoints(
        VaspKpointsParams(style=KpointsStyle.GAMMA, nx=8, ny=8, nz=8)
    )
    assert "Gamma" in text
    assert "8 8 8" in text


def test_vasp_job_input_texts():
    job = VaspJobInput(
        incar=VaspIncarParams(ispin=2, lwannier90=True),
        kpoints=VaspKpointsParams(nx=4, ny=4, nz=4),
    )
    assert "ISPIN = 2" in job.incar_text()
    assert "4 4 4" in job.kpoints_text()


def test_vasp_job_input_is_top_level_model():
    opts = VaspJobInput(incar=VaspIncarParams(encut=400, lsorbit=True))
    assert opts.incar.encut == 400
    assert opts.incar.lsorbit is True
    assert opts.field_name == "VaspJobInput"


def test_wannier90_win_render():
    params = Wannier90WinParams(
        num_wann=28,
        num_bands=48,
        write_hr=True,
        projections="Mn: d\nO: p",
        dis_win_min=-10.0,
        dis_win_max=10.0,
    )
    text = render_wannier90_win(params)
    assert "num_wann = 28" in text
    assert "write_hr = true" in text
    assert "begin projections" in text
    assert "Mn: d" in text
    assert "dis_win_min = -10.0" in text


def test_wannier90_win_input_filename():
    opts = Wannier90WinInput(channel=Wannier90Channel.DOWN)
    assert opts.filename() == "wannier90.dn.win"


def test_wannier90_run_seednames_and_win():
    opts = Wannier90RunInput(
        channels="wannier90.up wannier90.dn",
        win=Wannier90WinParams(num_wann=10),
        write_win=True,
    )
    assert opts.seednames() == ["wannier90.up", "wannier90.dn"]
    assert opts.win.num_wann == 10
    assert opts.cli_args_for("wannier90.up") == ["wannier90.x", "wannier90.up"]


def test_parse_efermi(tmp_path):
    outcar = tmp_path / "OUTCAR"
    outcar.write_text(
        " junk\n E-fermi :  1.234  XYZ\n more\n E-fermi :  4.327  ABC\n",
        encoding="utf-8",
    )
    assert parse_efermi(outcar) == 4.327


def test_write_vasp_inputs_helper(tmp_path):
    job = VaspJobInput(
        incar=VaspIncarParams(encut=300),
        kpoints=VaspKpointsParams(nx=2, ny=2, nz=2),
    )
    try:
        write_vasp_inputs(job, work_dir=tmp_path)
        assert False, "expected ValueError for missing poscar"
    except ValueError as exc:
        assert "poscar" in str(exc).lower()

    # INCAR/KPOINTS generation path (before poscar check writes them first —
    # verify render via job helpers instead)
    assert "ENCUT = 300" in job.incar_text()
    assert "2 2 2" in job.kpoints_text()


def test_write_wannier90_wins_helper(tmp_path):
    write_wannier90_wins(
        ["wannier90.up", "wannier90"],
        Wannier90WinParams(num_wann=4, projections="Fe: d"),
        work_dir=tmp_path,
    )
    up = (tmp_path / "wannier90.up.win").read_text(encoding="utf-8")
    spinor = (tmp_path / "wannier90.win").read_text(encoding="utf-8")
    assert "num_wann = 4" in up
    assert "spinors = false" in up
    assert "spinors = true" in spinor
