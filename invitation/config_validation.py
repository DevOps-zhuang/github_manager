"""Configuration validation module for AI and invitation workflows.

Validates environment variables and CLI overrides according to API_TYPE matrix.
Supports degraded mode where AI features are disabled but invitation flows continue.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

# Supported API provider types
SUPPORTED_API_TYPES = {"openai", "github", "azure", "custom"}
DEFAULT_MODEL = "gpt-4o"


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    is_valid: bool
    """True if all required fields are present and valid."""

    degraded_ai: bool
    """True if AI features should be disabled due to config issues."""

    errors: list[str] = field(default_factory=list)
    """Critical errors that prevent operation."""

    warnings: list[str] = field(default_factory=list)
    """Non-critical issues that should be noted."""

    effective: dict[str, Any] = field(default_factory=dict)
    """Effective configuration with resolved values (secrets redacted)."""


def _redact_secret(value: str | None) -> str | None:
    """Redact secrets to show only first 4 and last 2 characters."""
    if not value or len(value) < 6:
        return value
    return f"{value[:4]}...{value[-2:]}"


def validate_config(cli_overrides: dict[str, Any] | None = None) -> ValidationResult:
    """Validate configuration from environment and CLI overrides.

    Args:
        cli_overrides: Optional dictionary of CLI-provided values that override env vars.
                      Keys: api_type, api_key, model_name, api_base_url, api_version,
                            default_organization, default_team_prefix

    Returns:
        ValidationResult with validation status and effective configuration.
    """
    cli_overrides = cli_overrides or {}
    errors: list[str] = []
    warnings: list[str] = []
    degraded_ai = False

    # Merge CLI overrides with environment (CLI takes precedence)
    env = os.environ
    api_type = (cli_overrides.get("api_type") or env.get("API_TYPE", "openai")).lower().strip()
    api_key = (cli_overrides.get("api_key") or env.get("API_KEY") or "").strip() or None
    model_name = (cli_overrides.get("model_name") or env.get("MODEL_NAME", DEFAULT_MODEL)).strip()
    api_base_url = (cli_overrides.get("api_base_url") or env.get("API_BASE_URL") or "").strip() or None
    api_version = (cli_overrides.get("api_version") or env.get("API_VERSION") or "").strip() or None
    github_token = (env.get("GITHUB_TOKEN") or "").strip() or None
    default_org = (cli_overrides.get("default_organization") or env.get("DEFAULT_ORGANIZATION") or "").strip() or None
    default_team_prefix = (cli_overrides.get("default_team_prefix") or env.get("DEFAULT_TEAM_PREFIX") or "").strip() or None

    # Validate API_TYPE
    if api_type not in SUPPORTED_API_TYPES:
        errors.append(
            f"Unsupported API_TYPE '{api_type}'. Must be one of: {', '.join(SUPPORTED_API_TYPES)}"
        )
        degraded_ai = True

    # Matrix validation based on API_TYPE
    if api_type == "openai":
        if not api_key:
            errors.append("API_KEY is required for API_TYPE=openai")
            degraded_ai = True

    elif api_type == "github":
        if not api_key:
            if github_token:
                warnings.append(
                    "API_KEY missing for API_TYPE=github; falling back to GITHUB_TOKEN. "
                    "Note: GITHUB_TOKEN may lack model access permissions. "
                    "Consider setting a dedicated API_KEY."
                )
                api_key = github_token
            else:
                errors.append(
                    "API_KEY or GITHUB_TOKEN required for API_TYPE=github. "
                    "Neither was found in configuration."
                )
                degraded_ai = True

    elif api_type == "azure":
        if not api_key:
            errors.append("API_KEY is required for API_TYPE=azure")
            degraded_ai = True
        if not api_base_url:
            errors.append(
                "API_BASE_URL is required for API_TYPE=azure. "
                "Example: https://your-resource.openai.azure.com/openai/v1/"
            )
            degraded_ai = True

    elif api_type == "custom":
        if not api_key:
            errors.append("API_KEY is required for API_TYPE=custom")
            degraded_ai = True
        if not api_base_url:
            errors.append(
                "API_BASE_URL is required for API_TYPE=custom. "
                "Provide the full endpoint URL for your custom provider."
            )
            degraded_ai = True

    # Build effective config
    effective = {
        "api_type": api_type,
        "api_key": _redact_secret(api_key),
        "model_name": model_name,
        "api_base_url": api_base_url,
        "api_version": api_version,
        "default_organization": default_org,
        "default_team_prefix": default_team_prefix,
        "github_token_present": bool(github_token),
        "ai_enabled": not degraded_ai,
    }

    return ValidationResult(
        is_valid=len(errors) == 0,
        degraded_ai=degraded_ai,
        errors=errors,
        warnings=warnings,
        effective=effective,
    )


def format_validation_summary(result: ValidationResult) -> str:
    """Format validation result as a human-readable summary line.

    Args:
        result: ValidationResult to format

    Returns:
        Single-line summary string
    """
    eff = result.effective
    return (
        f"[CONFIG] api_type={eff['api_type']} "
        f"model={eff['model_name']} "
        f"ai_enabled={eff['ai_enabled']} "
        f"warnings={len(result.warnings)} "
        f"errors={len(result.errors)}"
    )
