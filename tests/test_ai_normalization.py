"""Unit tests for AI normalization service (without requiring API keys)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from invitation.ai_normalization_service import (
    AINormalizationService,
    LLMService,
    TransformationRule,
)


def test_transformation_rule_creation():
    """Test TransformationRule dataclass."""
    rule = TransformationRule(
        description="Rename column",
        rule_type="mapping",
        parameters={"source_column": "OldName", "target_column": "NewName"},
    )
    assert rule.description == "Rename column"
    assert rule.rule_type == "mapping"
    assert rule.parameters["source_column"] == "OldName"


def test_analyze_csv(tmp_path):
    """Test CSV analysis functionality."""
    # Create test CSV
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame(
        {
            "Name": ["Alice", "Bob", None],
            "Email": ["alice@example.com", "bob@example.com", "charlie@example.com"],
            "Age": [25, 30, 35],
        }
    )
    df.to_csv(csv_path, index=False)

    # Analyze
    service = AINormalizationService(llm_service=Mock())
    analysis = service.analyze_csv(csv_path)

    assert analysis["row_count"] == 3
    assert analysis["column_count"] == 3
    assert "Name" in analysis["columns"]
    assert "Email" in analysis["columns"]
    assert analysis["null_counts"]["Name"] == 1


def test_validate_transformation_code_safe():
    """Test code validation accepts safe code."""
    service = AINormalizationService(llm_service=Mock())

    safe_code = """
def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result = result.rename(columns={'OldName': 'NewName'})
    return result
"""

    is_valid, errors = service.validate_transformation_code(safe_code)
    assert is_valid
    assert len(errors) == 0


def test_validate_transformation_code_dangerous():
    """Test code validation rejects dangerous code."""
    service = AINormalizationService(llm_service=Mock())

    dangerous_code = """
def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    eval("print('danger')")
    return df
"""

    is_valid, errors = service.validate_transformation_code(dangerous_code)
    assert not is_valid
    assert len(errors) > 0
    assert any("eval" in error for error in errors)


def test_validate_transformation_code_missing_function():
    """Test code validation rejects code without proper function."""
    service = AINormalizationService(llm_service=Mock())

    bad_code = """
result = df.copy()
result = result.rename(columns={'OldName': 'NewName'})
"""

    is_valid, errors = service.validate_transformation_code(bad_code)
    assert not is_valid
    assert any("transform_data" in error for error in errors)


def test_execute_transformation_simple(tmp_path):
    """Test simple transformation execution."""
    # Create test CSV
    csv_path = tmp_path / "input.csv"
    df = pd.DataFrame(
        {
            "OldName": ["Alice", "Bob"],
            "Email": ["alice@example.com", "bob@example.com"],
        }
    )
    df.to_csv(csv_path, index=False)

    # Mock LLM service
    mock_llm = Mock(spec=LLMService)
    mock_llm.generate_transformation_code.return_value = """
def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result = result.rename(columns={'OldName': 'NewName'})
    return result
"""

    # Execute transformation
    service = AINormalizationService(llm_service=mock_llm)
    rules = [
        TransformationRule(
            description="Rename OldName to NewName",
            rule_type="mapping",
            parameters={"source_column": "OldName", "target_column": "NewName"},
        )
    ]

    clean_path = tmp_path / "output_clean.csv"
    report_path = tmp_path / "output_report.csv"

    result = service.execute_transformation(
        csv_path, rules, output_clean_path=clean_path, output_report_path=report_path
    )

    assert result.success
    assert result.clean_data is not None
    assert "NewName" in result.clean_data.columns
    assert "OldName" not in result.clean_data.columns
    assert clean_path.exists()
    assert report_path.exists()


def test_llm_service_parse_json_response():
    """Test parsing LLM JSON response."""
    service = LLMService(api_key="test-key")

    json_response = """
{
  "rules": [
    {
      "description": "Rename column",
      "rule_type": "mapping",
      "parameters": {"source_column": "Old", "target_column": "New"}
    }
  ],
  "clarifications": ["Need more info"]
}
"""

    rules, clarifications = service._parse_llm_response(json_response)

    assert len(rules) == 1
    assert rules[0].rule_type == "mapping"
    assert len(clarifications) == 1
    assert clarifications[0] == "Need more info"


def test_llm_service_parse_json_with_markdown():
    """Test parsing LLM response with markdown code blocks."""
    service = LLMService(api_key="test-key")

    markdown_response = """
Here's the parsed result:

```json
{
  "rules": [
    {
      "description": "Test rule",
      "rule_type": "filter",
      "parameters": {"column": "Status", "condition": "== 'Active'"}
    }
  ],
  "clarifications": []
}
```

Hope this helps!
"""

    rules, clarifications = service._parse_llm_response(markdown_response)

    assert len(rules) == 1
    assert rules[0].rule_type == "filter"
    assert len(clarifications) == 0


def test_generate_report():
    """Test report generation."""
    original_df = pd.DataFrame(
        {
            "Col1": [1, 2, 3],
            "Col2": ["a", "b", "c"],
        }
    )

    transformed_df = pd.DataFrame(
        {
            "Col1": [1, 2],
            "NewCol": ["x", "y"],
        }
    )

    rules = [
        TransformationRule(
            description="Filter rows",
            rule_type="filter",
            parameters={"column": "Col1", "condition": "< 3"},
        )
    ]

    service = AINormalizationService(llm_service=Mock())
    report = service._generate_report(
        original_df, transformed_df, rules, list(original_df.columns)
    )

    assert len(report) > 0
    assert "Original Row Count" in report["Metric"].values
    assert "Transformed Row Count" in report["Metric"].values


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
