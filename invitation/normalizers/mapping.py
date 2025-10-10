"""Declarative normalizer based on column name mapping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from invitation.normalizers.base import InvitationNormalizer, NormalizedInvitee, NormalizationError


@dataclass
class ColumnMappingConfig:
    """Configures how raw columns map to the standard schema."""

    mail: str
    organization: str
    team: str

    def translate(self, row: Mapping[str, object]) -> NormalizedInvitee:
        try:
            mail = _value(row, self.mail)
            organization = _value(row, self.organization)
            team = _value(row, self.team)
        except KeyError as exc:
            raise NormalizationError(
                f"Required column '{exc.args[0]}' missing in raw data.", row=row
            ) from exc

        return NormalizedInvitee(
            mail=str(mail),
            organization=str(organization),
            team=str(team),
        )


class MappingNormalizer(InvitationNormalizer):
    """Normalizes rows using a configurable column name mapping."""

    def __init__(self, config: ColumnMappingConfig, *, name: str | None = None) -> None:
        self._config = config
        self._name = name or "mapping"

    @property
    def name(self) -> str:
        return self._name

    def normalize_row(self, row: Mapping[str, object]) -> NormalizedInvitee:
        return self._config.translate(row)


def _value(row: Mapping[str, object], key: str | None) -> object:
    if not key:
        raise KeyError(key)
    return row[key]
