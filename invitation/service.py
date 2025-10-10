"""Invitation orchestration built on top of the normalization layer."""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

from invitation.constants import REQUIRED_COLUMNS, StandardColumns
from invitation.normalizers.base import NormalizedInvitee
from invitation.normalizers.registry import DEFAULT_REGISTRY, NormalizerRegistry


class InvitationService:
    """Coordinates data normalization and invitation dispatching."""

    def __init__(self, *, registry: NormalizerRegistry | None = None) -> None:
        self._registry = registry or DEFAULT_REGISTRY

    def normalize_dataset(
        self, enterprise_key: str, rows: Iterable[Mapping[str, object]]
    ) -> Sequence[NormalizedInvitee]:
        """Normalize raw rows for a specific enterprise."""

        invitees = list(self._registry.normalize(enterprise_key, rows))
        if not invitees:
            return []

        _ensure_required_columns(invitees)
        return invitees

    def build_invitation_payload(
        self, invitees: Sequence[NormalizedInvitee]
    ) -> Sequence[Mapping[str, str]]:
        """Convert normalized invitees into API-ready payloads."""

        return [invitee.to_payload() for invitee in invitees]

    def invite(
        self, enterprise_key: str, rows: Iterable[Mapping[str, object]]
    ) -> Sequence[Mapping[str, str]]:
        """End-to-end normalization followed by invitation dispatch.

        The actual dispatching to GitHub is left as a future extension. For now,
        this method returns the payload that would be sent.
        """

        invitees = self.normalize_dataset(enterprise_key, rows)
        payload = self.build_invitation_payload(invitees)
        # TODO: Integrate GitHub REST API client for actual invitation dispatch.
        return payload


def _ensure_required_columns(invitees: Sequence[NormalizedInvitee]) -> None:
    for invitee in invitees:
        payload = invitee.to_payload()
        missing_keys = [column for column in REQUIRED_COLUMNS if column not in payload]
        if missing_keys:
            raise ValueError(
                "Normalized dataset missing required columns: " + ", ".join(missing_keys)
            )

        mandatory_non_empty = (StandardColumns.MAIL, StandardColumns.ORGANIZATION)
        empty_required = [column for column in mandatory_non_empty if not payload.get(column)]
        if empty_required:
            raise ValueError(
                "Normalized dataset contains empty values for required columns: "
                + ", ".join(empty_required)
            )
