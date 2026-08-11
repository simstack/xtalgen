# Build from the simstack-model repository root:
#   docker build -t xtalgen:latest -f xtalgen/Dockerfile .
#
# Dual-use: capability tree is not installable on host (no pyproject.toml).
# In the image, pyproject.docker is renamed and the package is pip-installed;
# simstack comes from git (see pyproject.docker). TB2J is installed from vendor/.
FROM mambaorg/micromamba:latest

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN micromamba install -y -n base -c conda-forge setuptools python=3.12 \
    numpy scipy matplotlib ase netcdf4 sisl \
    && micromamba clean --all --yes

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/opt/conda/bin:/root/.local/bin:$PATH"

WORKDIR /app

ENV UV_PYTHON=/opt/conda/bin/python
ENV UV_PROJECT_ENVIRONMENT=/opt/conda
ENV PATH="/opt/conda/bin:/root/.local/bin:$PATH"

COPY xtalgen /build/xtalgen
WORKDIR /build/xtalgen

# Upstream TB2J (sisl/netcdf4 already provided by conda for Siesta path).
RUN uv pip install --system ./vendor/TB2J \
 && cp pyproject.docker pyproject.toml \
 && uv pip install --system . "setuptools>=80.9.0" \
 && python -c "import simstack, tbj2, TB2J; \
import importlib.metadata as m; \
print('simstack', simstack.__file__); \
print('tbj2', tbj2.__file__); \
print('TB2J', m.version('TB2J'))" \
 && wann2J.py --help >/dev/null \
 && siesta2J.py --help >/dev/null \
 && TB2J_merge.py --help >/dev/null \
 && TB2J_rotate.py --help >/dev/null

WORKDIR /app
ENTRYPOINT ["python", "-m", "simstack.core.run_node"]
