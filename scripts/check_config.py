"""Standalone configuration check utility.

Uses invitation.config_validation module to validate environment configuration.
Outputs JSON with validation results for CI/debugging purposes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from invitation.config_validation import validate_config, format_validation_summary

# Load .env file (override existing environment variables)
load_dotenv(override=True)


def main() -> int:
    """Run configuration validation and output results as JSON.
    
    Returns:
        0 if configuration is valid or degraded but functional
        2 if there are structural errors (unsupported API_TYPE)
    """
    result = validate_config()
    
    # Print human-readable summary
    print(format_validation_summary(result))
    print()
    
    # Print detailed JSON
    summary = {
        "is_valid": result.is_valid,
        "degraded_ai": result.degraded_ai,
        "errors": result.errors,
        "warnings": result.warnings,
        "effective": result.effective,
    }
    
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    # Exit code logic:
    # - Structural errors (unsupported type) → exit 2
    # - AI degraded but invitation can continue → exit 0
    # - All valid → exit 0
    if any("Unsupported API_TYPE" in e for e in result.errors):
        return 2
    
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
