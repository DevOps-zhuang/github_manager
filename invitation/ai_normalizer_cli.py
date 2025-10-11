"""CLI interface for AI-assisted CSV data normalization."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from invitation.ai_normalization_service import (
    AINormalizationService,
    LLMService,
)


def display_csv_analysis(analysis: dict) -> None:
    """Display CSV analysis results to user."""
    print("\n" + "=" * 60)
    print("CSV ANALYSIS")
    print("=" * 60)
    print(f"Rows: {analysis['row_count']}")
    print(f"Columns: {analysis['column_count']}")
    print(f"\nColumn names: {', '.join(analysis['columns'])}")
    print("\nNull value counts:")
    for col, count in analysis["null_counts"].items():
        if count > 0:
            print(f"  {col}: {count}")
    print("\nSample rows:")
    for i, row in enumerate(analysis["sample_rows"], 1):
        print(f"  Row {i}: {row}")
    print("=" * 60 + "\n")


def collect_transformation_rules(service: AINormalizationService, columns: list[str]) -> list:
    """Interactively collect transformation rules from user."""
    print("\n" + "=" * 60)
    print("TRANSFORMATION RULES INPUT")
    print("=" * 60)
    print("Describe the transformations you want to apply.")
    print("Examples:")
    print('  - "Rename EmailAddress to Mail, Department to Team"')
    print('  - "Filter rows where Status equals Active"')
    print('  - "Set default value for Organization to MyCompany"')
    print('  - "Merge FirstName and LastName into FullName with space"')
    print('  - "Split FullAddress into Street, City, State by comma"')
    print("\nType your transformation rules (or 'done' when finished):")
    print("=" * 60 + "\n")

    all_rules = []
    rule_descriptions = []

    while True:
        user_input = input("Transformation: ").strip()
        if not user_input or user_input.lower() == "done":
            break

        rule_descriptions.append(user_input)
        print(f"Added rule {len(rule_descriptions)}: {user_input}")

    if not rule_descriptions:
        print("No transformation rules provided. Exiting.")
        return []

    # Combine all rules and parse
    combined_input = " AND ".join(rule_descriptions)
    print("\nParsing transformation rules...")

    rules, clarifications = service.parse_transformation_rules(combined_input, columns)

    # Handle clarifications
    if clarifications:
        print("\n" + "⚠" * 30)
        print("CLARIFICATION NEEDED")
        print("⚠" * 30)
        print("The following aspects of your request need clarification:\n")
        for i, question in enumerate(clarifications, 1):
            print(f"{i}. {question}")
        print("\nPlease refine your transformation rules and try again.")
        return []

    # Display parsed rules
    if rules:
        print("\n" + "✓" * 30)
        print("PARSED TRANSFORMATION RULES")
        print("✓" * 30)
        for i, rule in enumerate(rules, 1):
            print(f"{i}. [{rule.rule_type}] {rule.description}")
            print(f"   Parameters: {rule.parameters}")
        print("✓" * 30 + "\n")

    return rules


def confirm_execution(clean_path: Path, report_path: Path) -> bool:
    """Ask user to confirm execution."""
    print("\n" + "=" * 60)
    print("OUTPUT FILES")
    print("=" * 60)
    print(f"Clean data: {clean_path}")
    print(f"Report:     {report_path}")
    print("=" * 60 + "\n")

    response = input("Proceed with transformation? (yes/no): ").strip().lower()
    return response in ["yes", "y"]


def preview_generated_code(code: str) -> bool:
    """Show generated code and ask for confirmation."""
    print("\n" + "=" * 60)
    print("GENERATED TRANSFORMATION CODE")
    print("=" * 60)
    print(code)
    print("=" * 60 + "\n")

    response = input("Execute this code? (yes/no): ").strip().lower()
    return response in ["yes", "y"]


def main(argv: Sequence[str] | None = None) -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI-assisted CSV data normalization tool"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to input CSV file",
    )
    parser.add_argument(
        "--enterprise-key",
        type=str,
        default=None,
        help="Enterprise identifier for organizing files in invitation/customize/<Enterprise>/ directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for generated files (default: invitation/customize/<Enterprise>/ if enterprise-key provided, "
             "otherwise same as input directory)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for authentication (can also use OPENAI_API_KEY or GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLM model to use (default: gpt-4o, or OPENAI_MODEL env var). "
             "Examples: gpt-4o, gpt-4-turbo (OpenAI/Azure), openai/gpt-4o (GitHub Models)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="API endpoint URL (can also use OPENAI_BASE_URL env var). "
             "Examples: https://models.github.ai/inference (GitHub Models), "
             "https://open-direct.openai.azure.com/openai/v1/ (Azure OpenAI)",
    )
    parser.add_argument(
        "--api-version",
        type=str,
        default=None,
        help="API version for legacy Azure OpenAI (optional, not needed for Response API)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive mode: skip confirmations (not recommended)",
    )

    args = parser.parse_args(argv)

    # Validate input file
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Determine output directory based on enterprise-key
    if args.output_dir:
        output_dir = args.output_dir
    elif args.enterprise_key:
        # Use enterprise-specific directory structure
        enterprise_name = args.enterprise_key.capitalize()
        output_dir = Path("invitation") / "customize" / enterprise_name
        print(f"Using enterprise directory: {output_dir}")
    else:
        # Default to same directory as input
        output_dir = args.input.parent
    
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy source file to enterprise directory if using enterprise-key
    if args.enterprise_key and not args.output_dir:
        source_copy_path = output_dir / args.input.name
        if source_copy_path != args.input:
            import shutil
            shutil.copy2(args.input, source_copy_path)
            print(f"Copied source file to: {source_copy_path}")

    base_name = args.input.stem
    clean_path = output_dir / f"{base_name}_clean.csv"
    report_path = output_dir / f"{base_name}_report.csv"

    # Initialize services
    try:
        llm_service = LLMService(
            api_key=args.api_key,
            model=args.model,
            base_url=args.base_url,
            api_version=args.api_version,
        )
        service = AINormalizationService(llm_service=llm_service)
    except Exception as e:
        print(f"Error initializing AI service: {e}", file=sys.stderr)
        print("\nConfiguration help:", file=sys.stderr)
        print("  - For OpenAI: set OPENAI_API_KEY environment variable", file=sys.stderr)
        print("  - For GitHub Models: set GITHUB_TOKEN and OPENAI_BASE_URL=https://models.github.ai/inference", file=sys.stderr)
        print("  - For Azure OpenAI: set OPENAI_API_KEY and OPENAI_BASE_URL", file=sys.stderr)
        print("  - Or use --api-key command line argument", file=sys.stderr)
        sys.exit(1)

    # Analyze input CSV
    print(f"Analyzing input file: {args.input}")
    try:
        analysis = service.analyze_csv(args.input)
    except Exception as e:
        print(f"Error analyzing CSV: {e}", file=sys.stderr)
        sys.exit(1)

    display_csv_analysis(analysis)

    # Collect transformation rules
    rules = collect_transformation_rules(service, analysis["columns"])
    if not rules:
        print("No valid transformation rules. Exiting.")
        sys.exit(1)

    # Confirm output paths
    if not args.non_interactive:
        if not confirm_execution(clean_path, report_path):
            print("Transformation cancelled.")
            sys.exit(0)

    # Generate transformation code
    print("\nGenerating transformation code...")
    try:
        code = llm_service.generate_transformation_code(rules, analysis["columns"])
    except Exception as e:
        print(f"Error generating code: {e}", file=sys.stderr)
        sys.exit(1)

    # Show code and confirm
    if not args.non_interactive:
        if not preview_generated_code(code):
            print("Transformation cancelled.")
            sys.exit(0)

    # Execute transformation
    print("\nExecuting transformation...")
    result = service.execute_transformation(
        args.input,
        rules,
        output_clean_path=clean_path,
        output_report_path=report_path,
    )

    # Display results
    if result.success:
        print("\n" + "✓" * 30)
        print("TRANSFORMATION SUCCESSFUL")
        print("✓" * 30)
        print(f"Clean data written to: {clean_path}")
        print(f"Report written to:     {report_path}")
        if result.clean_data is not None:
            print(f"Output rows: {len(result.clean_data)}")
        print("✓" * 30 + "\n")
    else:
        print("\n" + "✗" * 30)
        print("TRANSFORMATION FAILED")
        print("✗" * 30)
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        print("✗" * 30 + "\n")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
