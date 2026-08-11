# xtalgen — VASP / Wannier90 / TB2J for Simstack

Capability package for crystal magnetism workflows:

- [`vasp`](vasp/) — VASP run + Wannier90 (write helpers inside run nodes)
- [`tbj2`](tbj2/) — [TB2J](https://github.com/mailhexu/TB2J) exchange parameters

Upstream examples (not vendored): [TB2J_examples](https://github.com/mailhexu/TB2J_examples).

## Layout

```
xtalgen/
  pyproject.toml
  vasp/                 # import vasp
  tbj2/                 # import tbj2
```

## Install

```bash
uv sync                 # from this directory
# or: uv pip install -e ".[dev]"
```

Pulls editable `simstack` from `../simstack` and [TB2J](https://github.com/mailhexu/TB2J)
from GitHub. Upstream hard-deps `sisl` / `pypao` are excluded for the Wannier path
(`tool.uv.exclude-dependencies`); add `--extra siesta` when you need Siesta.

VASP and `wannier90.x` are external binaries — put them on `PATH` / configure
`[*.program.vasp]` in `config.toml`.

Examples live upstream (not vendored): https://github.com/mailhexu/TB2J_examples

Inside the `simstack-model` monorepo:

```bash
uv pip install -e "./xtalgen[dev]"
```

If resolver hits `pypao`/`sisl` (those settings apply to `uv sync`, not always to
`uv pip`), install TB2J separately:

```bash
uv pip install -e "./xtalgen[dev]" --no-deps
uv pip install "TB2J @ git+https://github.com/mailhexu/TB2J.git" --no-deps
```

## VASP + Wannier90 nodes

Only **run** callables are `@node`s. Input writing lives in `vasp.lib` and is
invoked inside the run nodes.

| Node | Role |
|------|------|
| `vasp_run` | Write INCAR/KPOINTS + stage POSCAR/POTCAR, then `context.resource_config.run("vasp")` |
| `wannier90_run` | Write `{seed}.win` (optional), then run `wannier90.x` → `*_hr.dat`, `*_centres.xyz` |
| `vasp_stage_wannier_for_tb2j` | Verify TB2J inputs; parse `E-fermi` from `OUTCAR` |

Helpers (not nodes): `vasp.lib.write_vasp_inputs`, `vasp.lib.write_wannier90_wins`.

Binary / launcher: `[<resource>.program.vasp] run_command` in `config.toml`
(e.g. `vasp_std`, `srun vasp_ncl`). MPI ranks come from
`parent_parameters.slurm_parameters` on the job allocation — not from the input model.
Workdir is always cwd.

Typical collinear flow (SrMnO3-style):

1. `vasp_run` (`VaspJobInput` with `LWANNIER90`; stage `.win` via `extra_files` or write later)
2. `wannier90_run` (`channels="wannier90.up wannier90.dn"`, `write_win=True`)
3. `vasp_stage_wannier_for_tb2j`
4. `tbj2_wannier_collinear` (from `tbj2`)

SOC / spinor: set `LSORBIT`, point `run_command` at `vasp_ncl`, run seed `wannier90`, then `tbj2_wannier_spinor`.

**License note:** VASP and PAW `POTCAR` files are proprietary and are **not** shipped.

## TB2J nodes

| Node | CLI |
|------|-----|
| `tb2j_wannier_collinear` | `wann2J.py` |
| `tb2j_wannier_spinor` | `wann2J.py --spinor` |
| `tb2j_siesta` | `siesta2J.py` |
| `tb2j_rotate` | `TB2J_rotate.py` |
| `tb2j_merge` | `TB2J_merge.py` |

## Register

```bash
uv run create_model_table --dir xtalgen/vasp
uv run create_node_table --dir xtalgen/vasp
uv run create_model_table --dir xtalgen/tbj2
uv run create_node_table --dir xtalgen/tbj2
```

Docs: https://tb2j.readthedocs.io/en/latest/ · https://www.vasp.at/
