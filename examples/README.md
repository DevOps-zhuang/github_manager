# Examples Directory

This directory contains example scripts demonstrating how to use the AI-assisted data normalization feature.

## Available Examples

### ai_normalization_demo.py

A complete demonstration of the AI normalization workflow that runs without requiring an OpenAI API key.

**What it demonstrates:**
- CSV analysis
- Transformation rule parsing
- Code generation and validation
- Safe execution
- Report generation
- All 5 acceptance criteria

**How to run:**
```bash
python examples/ai_normalization_demo.py
```

**Expected output:**
- Sample CSV data is created
- Transformations are applied (rename, filter, merge)
- Clean and report CSVs are generated
- Summary shows before/after comparison

## Running the Real CLI

To use the actual AI normalization CLI with real data:

1. Set your OpenAI API key:
```bash
export OPENAI_API_KEY=your-key-here
```

2. Run the CLI:
```bash
python -m invitation.ai_normalizer_cli your_data.csv
```

3. Follow the interactive prompts to describe your transformations

## Example Transformation Descriptions

### Column Mapping
```
"Rename EmailAddress to Mail and Department to Team"
"Map OrgName to Organization"
```

### Default Values
```
"Set default Organization to MyOrg"
"Fill empty Team values with DefaultTeam"
```

### Filtering
```
"Keep only rows where Status equals Active"
"Filter rows where Age greater than 18"
"Only include rows where Country is USA and Status is Active"
```

### Column Merging
```
"Combine FirstName and LastName into FullName with space"
"Merge Street, City, State into Address with comma and space"
```

### Column Splitting
```
"Split FullName into FirstName and LastName by space"
"Separate Address into Street, City, Zip by comma"
```

## Integration Example

After AI normalization, use the output with the existing invitation pipeline:

```bash
# Step 1: AI normalize
python -m invitation.ai_normalizer_cli raw_employees.csv
# Output: raw_employees_clean.csv, raw_employees_report.csv

# Step 2: Invite to GitHub
python -m invitation.inviter raw_employees_clean.csv \
  --organization MyOrg \
  --token $GITHUB_TOKEN
```

## More Information

- User Guide: [docs/AI_NORMALIZATION.md](../docs/AI_NORMALIZATION.md)
- Integration Examples: [docs/INTEGRATION_EXAMPLE.md](../docs/INTEGRATION_EXAMPLE.md)
- Feature Summary: [docs/FEATURE_SUMMARY.md](../docs/FEATURE_SUMMARY.md)
- Workflow Diagrams: [docs/WORKFLOW_DIAGRAMS.md](../docs/WORKFLOW_DIAGRAMS.md)
