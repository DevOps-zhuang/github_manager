"""Registry for invitation normalizers."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Mapping

from invitation.constants import REQUIRED_COLUMNS, StandardColumns
from invitation.normalizers.base import InvitationNormalizer, NormalizedInvitee, NormalizationError


class NormalizerRegistry:
    """Keeps a mapping between enterprise codes and normalizer classes."""

    def __init__(self) -> None:
        self._registry: Dict[str, Callable[[], InvitationNormalizer]] = {}

    def register(self, key: str, factory: Callable[[], InvitationNormalizer]) -> None:
        if key in self._registry:
            raise ValueError(f"Normalizer already registered for '{key}'.")
        self._registry[key] = factory

    def get(self, key: str) -> InvitationNormalizer:
        try:
            factory = self._registry[key]
        except KeyError as exc:
            raise KeyError(f"No normalizer registered for '{key}'.") from exc
        return factory()

    def normalize(
        self, key: str, rows: Iterable[Mapping[str, object]]
    ) -> Iterable[NormalizedInvitee]:
        normalizer = self.get(key)
        normalized = normalizer.normalize(rows)
        for invitee in normalized:
            _validate_standard_columns(invitee)
        return normalized

    def is_registered(self, key: str) -> bool:
        return key in self._registry


DEFAULT_REGISTRY = NormalizerRegistry()


def _validate_standard_columns(invitee: NormalizedInvitee) -> None:
    payload = invitee.to_payload()
    missing_keys = [column for column in REQUIRED_COLUMNS if column not in payload]
    if missing_keys:
        raise NormalizationError(
            "Normalized row is missing required columns: " + ", ".join(missing_keys)
        )
    if not payload.get(StandardColumns.MAIL) or not payload.get(StandardColumns.ORGANIZATION):
        raise NormalizationError(
            "Normalized row is missing values for required columns: "
            f"{StandardColumns.MAIL}, {StandardColumns.ORGANIZATION}"
        )
