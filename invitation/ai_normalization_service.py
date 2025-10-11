"""AI-powered data normalization service for CSV transformation."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd


@dataclass
class TransformationRule:
    """Represents a user-specified transformation rule."""

    description: str
    rule_type: str  # 'mapping', 'default', 'filter', 'merge', 'split'
    parameters: dict[str, Any]


@dataclass
class TransformationResult:
    """Result of applying transformation rules."""

    success: bool
    clean_data: pd.DataFrame | None
    report_data: pd.DataFrame | None
    errors: list[str]
    warnings: list[str]
    generated_code: str | None


class LLMService:
    """Abstraction layer for LLM interactions.
    
    Supports multiple LLM providers:
    - OpenAI (default)
    - GitHub Models (for dev/test)
    - Azure OpenAI (for production)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        api_version: str | None = None,
    ):
        """Initialize LLM service with flexible configuration.
        
        Args:
            api_key: API key for authentication. Falls back to OPENAI_API_KEY env var.
            model: Model name (e.g., 'gpt-4o', 'gpt-4'). Falls back to OPENAI_MODEL env var or 'gpt-4o'.
            base_url: API endpoint URL. Falls back to OPENAI_BASE_URL env var.
                     Examples:
                     - GitHub Models: https://models.inference.ai.azure.com
                     - Azure OpenAI: https://YOUR_RESOURCE.openai.azure.com/
            api_version: API version (for Azure OpenAI). Falls back to OPENAI_API_VERSION env var.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL")
        self.api_version = api_version or os.environ.get("OPENAI_API_VERSION")
        self._client = None

    def _get_client(self):
        """Lazy initialization of OpenAI client with configurable endpoint."""
        if self._client is None:
            try:
                import openai
                
                # Build client configuration
                client_kwargs = {"api_key": self.api_key}
                
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                
                if self.api_version:
                    # Azure OpenAI uses api_version parameter
                    client_kwargs["api_version"] = self.api_version
                
                self._client = openai.OpenAI(**client_kwargs)
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. Install it with: pip install openai"
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize OpenAI client: {e}")
        return self._client

    def parse_natural_language_rules(
        self, user_input: str, column_names: Sequence[str]
    ) -> tuple[list[TransformationRule], list[str]]:
        """Parse natural language transformation rules into structured format.

        Returns:
            Tuple of (parsed_rules, clarification_questions)
        """
        prompt = self._build_parsing_prompt(user_input, column_names)

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert data transformation assistant. Parse user requests into structured transformation rules.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )

            result_text = response.choices[0].message.content
            return self._parse_llm_response(result_text)

        except Exception as e:
            return [], [f"Error communicating with LLM: {str(e)}"]

    def _build_parsing_prompt(self, user_input: str, column_names: Sequence[str]) -> str:
        """Build prompt for parsing user transformation rules."""
        return f"""Given the following CSV columns: {', '.join(column_names)}

User request: "{user_input}"

Parse this into structured transformation rules. Return JSON in this format:
{{
  "rules": [
    {{
      "description": "Human-readable description",
      "rule_type": "mapping|default|filter|merge|split",
      "parameters": {{
        "source_column": "ColumnName",
        "target_column": "NewName",
        "default_value": "value",
        "condition": "expression",
        "delimiter": ","
      }}
    }}
  ],
  "clarifications": [
    "Question 1 if ambiguous",
    "Question 2 if conflicting"
  ]
}}

Rule types:
- mapping: Rename column (source_column -> target_column)
- default: Set default value for empty cells (column, default_value)
- filter: Keep only rows matching condition (column, condition)
- merge: Combine columns (source_columns, target_column, delimiter)
- split: Split column into multiple (source_column, target_columns, delimiter)

IMPORTANT VALIDATION RULES:
1. If the user references a column that does NOT exist in the CSV columns list, add a clarification question asking which actual column they meant.
2. For example, if user says "Rename OrgName to Organization" but "OrgName" is not in the columns, ask: "The column 'OrgName' does not exist. Did you mean one of these: [list actual column names]?"
3. Always verify that source columns exist before creating mapping/filter/merge/split rules.
4. If multiple columns are missing or the instruction is unclear, ask for clarification instead of guessing.

