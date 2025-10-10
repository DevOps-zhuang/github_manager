"""Entry points for transforming invitation datasets."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from invitation.normalizers.mapping import ColumnMappingConfig, MappingNormalizer
from invitation.normalizers.registry import DEFAULT_REGISTRY
from invitation.service import InvitationService

DEFAULT_ENTERPRISE_KEY = "default"


def bootstrap_default_normalizers() -> None:
    """Ensure the default normalizer is registered."""

    if DEFAULT_REGISTRY.is_registered(DEFAULT_ENTERPRISE_KEY):
        return

    DEFAULT_REGISTRY.register(
        DEFAULT_ENTERPRISE_KEY,
        lambda: MappingNormalizer(
            ColumnMappingConfig(
                mail="Mail",
                organization="Organization",
                team="Team",
            ),
            name="default",
        ),
    )


def register_enterprise_mapping(
    key: str,
    *,
    mail: str,
    organization: str,
    team: str,
) -> None:
    """Register a mapping-based normalizer for a specific enterprise."""

    if DEFAULT_REGISTRY.is_registered(key):
        raise ValueError(f"Normalizer already registered for '{key}'.")

    DEFAULT_REGISTRY.register(
        key,
        lambda: MappingNormalizer(
            ColumnMappingConfig(
                mail=mail,
                organization=organization,
                team=team,
            ),
            name=key,
        ),
    )


def load_enterprise_normalizer(enterprise_key: str):
    """Dynamically load an enterprise-specific normalizer.

    Convention:
    - Enterprise key -> directory name (capitalized first letter)
      e.g. key 'acme' => invitation/customize/Acme/normalizer.py
    - File: normalizer.py
    - Class: <CapitalizedKey>Normalizer (AcmeNormalizer)

    This function performs no special-casing for any enterprise to avoid
    leaking business identifiers into the public codebase.
    """
    if DEFAULT_REGISTRY.is_registered(enterprise_key):
        return

    dir_name = enterprise_key[:1].upper() + enterprise_key[1:]
    customize_path = Path(__file__).parent / "customize" / dir_name / "normalizer.py"

    if not customize_path.exists():
        raise ImportError(
            (
                f"Enterprise normalizer not found for '{enterprise_key}'. Expected file: {customize_path}\n"
                f"Create the file with class '{dir_name}Normalizer'. See invitation/normalizers/README.md for guidance."
            )
        )

    spec = importlib.util.spec_from_file_location(
        f"invitation.customize.{dir_name}.normalizer",
        str(customize_path),
    )
    if not spec or not spec.loader:
        raise ImportError(f"Could not load module spec from {customize_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]

    class_name = f"{dir_name}Normalizer"
    try:
        normalizer_class = getattr(module, class_name)
    except AttributeError as exc:
        raise ImportError(
            f"Expected class '{class_name}' in {customize_path} but it was not found."
        ) from exc

    DEFAULT_REGISTRY.register(enterprise_key, lambda: normalizer_class())


def transform_invitation_data(
    enterprise_key: str,
    rows: Iterable[Mapping[str, object]],
) -> Sequence[Mapping[str, str]]:
    """Normalize arbitrary enterprise data into the invitation schema."""

    bootstrap_default_normalizers()
    
    # Try to load enterprise-specific normalizer if not already registered
    if not DEFAULT_REGISTRY.is_registered(enterprise_key):
        load_enterprise_normalizer(enterprise_key)
    
    service = InvitationService()
    source_rows = list(rows)

    merged_rows: list[dict[str, str]] = []
    for original in source_rows:
        invitees = service.normalize_dataset(enterprise_key, [original])
        if not invitees:
            continue

        payload = service.build_invitation_payload(invitees)[0]
        combined = {str(key): ("" if value is None else str(value)) for key, value in original.items()}
        combined.update(payload)
        merged_rows.append(combined)

    return merged_rows


if __name__ == "__main__":  # pragma: no cover
    # Minimal self-test showcasing mapping-based registration only (no enterprise specifics)
    bootstrap_default_normalizers()
    register_enterprise_mapping(
        "acme_corp",
        mail="EmailAddress",
        organization="OrgName",
        team="TeamName",
    )
    demo_rows = [
        {"EmailAddress": "user1@example.com", "OrgName": "octo-org", "TeamName": "octo-team"},
        {"EmailAddress": "user2@example.com", "OrgName": "octo-org", "TeamName": "octo-team"},
    ]
    for row in transform_invitation_data("acme_corp", demo_rows):
        print(row)