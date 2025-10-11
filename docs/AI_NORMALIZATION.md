# AI-Assisted Data Normalization

## Overview

This tool provides an AI-powered command-line interface for normalizing CSV data. Instead of writing custom normalization code, users can describe transformations in natural language, and the AI will generate and execute the appropriate transformation code.

## Features

### Acceptance Criteria Coverage

- **AC1: Simple column mapping and default values** ✓
  - Rename columns with natural language: "Rename EmailAddress to Mail"
  - Set default values: "Set default value for Team to DefaultTeam"

- **AC2: Conditional filtering** ✓
  - Filter rows based on conditions: "Keep only rows where Status equals Active"
  - Complex conditions: "Filter rows where Age > 18 AND Country equals USA"

- **AC3: Complex field merge/split operations** ✓
  - Merge columns: "Combine FirstName and LastName into FullName with space"
  - Split columns: "Split Address into Street, City, State by comma"

- **AC4: Ambiguity detection** ✓
  - The AI detects unclear or conflicting instructions
  - Prompts users to clarify before proceeding

- **AC5: Dual file output** ✓
  - Generates `_clean.csv` with transformed data
  - Generates `_report.csv` with transformation summary

## Architecture

The implementation follows separation of concerns:

```
invitation/
  ├── ai_normalization_service.py   # Core service logic
  └── ai_normalizer_cli.py          # CLI interface
```

### Key Components

1. **LLMService**: Abstraction layer for LLM interactions
   - Parse natural language rules
   - Generate transformation code
   - Model-agnostic design (OpenAI by default, extensible)

2. **AINormalizationService**: Core transformation logic
   - CSV analysis
   - Code validation
   - Safe execution in controlled namespace
   - Report generation

3. **CLI**: Interactive user interface
   - Guided transformation rule collection
   - Preview and confirmation workflow
   - Clear feedback and error messages

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure API settings:

   **Option A: Environment variables** (recommended)
   ```bash
   export OPENAI_API_KEY=your-api-key-here
   export OPENAI_MODEL=gpt-4o
   ```

   **Option B: Using `.env` file**
   ```
   OPENAI_API_KEY=your-api-key-here
   OPENAI_MODEL=gpt-4o
   ```

   **For GitHub Models (dev/test):**
   ```bash
   export OPENAI_API_KEY=your-github-models-token
   export OPENAI_BASE_URL=https://models.inference.ai.azure.com
   export OPENAI_MODEL=gpt-4o
   ```

   **For Azure OpenAI (production):**
   ```bash
   export OPENAI_API_KEY=your-azure-key
   export OPENAI_BASE_URL=https://YOUR_RESOURCE.openai.azure.com/
   export OPENAI_API_VERSION=2024-02-15-preview
   export OPENAI_MODEL=gpt-4o
   ```

## Usage

### Basic Usage

```bash
python -m invitation.ai_normalizer_cli input.csv
```

The tool will:
1. Analyze your CSV and show column information
2. Prompt you to describe transformations
3. Parse your instructions and show what it understood
4. Generate transformation code and ask for confirmation
5. Execute the transformation and create output files

### Command-Line Options

```bash
python -m invitation.ai_normalizer_cli input.csv [options]

Options:
  --enterprise-key KEY   Enterprise identifier for organizing files in 
                         invitation/customize/<Enterprise>/ directory
  --output-dir DIR       Output directory (default: invitation/customize/<Enterprise>/ 
                         if enterprise-key provided, otherwise same as input)
  --api-key KEY          API key for authentication (default: from OPENAI_API_KEY env)
  --model MODEL          LLM model to use (default: gpt-4o, or OPENAI_MODEL env)
                         Examples: gpt-4o, gpt-4, gpt-4-turbo
  --base-url URL         API endpoint URL (default: from OPENAI_BASE_URL env)
                         Examples: https://models.inference.ai.azure.com (GitHub Models)
                                  https://YOUR_RESOURCE.openai.azure.com/ (Azure OpenAI)
  --api-version VERSION  API version for Azure OpenAI (default: from OPENAI_API_VERSION env)
  --non-interactive      Skip confirmations (not recommended)
```

### Examples with Different Providers

**Using OpenAI directly:**
```bash
python -m invitation.ai_normalizer_cli input.csv --enterprise-key acme --model gpt-4o
```

**Using GitHub Models (dev/test):**
```bash
python -m invitation.ai_normalizer_cli input.csv \
  --enterprise-key acme \
  --base-url https://models.inference.ai.azure.com \
  --model gpt-4o
```

**Using Azure OpenAI (production):**
```bash
python -m invitation.ai_normalizer_cli input.csv \
  --enterprise-key acme \
  --base-url https://YOUR_RESOURCE.openai.azure.com/ \
  --api-version 2024-02-15-preview \
  --model gpt-4o
```

### Enterprise Directory Structure

When using `--enterprise-key`, the tool automatically organizes files following the convention:
- **Input file copied to**: `invitation/customize/<Enterprise>/<original-filename>.csv`
- **Clean output**: `invitation/customize/<Enterprise>/<original-filename>_clean.csv`
- **Report output**: `invitation/customize/<Enterprise>/<original-filename>_report.csv`

This structure aligns with the existing enterprise normalizer convention and keeps all enterprise-specific data organized.

### Example Session

