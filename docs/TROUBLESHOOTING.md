# Environment Variable Configuration Guide

## Issue: "api_key client option must be set" Error

If you see this error when running the AI normalizer:
```
Failed to initialize OpenAI client: The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable
```

This means no API key was found in your environment. The tool looks for API keys in this order:

1. Command line argument: `--api-key your-key-here`
2. `OPENAI_API_KEY` environment variable  
3. `GITHUB_TOKEN` environment variable (for GitHub Models)

## Solutions

### Option 1: Use Command Line Argument (Recommended for Testing)
```bash
# For GitHub Models
python -m invitation.ai_normalizer_cli input.csv \
  --api-key github_pat_YOUR_TOKEN_HERE \
  --base-url https://models.github.ai/inference \
  --model openai/gpt-4o \
  --enterprise-key acme
```

### Option 2: Export Environment Variables in Your Shell

**For GitHub Models (dev/test):**
```bash
# Export variables in your current shell session
export GITHUB_TOKEN=github_pat_YOUR_TOKEN_HERE
export OPENAI_BASE_URL=https://models.github.ai/inference
export OPENAI_MODEL=openai/gpt-4o

# Verify they're set
echo $GITHUB_TOKEN
echo $OPENAI_BASE_URL
echo $OPENAI_MODEL

# Now run the tool
python -m invitation.ai_normalizer_cli input.csv --enterprise-key acme
```

**For Azure OpenAI (production):**
```bash
export OPENAI_API_KEY=your-azure-key-here
export OPENAI_BASE_URL=https://open-direct.openai.azure.com/openai/v1/
export OPENAI_MODEL=gpt-4o

python -m invitation.ai_normalizer_cli input.csv --enterprise-key acme
```

**For OpenAI (default):**
```bash
export OPENAI_API_KEY=sk-YOUR_OPENAI_KEY_HERE
export OPENAI_MODEL=gpt-4o

python -m invitation.ai_normalizer_cli input.csv --enterprise-key acme
```

### Option 3: Use .env File (Persistent Configuration)

Create a `.env` file in the project root directory:

```bash
# For GitHub Models
GITHUB_TOKEN=github_pat_YOUR_TOKEN_HERE
OPENAI_BASE_URL=https://models.github.ai/inference
OPENAI_MODEL=openai/gpt-4o
```

The tool will automatically load variables from `.env` if `python-dotenv` is installed.

## Verifying Your Configuration

Run this command to check if your environment variables are set:

```bash
# Check if variables are set
env | grep -E "GITHUB_TOKEN|OPENAI"
```

You should see output like:
```
GITHUB_TOKEN=github_pat_...
OPENAI_BASE_URL=https://models.github.ai/inference
OPENAI_MODEL=openai/gpt-4o
```

## Common Mistakes

### ❌ Setting variables without export
```bash
# This does NOT work - variable is only set in current line
GITHUB_TOKEN=github_pat_... python -m invitation.ai_normalizer_cli input.csv
```

### ✅ Correct way
```bash
# Export first, then run
export GITHUB_TOKEN=github_pat_...
python -m invitation.ai_normalizer_cli input.csv
```

### ❌ Setting in one terminal, running in another
Environment variables are per-shell session. If you set them in one terminal window and run the command in another, they won't be available.

### ✅ Correct way
Set and run in the same terminal session, or use `.env` file, or use `--api-key` argument.

## Issue 2: Missing Organization Column

If the tool doesn't ask about the required "Organization" column, this has been fixed in the latest version. The AI will now explicitly check that all three required columns (Mail, Organization, Team) are specified in your transformation rules.

**Example transformation that will be accepted:**
```
Transformation: "姓名"列对应"Name","Github账号邮箱"列对应"Mail","所属部门/业务单元"列对应"Team",同时需要增加上前缀"SH-"; 设置"Organization"为"mycompany"
```

**Example that will trigger clarification:**
```
Transformation: "姓名"列对应"Name","Github账号邮箱"列对应"Mail"
# AI will ask: "How should the 'Organization' column be set?" and "How should the 'Team' column be created?"
```

## Testing Your Setup

Create a test CSV file:
```bash
echo "Name,Email,Department" > test.csv
echo "John,john@example.com,Engineering" >> test.csv
```

Run the tool:
```bash
export GITHUB_TOKEN=your_token_here
export OPENAI_BASE_URL=https://models.github.ai/inference
export OPENAI_MODEL=openai/gpt-4o

python -m invitation.ai_normalizer_cli test.csv --enterprise-key test
```

If configuration is correct, you should see:
```
Analyzing input file: test.csv
CSV ANALYSIS
============================================================
Rows: 1
Columns: 3
...
```

If you see the "api_key must be set" error, your environment variables are not properly configured. Follow the steps above carefully.
