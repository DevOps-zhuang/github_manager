# Integration Example: AI Normalization + Invitation Pipeline

This example shows how to use AI-assisted normalization followed by the existing invitation workflow.

## Step 1: AI-Assisted Normalization

Start with raw enterprise data in any format:

```csv
EmailAddress,FirstName,LastName,DepartmentName,EmployeeStatus
alice@company.com,Alice,Smith,Engineering,Active
bob@company.com,Bob,Jones,Marketing,Active
charlie@company.com,Charlie,Brown,Engineering,Inactive
```

Use natural language to normalize:

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your-key-here

# Run AI normalization
python -m invitation.ai_normalizer_cli raw_employees.csv
```

Interactive session:
```
Transformation: Rename EmailAddress to Mail and DepartmentName to Team
Transformation: Set default Organization to my-github-org
Transformation: Filter rows where EmployeeStatus equals Active
Transformation: done
```

Output files:
- `raw_employees_clean.csv` - Ready for invitation pipeline
- `raw_employees_report.csv` - Transformation audit trail

## Step 2: Use with Invitation Pipeline

The `_clean.csv` output is now in standard format:

```csv
Mail,Organization,Team
alice@company.com,my-github-org,Engineering
bob@company.com,my-github-org,Marketing
```

Directly feed it to the invitation system:

```bash
# Run invitations
python -m invitation.inviter raw_employees_clean.csv \
  --organization my-github-org \
  --token $GITHUB_TOKEN \
  --mode grouped
```

## Complete Workflow Script

```bash
#!/bin/bash
set -e

# Configuration
INPUT_CSV="raw_employees.csv"
GITHUB_ORG="my-github-org"
GITHUB_TOKEN="${GITHUB_TOKEN:?GITHUB_TOKEN not set}"
OPENAI_API_KEY="${OPENAI_API_KEY:?OPENAI_API_KEY not set}"

echo "Step 1: AI-Assisted Normalization"
python -m invitation.ai_normalizer_cli "$INPUT_CSV" \
  --api-key "$OPENAI_API_KEY"

# The output will be raw_employees_clean.csv
CLEAN_CSV="${INPUT_CSV%.csv}_clean.csv"

echo ""
echo "Step 2: Verify normalized data"
head -5 "$CLEAN_CSV"

echo ""
echo "Step 3: Send GitHub invitations"
python -m invitation.inviter "$CLEAN_CSV" \
  --organization "$GITHUB_ORG" \
  --token "$GITHUB_TOKEN" \
  --mode grouped \
  --per-invite-delay 1.0

echo ""
echo "✓ Complete! Check invitation/reports/ for results"
```

## Benefits of This Workflow

1. **No Programming Required**: Business users describe transformations in plain English
2. **Audit Trail**: Both transformation and invitation results are tracked
3. **Safety**: Code is reviewed before execution, transformations are validated
4. **Flexibility**: Each step can be run independently or combined
5. **Transparency**: Generated code and reports provide full visibility

## Advanced: Batch Processing

Process multiple files with saved transformation rules:

```bash
# First file: Define transformations interactively
python -m invitation.ai_normalizer_cli dept_engineering.csv

# Subsequent files: Could reuse similar transformations
# (Future enhancement: save/load transformation templates)
```

## Integration with Existing Enterprise Normalizers

If you already have an enterprise-specific normalizer in `invitation/customize/`, you can:

1. Use AI normalization for **initial exploration** and **one-off imports**
2. Use enterprise normalizers for **regular, repeatable processes**
3. Use AI to **generate enterprise normalizer code** as a starting point

Example:
```bash
# Explore new data format with AI
python -m invitation.ai_normalizer_cli new_format.csv

# Review generated code from _report.csv
# If satisfied, save to invitation/customize/NewEnterprise/normalizer.py
# Then use: python -m invitation.pipeline newenterprise new_format.csv
```

## Troubleshooting

### API Key Issues
```bash
# Check if key is set
echo $OPENAI_API_KEY

# Set it if needed
export OPENAI_API_KEY=sk-...
```

### Output Files Not Created
- Check write permissions in output directory
- Ensure transformation succeeded (check for error messages)

### Invitation Failures
- Verify GitHub token has correct permissions
- Check rate limits: `invitation/reports/invitation_results.csv`
- Use `--dry-run` flag to preview before executing

## Next Steps

- See `docs/AI_NORMALIZATION.md` for detailed transformation examples
- See `README.md` for invitation pipeline options
- Run `examples/ai_normalization_demo.py` for a working demo
