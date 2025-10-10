"""Base classes and contracts for invitation data normalization."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping

from invitation.constants import StandardColumns


@dataclass(frozen=True)
class NormalizedInvitee:
    """Strongly-typed representation of a normalized invitee row."""

    mail: str
    organization: str
    team: str

    def to_payload(self) -> Dict[str, str]:
        """Convert to payload expected by the invitation workflow."""

        return {
            StandardColumns.MAIL: self.mail,
            StandardColumns.ORGANIZATION: self.organization,
            StandardColumns.TEAM: self.team,
        }


class InvitationNormalizer(ABC):
    """Abstract base class for enterprise-specific data normalization."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable identifier for logging and diagnostics."""

    @abstractmethod
    def normalize_row(self, row: Mapping[str, object]) -> NormalizedInvitee:
        """Normalize a single raw data row into the standard schema."""

    def normalize(self, rows: Iterable[Mapping[str, object]]) -> List[NormalizedInvitee]:
        """Normalize a sequence of rows.

        Subclasses may override for batch optimizations, but the default
        implementation simply maps :meth:`normalize_row` across the input.
        """

        normalized: List[NormalizedInvitee] = []
        for row in rows:
            invitee = self.normalize_row(row)
            normalized.append(invitee)
        return normalized


class NormalizationError(ValueError):
    """Raised when raw data cannot be normalized into the standard schema."""

    def __init__(self, message: str, *, row: Mapping[str, object] | None = None) -> None:
        super().__init__(message)
        self.row = row
