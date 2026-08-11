"""TB2J_merge.py input model."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from odmantic import Field, Model

from simstack.models import simstack_model
from tbj2.lib.cli import split_tokens


class TB2JMergeType(str, Enum):
    STRUCTURE = "structure"
    SPIN = "spin"


@simstack_model
class TB2JMergeInput(Model):
    """
    Options for ``TB2J_merge.py``.

    ``result_paths`` is space-separated directories of prior TB2J runs; the last
    path is the unrotated / reference result (TB2J convention).
    """

    field_name: str = "TB2JMergeInput"
    result_paths: str = Field(
        ...,
        description="Space-separated TB2J result dirs (parent dirs or TB2J_results)",
    )
    merge_type: Optional[TB2JMergeType] = Field(
        None,
        description="Optional --type structure|spin (accepted by TB2J_merge CLI)",
    )
    output_path: str = Field(
        "TB2J_results",
        description="Merged output directory (--output_path)",
    )
    main_path: Optional[str] = Field(
        None,
        description="Optional --main_path reference structure directory",
    )

    def cli_args(self) -> list[str]:
        paths = split_tokens(self.result_paths)
        if len(paths) < 2:
            raise ValueError("result_paths needs at least two directories")
        args = ["TB2J_merge.py"]
        if self.merge_type is not None:
            args.extend(["--type", self.merge_type.value])
        args.extend(paths)
        args.extend(["--output_path", self.output_path])
        if self.main_path:
            args.extend(["--main_path", self.main_path])
        return args
