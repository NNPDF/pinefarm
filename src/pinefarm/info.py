"""Provide inspection tools."""

import dataclasses
import typing

from .external import decide_external_tool
from .external.interface import External


@dataclasses.dataclass
class Info:
    """Info type."""

    color: str
    external: typing.Type[External]

    @property
    def kind(self):
        """Type of process as defined by the external interface."""
        return self.external.kind


def label(dataset: str) -> Info:
    """Generate associated Info type."""
    ext_tool, color = decide_external_tool(dataset)
    return Info(color=color, external=ext_tool)
