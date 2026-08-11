"""Collect TB2J result artifacts onto a NodeRunner."""

from __future__ import annotations

from pathlib import Path

from simstack.models.files import FileStack

# Primary text/XML outputs written under --output_path (default TB2J_results).
PRIMARY_OUTPUTS = (
    "exchange.out",
    "exchange.txt",
    "exchange.xml",
    "TB2J.pickle",
)

# Downstream spin-dynamics templates (any present files).
DOWNSTREAM_GLOBS = (
    "Multibinit/**/*",
    "Vampire/**/*",
    "TomASD/**/*",
)


def collect_tb2j_results(
    node_runner,
    output_path: str = "TB2J_results",
    *,
    required_any: bool = True,
) -> list[FileStack]:
    """
    Attach files under ``output_path`` to ``node_runner.info_files`` / return list.

    Raises ``FileNotFoundError`` when ``required_any`` and the directory is missing
    or contains no recognized primary outputs.
    """
    root = Path(output_path)
    if not root.is_dir():
        if required_any:
            raise FileNotFoundError(f"TB2J output directory not found: {output_path}")
        return []

    collected: list[FileStack] = []
    found_primary = False

    for name in PRIMARY_OUTPUTS:
        path = root / name
        if path.is_file():
            found_primary = True
            stack = FileStack.from_local_file(
                str(path), in_memory=True, is_hashable=True, secure_source=True
            )
            node_runner.info_files.append(stack)
            collected.append(stack)

    for pattern in DOWNSTREAM_GLOBS:
        for path in root.glob(pattern):
            if path.is_file():
                stack = FileStack.from_local_file(
                    str(path), in_memory=True, is_hashable=True, secure_source=True
                )
                node_runner.info_files.append(stack)
                collected.append(stack)

    if required_any and not found_primary:
        raise FileNotFoundError(
            f"No TB2J primary outputs (exchange.*) under {output_path}"
        )

    return collected