If the request is unclear, references non-existent columns, or is conflicting, include clarification questions.
Return ONLY valid JSON, no explanations."""

    def _parse_llm_response(
        self, response_text: str
    ) -> tuple[list[TransformationRule], list[str]]:
        """Parse LLM JSON response into transformation rules."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find JSON object
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    json_text = response_text

            data = json.loads(json_text)

            rules = [
                TransformationRule(
                    description=r["description"],
                    rule_type=r["rule_type"],
                    parameters=r["parameters"],
                )
                for r in data.get("rules", [])
            ]

            clarifications = data.get("clarifications", [])

            return rules, clarifications

        except json.JSONDecodeError as e:
            return [], [f"Failed to parse LLM response as JSON: {e}"]

    def generate_transformation_code(
        self, rules: Sequence[TransformationRule], column_names: Sequence[str]
    ) -> str:
        """Generate Python pandas code to execute transformation rules."""
        prompt = self._build_code_generation_prompt(rules, column_names)

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Python and pandas programmer. Generate safe, efficient transformation code.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )

            code = response.choices[0].message.content

            # Extract code from markdown blocks if present
            code_match = re.search(r"```python\s*(.*?)\s*```", code, re.DOTALL)
            if code_match:
                code = code_match.group(1)

            return code.strip()

        except Exception as e:
            raise RuntimeError(f"Failed to generate transformation code: {e}")

    def _build_code_generation_prompt(
        self, rules: Sequence[TransformationRule], column_names: Sequence[str]
    ) -> str:
        """Build prompt for code generation."""
        rules_description = "\n".join(
            [
                f"{i+1}. {rule.rule_type}: {rule.description} - params: {rule.parameters}"
                for i, rule in enumerate(rules)
            ]
        )

        return f"""Generate pandas transformation code for the following rules:

Available columns: {', '.join(column_names)}

Transformation rules:
{rules_description}

Requirements:
1. Define a function: def transform_data(df: pd.DataFrame) -> pd.DataFrame
2. The function should take a DataFrame and return the transformed DataFrame
3. Use only safe pandas operations (no eval, exec, or system calls)
4. Handle missing values gracefully
5. Add comments explaining each transformation
6. Preserve all original columns unless explicitly mapped/renamed
7. Return ONLY the function code, no explanations or markdown

Example structure:
def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    # Make a copy to avoid modifying original
    result = df.copy()
    
    # Apply transformations here
    ...
    
    return result
"""


