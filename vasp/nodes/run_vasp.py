"""Node: write VASP inputs then run via config.toml ``program.vasp``."""

from pathlib import Path

from simstack.core.context import context
from simstack.core.node import node
from simstack.core.simstack_result import SimstackResult
from simstack.models import FloatData
from vasp.lib.cli import attach_file
from vasp.lib.outcar import parse_efermi
from vasp.lib.write_inputs import write_vasp_inputs
from vasp.models.vasp_input import VaspJobInput

VASP_INPUT_FILES = ("INCAR", "KPOINTS", "POSCAR", "POTCAR")
# Diagnostic / log outputs — go to info_files only.
VASP_INFO_FILES = (
    "OUTCAR",
    "OSZICAR",
    "EIGENVAL",
    "CHGCAR",
    "WAVECAR",
    "vasprun.xml",
    "CONTCAR",
)
# Passed to resource_config.run as expected products (union of info + pipeline globs).
VASP_RESULT_FILES = VASP_INFO_FILES


@node
async def vasp_run(opts: VaspJobInput, **kwargs) -> SimstackResult:
    """
    Write INCAR/KPOINTS/POSCAR/POTCAR in cwd, then run ``program.vasp``.

    Binary and launcher come from ``config.toml``
    (``[<resource>.program.vasp] run_command``). MPI size is taken from the
    Slurm allocation on ``kwargs["parent_parameters"]`` (do not pass a local
    ``mpi_prefix``). Parses ``E-fermi`` from OUTCAR onto ``node_runner.efermi``.

    Pipeline outputs (Wannier90 interface files) go to ``files`` with
    ``in_memory=False`` and ``secure_source=True``. Inputs and diagnostic
    VASP outputs go to ``info_files`` only.

    SimstackResult:
        files (List[FileStack]): Wannier90 interface files for downstream nodes
        info_files (List[FileStack]): Inputs and diagnostic VASP outputs
        efermi (FloatData): Fermi energy from OUTCAR (eV), when parseable
    """
    node_runner = kwargs["node_runner"]
    try:
        parent_parameters = kwargs.get("parent_parameters")
        if parent_parameters is not None:
            node_runner.info(f"parent_parameters: {parent_parameters}")
            slurm = getattr(parent_parameters, "slurm_parameters", None)
            if slurm is not None:
                node_runner.info(
                    "slurm_parameters: "
                    f"nodes={slurm.nodes}, tasks={slurm.tasks}, "
                    f"tasks_per_node={slurm.tasks_per_node}, "
                    f"cpus_per_task={slurm.cpus_per_task}"
                )

        program = context.resource_config.get_program("vasp")
        if not program.get("run_command"):
            return node_runner.fail(
                "Missing run_command for [*.program.vasp] in config.toml "
                f"(resource={getattr(context.resource_config, '_resource', '?')})"
            )

        try:
            # Attaches staged inputs to info_files only.
            write_vasp_inputs(opts, node_runner=node_runner)
        except ValueError as exc:
            return node_runner.fail(str(exc))

        context.resource_config.run(
            "vasp",
            list(VASP_INPUT_FILES),
            list(VASP_RESULT_FILES),
            node_runner=node_runner,
        )

        outcar_path = Path("OUTCAR")
        if not outcar_path.is_file():
            return node_runner.fail(
                "OUTCAR not found after VASP run "
                f"(run_command={program.get('run_command')!r})"
            )

        for name in VASP_INFO_FILES:
            attach_file(node_runner, name, dest="info_files")

        # Downstream Wannier90 needs .mmn / .amn / .eig (and related) on disk.
        for path in Path(".").glob("wannier90*"):
            if path.is_file():
                attach_file(
                    node_runner,
                    path,
                    dest="files",
                    in_memory=False,
                    secure_source=True,
                )

        efermi = parse_efermi(outcar_path)
        if efermi is not None:
            node_runner.efermi = FloatData(field_name="efermi", value=efermi)
            node_runner.info(f"E-fermi = {efermi} eV")

        return node_runner.succeed()
    except Exception as exc:
        node_runner.error(f"vasp_run: {exc}")
        return node_runner.fail(error_message=str(exc))
