"""CLI interface for AI-assisted CSV data normalization."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Sequence

from invitation.ai_normalization_service import (
    AINormalizationService,
    LLMService,
)
from invitation.config_validation import (
    validate_config,
    format_validation_summary,
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


def collect_transformation_rules(
    service: AINormalizationService, columns: list[str]
) -> list | None:
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

    rule_descriptions: list[str] = []
    first_pass = True

    while True:
        if not first_pass:
            print("\nAdd more instructions (or type 'done' to continue, 'cancel' to abort):")
        first_pass = False

        while True:
            user_input = input("Transformation: ").strip()
            if not user_input:
                break
            if user_input.lower() == "done":
                break
            if user_input.lower() == "cancel":
                print("Transformation session cancelled by user.")
                return None

            rule_descriptions.append(user_input)
            print(f"Added rule {len(rule_descriptions)}: {user_input}")

        if not rule_descriptions:
            response = input("No rules entered. Cancel session? (yes to cancel / no to retry): ").strip().lower()
            if response in {"yes", "y", "cancel"}:
                print("Transformation session cancelled by user.")
                return None
            continue

        clarification_notes: list[str] = []

        while True:
            combined_segments = rule_descriptions + clarification_notes
            combined_input = " AND ".join(combined_segments)
            print("\nParsing transformation rules...")
            rules, clarifications = service.parse_transformation_rules(combined_input, columns)

            if clarifications:
                print("\n" + "⚠" * 30)
                print("CLARIFICATION NEEDED")
                print("⚠" * 30)
                print("The following aspects of your request need clarification:\n")
                for i, question in enumerate(clarifications, 1):
                    print(f"{i}. {question}")

                new_notes: list[str] = []
                for idx, question in enumerate(clarifications, 1):
                    answer = input(
                        f"Clarification {idx} response (type 'cancel' to abort, leave blank to skip): "
                    ).strip()
                    if answer.lower() == "cancel":
                        print("Transformation session cancelled by user.")
                        return None
                    if answer:
                        new_notes.append(f"{question} -> {answer}")

                if not new_notes:
                    retry = input(
                        "No clarifications provided. Add more instructions manually? (yes/no): "
                    ).strip().lower()
                    if retry in {"yes", "y"}:
                        break  # exit clarification loop, return to outer input loop for more rules
                    reconsider = input(
                        "Would you like to cancel the session? (yes/no): "
                    ).strip().lower()
                    if reconsider in {"yes", "y", "cancel"}:
                        print("Transformation session cancelled by user.")
                        return None
                    print("Retrying clarification collection...")
                    continue

                clarification_notes.extend(new_notes)
                continue

            # Clarifications resolved; display parsed rules
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


def _sanitize_enterprise_key(raw_key: str) -> str:
    """Normalize enterprise key into a filesystem-friendly name."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", raw_key.strip())
    return cleaned or "enterprise"


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
        help="API key for authentication (can also use API_KEY or GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLM model to use (default: gpt-4o, or MODEL_NAME env var). "
             "Examples: gpt-4o, gpt-4-turbo",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="API endpoint URL (can also use API_BASE_URL env var). "
             "Required for azure/custom API_TYPE. "
             "Examples: https://models.github.ai/inference (GitHub Models), "
             "https://your-resource.openai.azure.com/openai/v1/ (Azure OpenAI)",
    )
    parser.add_argument(
        "--api-version",
        type=str,
        default=None,
        help="API version for legacy Azure OpenAI (optional, use API_VERSION env var)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive mode: skip confirmations (not recommended)",
    )

    args = parser.parse_args(argv)

    if not args.enterprise_key and args.non_interactive:
        print("Error: --enterprise-key is required in non-interactive mode.", file=sys.stderr)
        sys.exit(1)

    if not args.enterprise_key:
        entered_key = input("Enterprise key (required): ").strip()
        if not entered_key:
            print("Error: enterprise key is required to continue.", file=sys.stderr)
            sys.exit(1)
        args.enterprise_key = entered_key

    # Validate input file
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Determine output directory based on enterprise-key
    enterprise_dir: Path | None = None
    if args.enterprise_key:
        sanitized = _sanitize_enterprise_key(args.enterprise_key)
        enterprise_dir = Path("invitation") / "customize" / sanitized
    
    if args.output_dir:
        output_dir = args.output_dir
    elif enterprise_dir is not None:
        output_dir = enterprise_dir
        print(f"Using enterprise directory: {output_dir}")
    else:
        output_dir = args.input.parent

    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy source file to enterprise directory if using enterprise-key
    if enterprise_dir is not None:
        enterprise_dir.mkdir(parents=True, exist_ok=True)
        source_copy_path = enterprise_dir / args.input.name
        if source_copy_path.resolve() != args.input.resolve():
            import shutil

            shutil.copy2(args.input, source_copy_path)
            print(f"Copied source file to: {source_copy_path}")

    base_name = args.input.stem
    clean_path = output_dir / f"{base_name}_clean.csv"
    report_path = output_dir / f"{base_name}_report.csv"

    # Validate configuration before initializing services
    cli_overrides = {
        "api_key": args.api_key,
        "model_name": args.model,
        "api_base_url": args.base_url,
        "api_version": args.api_version,
    }
    validation = validate_config(cli_overrides)
    
    # Print validation summary
    print(format_validation_summary(validation))
    
    # Display warnings
    for warning in validation.warnings:
        print(f"⚠️  Warning: {warning}", file=sys.stderr)
    
    # Check if AI is degraded
    if validation.degraded_ai:
        print("\n" + "=" * 60, file=sys.stderr)
        print("AI CONFIGURATION UNAVAILABLE", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("The AI normalization feature requires valid configuration.", file=sys.stderr)
        print("\nErrors detected:", file=sys.stderr)
        for error in validation.errors:
            print(f"  ❌ {error}", file=sys.stderr)
        print("\nPlease fix the configuration and try again.", file=sys.stderr)
        print("\nConfiguration help:", file=sys.stderr)
        print("  - Set API_TYPE (openai/github/azure/custom) in environment", file=sys.stderr)
        print("  - For OpenAI: API_KEY=sk-xxx", file=sys.stderr)
        print("  - For GitHub Models: API_KEY=ghu_xxx or GITHUB_TOKEN=github_pat_xxx", file=sys.stderr)
        print("  - For Azure/Custom: API_KEY + API_BASE_URL required", file=sys.stderr)
        print("\nSee docs/CONFIGURATION.md for detailed examples.", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(0)  # Friendly exit, not an error

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
        print("  - For OpenAI: set API_KEY environment variable", file=sys.stderr)
        print("  - For GitHub Models: set GITHUB_TOKEN or API_KEY and API_BASE_URL=https://models.github.ai/inference", file=sys.stderr)
        print("  - For Azure OpenAI: set API_KEY and API_BASE_URL", file=sys.stderr)
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
    if rules is None:
        print("Transformation cancelled by user.")
        sys.exit(0)
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

    if enterprise_dir is not None:
        generated_code_path = enterprise_dir / "normalizer.py"
        try:
            generated_code_path.write_text(code, encoding="utf-8")
            print(f"Saved generated code to: {generated_code_path}")
        except Exception as e:
            print(f"Warning: failed to write generated code file: {e}", file=sys.stderr)

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
