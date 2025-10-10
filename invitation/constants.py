"""Shared constants for invitation data normalization."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class StandardColumns:
    """Column names required by the downstream invitation workflow."""

    MAIL: ClassVar[str] = "Mail"
    ORGANIZATION: ClassVar[str] = "Organization"
    TEAM: ClassVar[str] = "Team"
    PARENT_TEAM: ClassVar[str] = "ParentTeam"


REQUIRED_COLUMNS = (
    StandardColumns.MAIL,
    StandardColumns.ORGANIZATION,
    StandardColumns.TEAM,
)