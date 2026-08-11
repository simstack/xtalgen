"""Smoke checks for TB2J CLI argument builders."""

from tbj2.models.merge_input import TB2JMergeInput, TB2JMergeType
from tbj2.models.rotate_input import TB2JRotateInput
from tbj2.models.siesta_input import SiestaInput
from tbj2.models.tb2j_common import TB2JCommonParams
from tbj2.models.wannier_input import (
    WannierCollinearInput,
    WannierGroupBy,
    WannierSpinorInput,
)


def test_wannier_collinear_cli_args():
    opts = WannierCollinearInput(
        efermi=12.6,
        common=TB2JCommonParams(
            elements="Fe",
            kmesh_x=9,
            kmesh_y=9,
            kmesh_z=9,
            rcut=15.0,
            emin=-12.0,
            nz=50,
        ),
        prefix_up="Fe_up",
        prefix_down="Fe_down",
    )
    args = opts.cli_args(posfile_name="Fe.scf.pwi")
    assert args[0] == "wann2J.py"
    assert "--spinor" not in args
    assert args[args.index("--efermi") + 1] == "12.6"
    assert args[args.index("--prefix_up") + 1] == "Fe_up"
    assert args[args.index("--prefix_down") + 1] == "Fe_down"
    assert args[args.index("--posfile") + 1] == "Fe.scf.pwi"
    k_i = args.index("--kmesh")
    assert args[k_i + 1 : k_i + 4] == ["9", "9", "9"]
    assert "--elements" in args and "Fe" in args
    assert args[args.index("--rcut") + 1] == "15.0"


def test_wannier_spinor_cli_args():
    opts = WannierSpinorInput(
        efermi=-0.87,
        common=TB2JCommonParams(
            elements="Cr",
            kmesh_x=7,
            kmesh_y=7,
            kmesh_z=1,
            nz=150,
        ),
        prefix_spinor="wannier90",
        groupby=WannierGroupBy.ORBITAL,
    )
    args = opts.cli_args()
    assert args[0] == "wann2J.py"
    assert "--spinor" in args
    assert args[args.index("--groupby") + 1] == "orbital"
    assert args[args.index("--prefix_spinor") + 1] == "wannier90"


def test_siesta_cli_args():
    opts = SiestaInput(
        common=TB2JCommonParams(
            elements="Fe",
            kmesh_x=7,
            kmesh_y=7,
            kmesh_z=7,
            nz=100,
            rcut=10.0,
        )
    )
    args = opts.cli_args(fdf_name="siesta.fdf")
    assert args[0] == "siesta2J.py"
    assert args[args.index("--fdf_fname") + 1] == "siesta.fdf"
    assert args[args.index("--rcut") + 1] == "10.0"


def test_merge_cli_args():
    opts = TB2JMergeInput(
        result_paths="x y z",
        merge_type=TB2JMergeType.STRUCTURE,
    )
    args = opts.cli_args()
    assert args[:3] == ["TB2J_merge.py", "--type", "structure"]
    assert args[3:6] == ["x", "y", "z"]
    assert args[args.index("--output_path") + 1] == "TB2J_results"


def test_rotate_cli_args():
    opts = TB2JRotateInput(ftype="vasp", noncollinear=True)
    args = opts.cli_args(structure_name="BiFeO3.vasp")
    assert args[0] == "TB2J_rotate.py"
    assert args[1] == "BiFeO3.vasp"
    assert args[args.index("--ftype") + 1] == "vasp"
    assert "--noncollinear" in args
