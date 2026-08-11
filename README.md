# TB2J Simstack wrapper (`xtalgen` / package `tbj2`)

Simstack models and nodes for [TB2J](https://github.com/mailhexu/TB2J) —
magnetic exchange (Heisenberg J, DMI, Jani) from Wannier90 or Siesta
Hamiltonians. Upstream examples live under
[`vendor/TB2J_examples`](https://github.com/mailhexu/TB2J_examples).

DFT / Wannierization stay upstream; these nodes only run TB2J CLIs on prepared
inputs.

## Layout

```
xtalgen/              # capability root (Dockerfile, vendor, pyproject.docker)
  Dockerfile
  pyproject.docker
  vendor/
  tbj2/               # Python package (import tbj2)
    models/
    nodes/
    lib/
    testing/
    tests/
```

## Nodes

| Node | Upstream CLI | Role |
|------|--------------|------|
| `tb2j_wannier_collinear` | `wann2J.py` | Collinear up/down Wannier → J |
| `tb2j_wannier_spinor` | `wann2J.py --spinor` | NC / SOC Wannier → J, DMI, … |
| `tb2j_siesta` | `siesta2J.py` | Siesta HS / NetCDF → J |
| `tb2j_rotate` | `TB2J_rotate.py` | Rotated structures for merge workflow |
| `tb2j_merge` | `TB2J_merge.py` | Merge rotated TB2J result dirs |

Option schemas live under `tbj2/models/` and mirror TB2J CLI flags.

## Dual-use

- **Host (`simstack-model`):** not installable — no `pyproject.toml` at the capability root.
  Put `xtalgen` on `PYTHONPATH` (parent of package `tbj2`) for imports.
- **Container:** installable — Dockerfile renames `pyproject.docker` → `pyproject.toml`
  and runs `uv pip install .`. [`simstack`](https://github.com/simstack/simstack)
  (`fix-git-pull`) installs from git; TB2J installs from `vendor/TB2J`.

## Local Docker image

From the simstack-model repository root:

```bash
docker build -t xtalgen:latest -f xtalgen/Dockerfile .
```

## Register models / nodes (host)

```bash
uv run create_model_table --dir xtalgen/tbj2
uv run create_node_table --dir xtalgen/tbj2
```

## Vendor

| Path | Source |
|------|--------|
| `vendor/TB2J` | https://github.com/mailhexu/TB2J |
| `vendor/TB2J_examples` | https://github.com/mailhexu/TB2J_examples |

Docs: https://tb2j.readthedocs.io/en/latest/