class AINormalizationService:
    """Main service for AI-driven CSV normalization."""

    def __init__(self, llm_service: LLMService | None = None):
        """Initialize the AI normalization service."""
        self.llm_service = llm_service or LLMService()

    def analyze_csv(self, input_path: Path) -> dict[str, Any]:
        """Analyze input CSV and return metadata."""
        try:
            df = pd.read_csv(input_path, encoding="utf-8-sig")

            return {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "dtypes": df.dtypes.to_dict(),
                "null_counts": df.isnull().sum().to_dict(),
                "sample_rows": df.head(3).to_dict(orient="records"),
            }
        except Exception as e:
            raise RuntimeError(f"Failed to analyze CSV: {e}")

    def parse_transformation_rules(
        self, user_input: str, column_names: Sequence[str]
    ) -> tuple[list[TransformationRule], list[str]]:
        """Parse user's natural language transformation rules."""
        return self.llm_service.parse_natural_language_rules(user_input, column_names)

    def validate_transformation_code(self, code: str) -> tuple[bool, list[str]]:
        """Validate generated code for safety and correctness."""
        errors = []

        # Check for dangerous operations
        dangerous_patterns = [
            r"\beval\b",
            r"\bexec\b",
            r"\b__import__\b",
            r"\bopen\b",
            r"\bos\.",
            r"\bsys\.",
            r"\bsubprocess\b",
            r"\bimportlib\b",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, code):
                errors.append(f"Code contains potentially dangerous operation: {pattern}")

        # Check for required function signature
        if "def transform_data(df: pd.DataFrame) -> pd.DataFrame:" not in code:
            errors.append(
                "Code must define function: def transform_data(df: pd.DataFrame) -> pd.DataFrame:"
            )

        return len(errors) == 0, errors

    def execute_transformation(
        self,
        input_path: Path,
        rules: Sequence[TransformationRule],
        output_clean_path: Path | None = None,
        output_report_path: Path | None = None,
    ) -> TransformationResult:
        """Execute transformation rules on input CSV."""
        errors = []
        warnings = []

        try:
            # Load input data
            df = pd.read_csv(input_path, encoding="utf-8-sig")
            original_columns = list(df.columns)

            # Generate transformation code
            code = self.llm_service.generate_transformation_code(
                rules, df.columns.tolist()
            )

            # Validate code
            is_valid, validation_errors = self.validate_transformation_code(code)
            if not is_valid:
                errors.extend(validation_errors)
                return TransformationResult(
                    success=False,
                    clean_data=None,
                    report_data=None,
                    errors=errors,
                    warnings=warnings,
                    generated_code=code,
                )

            # Execute transformation in controlled namespace
            namespace: dict[str, Any] = {"pd": pd, "df": df}
            exec(code, namespace)

            transform_func = namespace.get("transform_data")
            if not callable(transform_func):
                errors.append("Generated code did not define transform_data function")
                return TransformationResult(
                    success=False,
                    clean_data=None,
                    report_data=None,
                    errors=errors,
                    warnings=warnings,
                    generated_code=code,
                )

            # Apply transformation
            transformed_df = transform_func(df)

            # Generate report
            report_data = self._generate_report(
                df, transformed_df, rules, original_columns
            )

            # Write outputs if paths provided
            if output_clean_path:
                output_clean_path.parent.mkdir(parents=True, exist_ok=True)
                transformed_df.to_csv(output_clean_path, index=False, encoding="utf-8")

            if output_report_path:
                output_report_path.parent.mkdir(parents=True, exist_ok=True)
                report_data.to_csv(output_report_path, index=False, encoding="utf-8")

            return TransformationResult(
                success=True,
                clean_data=transformed_df,
                report_data=report_data,
                errors=errors,
                warnings=warnings,
                generated_code=code,
            )

        except Exception as e:
            errors.append(f"Transformation execution failed: {str(e)}")
            return TransformationResult(
                success=False,
                clean_data=None,
                report_data=None,
                errors=errors,
                warnings=warnings,
                generated_code=code if "code" in locals() else None,
            )

    def _generate_report(
        self,
        original_df: pd.DataFrame,
        transformed_df: pd.DataFrame,
        rules: Sequence[TransformationRule],
        original_columns: list[str],
    ) -> pd.DataFrame:
        """Generate transformation report CSV."""
        report_rows = []

        # Summary statistics
        report_rows.append(
            {
                "Metric": "Original Row Count",
                "Value": str(len(original_df)),
                "Details": "",
            }
        )
        report_rows.append(
            {
                "Metric": "Transformed Row Count",
                "Value": str(len(transformed_df)),
                "Details": "",
            }
        )
        report_rows.append(
            {
                "Metric": "Rows Removed",
                "Value": str(len(original_df) - len(transformed_df)),
                "Details": "",
            }
        )

        # Column changes
        new_columns = set(transformed_df.columns) - set(original_columns)
        removed_columns = set(original_columns) - set(transformed_df.columns)

        if new_columns:
            report_rows.append(
                {
                    "Metric": "New Columns",
                    "Value": str(len(new_columns)),
                    "Details": ", ".join(new_columns),
                }
            )

        if removed_columns:
            report_rows.append(
                {
                    "Metric": "Removed Columns",
                    "Value": str(len(removed_columns)),
                    "Details": ", ".join(removed_columns),
                }
            )

        # Applied rules
        for i, rule in enumerate(rules, 1):
            report_rows.append(
                {
                    "Metric": f"Rule {i}",
                    "Value": rule.rule_type,
                    "Details": rule.description,
                }
            )

        return pd.DataFrame(report_rows)
