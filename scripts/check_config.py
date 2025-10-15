"""Standalone configuration check utility.

当前脚本用于在实现正式校验逻辑前，给出一个占位/骨架。
后续 Task 6 完成后，会调用 invitation.config_validation.validate_config。
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Any


EXPECTED_TYPES = {"openai", "github", "azure", "custom"}
DEFAULT_MODEL = "gpt-4o"


@dataclass
class ValidationResult:
    is_valid: bool
    degraded_ai: bool
    errors: list[str]
    warnings: list[str]
    effective: dict[str, Any]


def _redact(value: str | None) -> str | None:
    if not value or len(value) < 6:
        return value
    return value[:4] + "..." + value[-2:]


def basic_validate() -> ValidationResult:
    env = os.environ
    errors: list[str] = []
    warnings: list[str] = []
    degraded = False

    api_type = env.get("API_TYPE", "openai").lower()
    if api_type not in EXPECTED_TYPES:
        errors.append(f"Unsupported API_TYPE '{api_type}'")
        degraded = True

    api_key = env.get("API_KEY")
    model_name = env.get("MODEL_NAME", DEFAULT_MODEL)
    base_url = env.get("API_BASE_URL")
    api_version = env.get("API_VERSION")
    gh_token = env.get("GITHUB_TOKEN")

    # Matrix checks
    if api_type == "openai":
        if not api_key:
            errors.append("API_KEY required for API_TYPE=openai")
            degraded = True
    elif api_type == "github":
        if not api_key:
            if gh_token:
                warnings.append("API_KEY missing; falling back to GITHUB_TOKEN (not recommended)")
                api_key = gh_token
            else:
                errors.append("API_KEY or GITHUB_TOKEN required for API_TYPE=github")
                degraded = True
    elif api_type in {"azure", "custom"}:
        if not api_key:
            errors.append(f"API_KEY required for API_TYPE={api_type}")
            degraded = True
        if not base_url:
            errors.append(f"API_BASE_URL required for API_TYPE={api_type}")
            degraded = True

    effective = {
        "api_type": api_type,
        "model_name": model_name,
        "api_key": _redact(api_key),
        "api_base_url": base_url,
        "api_version": api_version,
        "default_org": env.get("DEFAULT_ORGANIZATION"),
        "default_team_prefix": env.get("DEFAULT_TEAM_PREFIX"),
        "github_token_present": bool(gh_token),
    }

    return ValidationResult(
        is_valid=not errors,
        degraded_ai=degraded,
        errors=errors,
        warnings=warnings,
        effective=effective,
    )


def main() -> int:
    result = basic_validate()
    summary = {
        "is_valid": result.is_valid,
        "degraded_ai": result.degraded_ai,
        "errors": result.errors,
        "warnings": result.warnings,
        "effective": result.effective,
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # 退出规则：
    #  - 结构性错误（unsupported api_type 等） → 退出码 2
    #  - AI 配置失效但仍可运行其它功能 → 退出码 0（由上层决定是否继续）
    if any(e.startswith("Unsupported API_TYPE") for e in result.errors):
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
