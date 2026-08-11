"""Smoke checks for VASP / Wannier90 input renderers and write helpers."""

from pathlib import Path

from simstack.models import FileStack
from vasp.lib.incar import render_incar
from vasp.lib.kpoints import render_kpoints
from vasp.lib.outcar import parse_efermi
from vasp.lib.win import render_wannier90_win
from vasp.lib.write_win import write_wannier90_wins
from vasp.models.vasp_common import KpointsStyle, VaspIncarParams, VaspKpointsParams
from vasp.models.vasp_input import VaspJobInput
from vasp.models.wannier90_input import (
    Wannier90Channel,
    Wannier90RunInput,
    Wannier90WinInput,
    Wannier90WinParams,
)


def _dummy_poscar_potcar(tmp_path: Path) -> tuple[FileStack, FileStack]:
    pos = tmp_path / "POSCAR"
    pot = tmp_path / "POTCAR"
    pos.write_text("dummy POSCAR\n", encoding="utf-8")
    pot.write_text("dummy POTCAR\n", encoding="utf-8")
    return (
        FileStack.from_local_file(str(pos), in_memory=True, is_hashable=True),
        FileStack.from_local_file(str(pot), in_memory=True, is_hashable=True),
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


def test_vasp_job_input_texts(tmp_path):
    poscar, potcar = _dummy_poscar_potcar(tmp_path)
    job = VaspJobInput(
        incar=VaspIncarParams(ispin=2, lwannier90=True),
        kpoints=VaspKpointsParams(nx=4, ny=4, nz=4),
        poscar=poscar,
        potcar=potcar,
    )
    assert "ISPIN = 2" in job.incar_text()
    assert "4 4 4" in job.kpoints_text()


def test_vasp_job_input_is_top_level_model(tmp_path):
    poscar, potcar = _dummy_poscar_potcar(tmp_path)
    opts = VaspJobInput(
        incar=VaspIncarParams(encut=400, lsorbit=True),
        poscar=poscar,
        potcar=potcar,
    )
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
    assert params.use_dis_params is True
    text = render_wannier90_win(params)
    assert "num_wann = 28" in text
    assert "write_hr = true" in text
    assert "begin projections" in text
    assert "Mn: d" in text
    assert "dis_win_min = -10.0" in text

    cleared = Wannier90WinParams(
        use_dis_params=False,
        dis_win_min=-10.0,
        dis_win_max=10.0,
    )
    assert cleared.dis_win_min is None
    assert "dis_win_min" not in render_wannier90_win(cleared)


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
    assert opts.write_win is True
    assert opts.use_win_files is False
    assert opts.win_files is None


def test_parse_efermi(tmp_path):
    outcar = tmp_path / "OUTCAR"
    outcar.write_text(
        " junk\n E-fermi :  1.234  XYZ\n more\n E-fermi :  4.327  ABC\n",
        encoding="utf-8",
    )
    assert parse_efermi(outcar) == 4.327


def test_vasp_job_input_requires_poscar_potcar():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        VaspJobInput(
            incar=VaspIncarParams(encut=300),
            kpoints=VaspKpointsParams(nx=2, ny=2, nz=2),
        )


def test_vasp_job_input_potcar_autobuild(tmp_path):
    poscar, _potcar = _dummy_poscar_potcar(tmp_path)
    job = VaspJobInput(
        poscar=poscar,
        potcar_autobuild=True,
        incar=VaspIncarParams(encut=300),
        kpoints=VaspKpointsParams(nx=2, ny=2, nz=2),
    )
    assert job.potcar is None
    assert job.potcar_autobuild is True


def test_vasp_job_input_requires_potcar_without_autobuild(tmp_path):
    import pytest
    from pydantic import ValidationError

    poscar, _ = _dummy_poscar_potcar(tmp_path)
    with pytest.raises(ValidationError):
        VaspJobInput(
            poscar=poscar,
            potcar_autobuild=False,
            potcar=None,
            incar=VaspIncarParams(encut=300),
            kpoints=VaspKpointsParams(nx=2, ny=2, nz=2),
        )


def test_parse_poscar_elements_and_build_potcar(tmp_path):
    from vasp.lib.potcar import build_potcar_from_poscar, parse_poscar_elements
    from vasp.testing.minimal_vasp_run import POSCAR_PATH

    assert parse_poscar_elements(POSCAR_PATH) == ["Fe"]

    lib = tmp_path / "potpaw"
    fe_dir = lib / "Fe"
    fe_dir.mkdir(parents=True)
    (fe_dir / "POTCAR").write_text("FAKE_FE_POTCAR\n", encoding="utf-8")
    o_dir = lib / "O"
    o_dir.mkdir()
    (o_dir / "POTCAR").write_text("FAKE_O_POTCAR\n", encoding="utf-8")

    pos = tmp_path / "POSCAR"
    pos.write_text(
        "test\n1.0\n1 0 0\n0 1 0\n0 0 1\nFe O\n1 1\nDirect\n0 0 0\n0.5 0.5 0.5\n",
        encoding="utf-8",
    )
    out, elements = build_potcar_from_poscar(pos, lib, tmp_path / "POTCAR")
    assert elements == ["Fe", "O"]
    text = out.read_text(encoding="utf-8")
    assert text.startswith("FAKE_FE_POTCAR")
    assert "FAKE_O_POTCAR" in text


def test_write_vasp_inputs_helper(tmp_path):
    poscar, potcar = _dummy_poscar_potcar(tmp_path)
    job = VaspJobInput(
        incar=VaspIncarParams(encut=300),
        kpoints=VaspKpointsParams(nx=2, ny=2, nz=2),
        poscar=poscar,
        potcar=potcar,
        potcar_autobuild=False,
    )
    assert job.poscar is poscar
    assert job.potcar is potcar
    assert "ENCUT = 300" in job.incar_text()
    assert "2 2 2" in job.kpoints_text()
    # Full materialize path needs context.initialize(); covered in with_config tests.


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


def test_minimal_vasp_wannier_job_input(tmp_path):
    """Builder stages Fe .win into VASP extras; Wannier reuses VASP outputs."""
    from vasp.testing.minimal_vasp_wannier_run import minimal_vasp_wannier_job_input

    poscar, potcar = _dummy_poscar_potcar(tmp_path)
    opts = minimal_vasp_wannier_job_input(
        poscar=poscar, potcar=potcar, potcar_autobuild=False
    )

    assert opts.vasp.incar.lwannier90 is True
    assert opts.vasp.incar.lwrite_mmn_amn is True
    assert opts.vasp.incar.ispin == 1
    assert opts.vasp.incar.nbands == 16
    assert opts.vasp.use_extra_files is True
    extras = list(opts.vasp.extra_files)
    assert len(extras) == 1
    assert extras[0].name == "wannier90.win"

    assert opts.wannier.channels == "wannier90"
    assert opts.wannier.write_win is False
    assert opts.wannier.win.num_wann == 5
    assert "Fe:d" in opts.wannier.win.projections
    assert "LWANNIER90 = .TRUE." in opts.vasp.incar_text()


def test_minimal_vasp_wannier_job_input_autobuild(tmp_path):
    from vasp.testing.minimal_vasp_wannier_run import minimal_vasp_wannier_job_input

    poscar, _ = _dummy_poscar_potcar(tmp_path)
    opts = minimal_vasp_wannier_job_input(poscar=poscar, potcar_autobuild=True)
    assert opts.vasp.potcar_autobuild is True
    assert opts.vasp.potcar is None
