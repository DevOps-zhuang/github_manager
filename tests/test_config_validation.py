"""Unit tests for configuration validation module."""

from __future__ import annotations

import os
from unittest import mock

import pytest

from invitation.config_validation import (
    validate_config,
    format_validation_summary,
    _redact_secret,
)


class TestSecretRedaction:
    """Test secret redaction functionality."""

    def test_redact_short_secret(self):
        """Short secrets are not redacted."""
        assert _redact_secret("abc") == "abc"
        assert _redact_secret("12345") == "12345"

    def test_redact_long_secret(self):
        """Long secrets show first 4 and last 2 chars."""
        assert _redact_secret("sk-1234567890abcd") == "sk-1...cd"
        assert _redact_secret("github_pat_1234567890") == "gith...90"

    def test_redact_none(self):
        """None values pass through."""
        assert _redact_secret(None) is None


class TestConfigValidation:
    """Test configuration validation logic."""

    def test_openai_valid(self):
        """Valid OpenAI configuration."""
        with mock.patch.dict(os.environ, {"API_TYPE": "openai", "API_KEY": "sk-test123456"}):
            result = validate_config()
            assert result.is_valid
            assert not result.degraded_ai
            assert len(result.errors) == 0
            assert result.effective["api_type"] == "openai"
            assert result.effective["ai_enabled"]

    def test_openai_missing_key(self):
        """OpenAI without API_KEY degrades AI."""
        with mock.patch.dict(os.environ, {"API_TYPE": "openai"}, clear=True):
            result = validate_config()
            assert not result.is_valid
            assert result.degraded_ai
            assert any("API_KEY is required" in e for e in result.errors)
            assert not result.effective["ai_enabled"]

    def test_github_with_api_key(self):
        """GitHub Models with API_KEY (preferred)."""
        with mock.patch.dict(
            os.environ, {"API_TYPE": "github", "API_KEY": "ghu_test123456"}
        ):
            result = validate_config()
            assert result.is_valid
            assert not result.degraded_ai
            assert len(result.warnings) == 0

    def test_github_fallback_to_token(self):
        """GitHub Models falls back to GITHUB_TOKEN with warning."""
        with mock.patch.dict(
            os.environ,
            {"API_TYPE": "github", "GITHUB_TOKEN": "github_pat_test123456"},
            clear=True,
        ):
            result = validate_config()
            assert result.is_valid
            assert not result.degraded_ai
            assert len(result.warnings) == 1
            assert "falling back to GITHUB_TOKEN" in result.warnings[0]

    def test_github_no_credentials(self):
        """GitHub Models without any credentials degrades AI."""
        with mock.patch.dict(os.environ, {"API_TYPE": "github"}, clear=True):
            result = validate_config()
            assert not result.is_valid
            assert result.degraded_ai
            assert any("required for API_TYPE=github" in e for e in result.errors)

    def test_azure_valid(self):
        """Valid Azure OpenAI configuration."""
        with mock.patch.dict(
            os.environ,
            {
                "API_TYPE": "azure",
                "API_KEY": "azure-key-test",
                "API_BASE_URL": "https://test.openai.azure.com/openai/v1/",
            },
        ):
            result = validate_config()
            assert result.is_valid
            assert not result.degraded_ai
            assert result.effective["api_type"] == "azure"

    def test_azure_missing_base_url(self):
        """Azure without BASE_URL degrades AI."""
        with mock.patch.dict(
            os.environ, {"API_TYPE": "azure", "API_KEY": "azure-key-test"}, clear=True
        ):
            result = validate_config()
            assert not result.is_valid
            assert result.degraded_ai
            assert any("API_BASE_URL is required" in e for e in result.errors)

    def test_custom_valid(self):
        """Valid custom provider configuration."""
        with mock.patch.dict(
            os.environ,
            {
                "API_TYPE": "custom",
                "API_KEY": "custom-key",
                "API_BASE_URL": "https://my-proxy.internal/v1/",
            },
        ):
            result = validate_config()
            assert result.is_valid
            assert not result.degraded_ai

    def test_unsupported_type(self):
        """Unsupported API_TYPE."""
        with mock.patch.dict(os.environ, {"API_TYPE": "bedrock"}, clear=True):
            result = validate_config()
            assert not result.is_valid
            assert result.degraded_ai
            assert any("Unsupported API_TYPE" in e for e in result.errors)

    def test_cli_overrides_env(self):
        """CLI overrides take precedence over environment."""
        with mock.patch.dict(
            os.environ, {"API_TYPE": "openai", "API_KEY": "env-key"}, clear=True
        ):
            result = validate_config({"api_key": "cli-key"})
            assert result.is_valid
            assert "cli-..." in result.effective["api_key"]

    def test_default_model_name(self):
        """MODEL_NAME defaults to gpt-4o."""
        with mock.patch.dict(os.environ, {"API_TYPE": "openai", "API_KEY": "test"}):
            result = validate_config()
            assert result.effective["model_name"] == "gpt-4o"

    def test_default_organization(self):
        """DEFAULT_ORGANIZATION is captured."""
        with mock.patch.dict(
            os.environ,
            {"API_TYPE": "openai", "API_KEY": "test", "DEFAULT_ORGANIZATION": "TestOrg"},
        ):
            result = validate_config()
            assert result.effective["default_organization"] == "TestOrg"


class TestFormatSummary:
    """Test summary formatting."""

    def test_format_valid_config(self):
        """Format valid configuration summary."""
        with mock.patch.dict(os.environ, {"API_TYPE": "openai", "API_KEY": "sk-test"}):
            result = validate_config()
            summary = format_validation_summary(result)
            assert "[CONFIG]" in summary
            assert "api_type=openai" in summary
            assert "model=gpt-4o" in summary
            assert "ai_enabled=True" in summary
            assert "warnings=0" in summary
            assert "errors=0" in summary

    def test_format_degraded_config(self):
        """Format degraded configuration summary."""
        with mock.patch.dict(os.environ, {"API_TYPE": "openai"}, clear=True):
            result = validate_config()
            summary = format_validation_summary(result)
            assert "ai_enabled=False" in summary
            assert "errors=1" in summary
