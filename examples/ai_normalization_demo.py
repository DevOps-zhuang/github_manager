"""Demo script showing AI normalization workflow without requiring API keys."""

from pathlib import Path
from unittest.mock import Mock

import pandas as pd

from invitation.ai_normalization_service import (
    AINormalizationService,
    LLMService,
    TransformationRule,
)


def create_sample_data(output_path: Path):
    """Create sample CSV data for demonstration."""
    data = {
        "EmailAddress": [
            "alice@example.com",
            "bob@example.com",
            "charlie@example.com",
            "david@example.com",
        ],
        "FirstName": ["Alice", "Bob", "Charlie", "David"],
        "LastName": ["Smith", "Jones", "Brown", "Wilson"],
        "DepartmentName": ["Engineering", "Marketing", "Engineering", "Sales"],
        "Status": ["Active", "Active", "Inactive", "Active"],
    }

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Created sample data: {output_path}")
    return df


def demo_without_api():
    """Demonstrate the AI normalization workflow without actual API calls."""
    print("\n" + "=" * 70)
    print("AI-ASSISTED DATA NORMALIZATION DEMO")
    print("=" * 70)

    # Create sample data
    input_path = Path("/tmp/demo_input.csv")
    create_sample_data(input_path)

    # Initialize service with mocked LLM
    mock_llm = Mock(spec=LLMService)

    # Mock the LLM to return predefined transformation code
    mock_llm.generate_transformation_code.return_value = """
def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    # Make a copy to avoid modifying original
    result = df.copy()
    
    # AC1: Simple column mapping
    result = result.rename(columns={
        'EmailAddress': 'Mail',
        'DepartmentName': 'Team'
    })
    
    # AC1: Set default value for Organization
    result['Organization'] = 'github-demo-org'
    
    # AC2: Conditional filtering - keep only Active users
    result = result[result['Status'] == 'Active']
    
    # AC3: Merge FirstName and LastName
    result['FullName'] = result['FirstName'] + ' ' + result['LastName']
    
    # Drop unnecessary columns
    result = result.drop(columns=['FirstName', 'LastName', 'Status'])
    
    return result
"""

    service = AINormalizationService(llm_service=mock_llm)

    # Step 1: Analyze CSV
    print("\nStep 1: Analyzing CSV...")
    analysis = service.analyze_csv(input_path)
    print(f"  Rows: {analysis['row_count']}")
    print(f"  Columns: {', '.join(analysis['columns'])}")

    # Step 2: Define transformation rules
    print("\nStep 2: Transformation Rules...")
    rules = [
        TransformationRule(
            description="Rename EmailAddress to Mail",
            rule_type="mapping",
            parameters={"source_column": "EmailAddress", "target_column": "Mail"},
        ),
        TransformationRule(
            description="Rename DepartmentName to Team",
            rule_type="mapping",
            parameters={"source_column": "DepartmentName", "target_column": "Team"},
        ),
        TransformationRule(
            description="Set default Organization to github-demo-org",
            rule_type="default",
            parameters={"column": "Organization", "default_value": "github-demo-org"},
        ),
        TransformationRule(
            description="Filter rows where Status equals Active",
            rule_type="filter",
            parameters={"column": "Status", "condition": "== 'Active'"},
        ),
        TransformationRule(
            description="Merge FirstName and LastName into FullName",
            rule_type="merge",
            parameters={
                "source_columns": ["FirstName", "LastName"],
                "target_column": "FullName",
                "delimiter": " ",
            },
        ),
    ]

    for i, rule in enumerate(rules, 1):
        print(f"  {i}. [{rule.rule_type}] {rule.description}")

    # Step 3: Execute transformation
    print("\nStep 3: Executing transformation...")
    output_clean = Path("/tmp/demo_output_clean.csv")
    output_report = Path("/tmp/demo_output_report.csv")

    result = service.execute_transformation(
        input_path, rules, output_clean_path=output_clean, output_report_path=output_report
    )

    if result.success:
        print("  ✓ Transformation successful!")
        print(f"\nStep 4: Output files generated:")
        print(f"  Clean data: {output_clean}")
        print(f"  Report:     {output_report}")

        # Display results
        if result.clean_data is not None:
            print(f"\nTransformed data ({len(result.clean_data)} rows):")
            print(result.clean_data.to_string(index=False))

            print("\nTransformation Report:")
            if result.report_data is not None:
                print(result.report_data.to_string(index=False))

        print("\n" + "=" * 70)
        print("ACCEPTANCE CRITERIA COVERAGE")
        print("=" * 70)
        print("✓ AC1: Column mapping (EmailAddress→Mail) and defaults (Organization)")
        print("✓ AC2: Conditional filtering (Status == Active)")
        print("✓ AC3: Field merging (FirstName + LastName → FullName)")
        print("✓ AC4: Ambiguity detection (handled by LLM service)")
        print("✓ AC5: Dual file output (_clean.csv and _report.csv)")
        print("=" * 70)

    else:
        print("  ✗ Transformation failed!")
        for error in result.errors:
            print(f"    Error: {error}")


if __name__ == "__main__":
    demo_without_api()