```
$ python -m invitation.ai_normalizer_cli data/users.csv --enterprise-key acme

Analyzing input file: data/users.csv

============================================================
CSV ANALYSIS
============================================================
Rows: 100
Columns: 5

Column names: EmailAddress, FirstName, LastName, Department, Status

Sample rows:
  Row 1: {'EmailAddress': 'john@example.com', 'FirstName': 'John', ...}
  ...
============================================================

============================================================
TRANSFORMATION RULES INPUT
============================================================
Describe the transformations you want to apply.
Examples:
  - "Rename EmailAddress to Mail, Department to Team"
  - "Filter rows where Status equals Active"
  - "Set default Organization to my-company"
  ...
============================================================

Transformation: Rename EmailAddress to Mail and Department to Team
Added rule 1: Rename EmailAddress to Mail and Department to Team

Transformation: Filter rows where Status equals Active
Added rule 2: Filter rows where Status equals Active

Transformation: Set default Organization to acme-corp
Added rule 3: Set default Organization to acme-corp

Transformation: done

Parsing transformation rules...

✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓
PARSED TRANSFORMATION RULES
✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓
1. [mapping] Rename EmailAddress to Mail
   Parameters: {'source_column': 'EmailAddress', 'target_column': 'Mail'}
2. [mapping] Rename Department to Team
   Parameters: {'source_column': 'Department', 'target_column': 'Team'}
3. [filter] Keep rows where Status equals Active
   Parameters: {'column': 'Status', 'condition': '== "Active"'}
✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓

============================================================
OUTPUT FILES
============================================================
Clean data: data/users_clean.csv
Report:     data/users_report.csv
============================================================

Proceed with transformation? (yes/no): yes

Generating transformation code...

============================================================
GENERATED TRANSFORMATION CODE
============================================================
def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    
    # Rename EmailAddress to Mail
    result = result.rename(columns={'EmailAddress': 'Mail'})
    
    # Rename Department to Team
    result = result.rename(columns={'Department': 'Team'})
    
    # Filter rows where Status equals Active
    result = result[result['Status'] == 'Active']
    
    return result
============================================================

Execute this code? (yes/no): yes

Executing transformation...

✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓
TRANSFORMATION SUCCESSFUL
✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓
Clean data written to: data/users_clean.csv
Report written to:     data/users_report.csv
Output rows: 75
✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓
```

## Transformation Types

### 1. Column Mapping
Rename columns to match standard schema:
```
"Rename EmailAddress to Mail"
"Rename Department to Team and EmailAddress to Mail"
```

**Note**: The AI will detect if you reference a column that doesn't exist in your CSV and ask for clarification. For example, if you say "Rename OrgName to Organization" but there's no "OrgName" column, it will ask which actual column you meant.

### 2. Default Values
Fill empty cells with default values:
```
"Set default value for Team to DefaultTeam"
"Set default Organization to MyCompany"
"Fill empty Organization with UnknownOrg"
```

### 3. Filtering
Keep only rows matching conditions:
```
"Keep only rows where Status equals Active"
"Filter rows where Age > 18"
"Only include rows where Country is USA and Status is Active"
```

### 4. Column Merging
Combine multiple columns:
```
"Merge FirstName and LastName into FullName with space"
"Combine Street, City, State into Address with comma"
```

### 5. Column Splitting
Split a column into multiple columns:
```
"Split FullName into FirstName and LastName by space"
"Separate Address into Street, City, State by comma"
```

## Safety Features

1. **Code Validation**: Generated code is checked for dangerous operations
   - No `eval()` or `exec()` in unsafe contexts
   - No file system access
   - No system calls

2. **User Confirmation**: Multiple confirmation steps
   - Review parsed rules before code generation
   - Preview generated code before execution
   - Confirm output paths

3. **Sandboxed Execution**: Code runs in controlled namespace
   - Only pandas and necessary imports available
   - No access to system modules

4. **Error Handling**: Comprehensive error messages
   - Clear indication of what went wrong
   - Suggestions for fixing issues

## Output Files

### Clean CSV (`_clean.csv`)
Contains the transformed data ready for use in the invitation pipeline.

### Report CSV (`_report.csv`)
Contains transformation summary:
- Original and final row counts
- Rows removed by filters
- New/removed columns
- Applied transformation rules

Example report:
```csv
Metric,Value,Details
Original Row Count,100,
Transformed Row Count,75,
Rows Removed,25,
Rule 1,mapping,Rename EmailAddress to Mail
Rule 2,filter,Keep rows where Status equals Active
```

## Integration with Existing Pipeline

The AI-normalized output can be used directly with the existing invitation pipeline:

```bash
# 1. AI-assisted normalization
python -m invitation.ai_normalizer_cli raw_data.csv

# 2. Use the clean output with existing pipeline
python -m invitation.inviter raw_data_clean.csv --organization MyOrg --token $GITHUB_TOKEN
```

## Limitations

1. **API Requirements**: Requires OpenAI API access (or compatible endpoint)
2. **Cost**: API calls incur costs (minimal for typical CSV files)
3. **Complexity**: Very complex transformations may require manual code
4. **Validation**: Always review generated code before execution

## Future Enhancements

- Support for additional LLM providers (Anthropic, local models)
- Batch processing multiple files
- Saved transformation templates
- Web UI interface
- Integration with existing enterprise normalizers

## Troubleshooting

### "Error initializing AI service"
- Ensure OPENAI_API_KEY is set
- Check API key validity
- Verify network connectivity

### "Code contains potentially dangerous operation"
- Review the transformation rules
- The AI generated unsafe code - try rephrasing
- Contact maintainers if legitimate use case

### "Failed to parse LLM response"
- Try simpler, more explicit transformation descriptions
- Break complex rules into multiple steps
- Check API connectivity

### Ambiguity Warnings
- The AI needs more specific instructions
- Answer clarification questions
- Be explicit about column names and conditions
