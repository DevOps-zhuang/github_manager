# AI Normalization Configuration Guide

This guide explains how to configure the AI-assisted data normalization tool for different deployment environments and LLM providers.

## Overview

The tool supports flexible configuration through:
- **Environment variables** (recommended for production)
- **Command-line arguments** (useful for quick tests or overrides)
- **`.env` file** (convenient for local development)

## Configuration Options

| Parameter | Environment Variable | CLI Argument | Default | Description |
|-----------|---------------------|--------------|---------|-------------|
| API Key | `OPENAI_API_KEY` | `--api-key` | (required) | Authentication token for the LLM API |
| Model | `OPENAI_MODEL` | `--model` | `gpt-4o` | The LLM model to use |
| Base URL | `OPENAI_BASE_URL` | `--base-url` | OpenAI default | API endpoint URL |
| API Version | `OPENAI_API_VERSION` | `--api-version` | (optional) | API version (Azure OpenAI only) |
| Enterprise Key | N/A | `--enterprise-key` | (optional) | Organizes files in `invitation/customize/<Enterprise>/` |
| Output Directory | N/A | `--output-dir` | Auto-determined | Custom output location (overrides enterprise-key path) |

## Enterprise Directory Management

When using `--enterprise-key`, the tool automatically:
1. Creates `invitation/customize/<Enterprise>/` directory
2. Copies source CSV to this directory
3. Saves all outputs (`_clean.csv`, `_report.csv`) in this directory

This aligns with the existing enterprise normalizer convention and keeps enterprise data isolated.

## Deployment Scenarios

### 1. OpenAI (Default)

The simplest configuration uses OpenAI's API directly.

**Environment variables:**
```bash
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o
```

**Usage:**
```bash
python -m invitation.ai_normalizer_cli input.csv --enterprise-key acme
```

**Or with CLI arguments:**
```bash
python -m invitation.ai_normalizer_cli input.csv \
  --enterprise-key acme \
  --api-key sk-... \
  --model gpt-4o
```

### 2. GitHub Models (Dev/Test)

GitHub Models provides free access to various LLMs for development and testing.

**Setup:**
1. Get a GitHub token with access to GitHub Models
2. Configure the tool to use GitHub Models endpoint

**Environment variables:**
```bash
export GITHUB_TOKEN=github_pat_...
export OPENAI_BASE_URL=https://models.github.ai/inference
export OPENAI_MODEL=openai/gpt-4o
```

**Usage:**
```bash
python -m invitation.ai_normalizer_cli input.csv --enterprise-key acme
```

**Or with CLI arguments:**
```bash
python -m invitation.ai_normalizer_cli input.csv \
  --enterprise-key acme \
  --api-key github_pat_... \
  --base-url https://models.github.ai/inference \
  --model openai/gpt-4o
```

**Available Models on GitHub Models:**
- `openai/gpt-4o`
- `openai/gpt-4o-mini`
- `openai/gpt-4-turbo`
- And others - check [GitHub Models Marketplace](https://github.com/marketplace/models)

**Note:** GitHub Models requires model names in format `provider/model-name` (e.g., `openai/gpt-4o`).

### 3. Azure OpenAI (Production)

Azure OpenAI is recommended for production deployments due to enterprise-grade security and compliance.

**Setup:**
1. Create an Azure OpenAI resource
2. Deploy the desired model (e.g., gpt-4o)
3. Get your API key and endpoint URL

**Environment variables (using Response API - recommended):**
```bash
export OPENAI_API_KEY=your-azure-key
export OPENAI_BASE_URL=https://open-direct.openai.azure.com/openai/v1/
export OPENAI_MODEL=gpt-4o
```

**Usage:**
```bash
python -m invitation.ai_normalizer_cli input.csv --enterprise-key acme
```

**Or with CLI arguments:**
```bash
python -m invitation.ai_normalizer_cli input.csv \
  --enterprise-key acme \
  --api-key your-azure-key \
  --base-url https://open-direct.openai.azure.com/openai/v1/ \
  --model gpt-4o
```

**Note:** 
- For Azure OpenAI, the newer **Response API** (`https://open-direct.openai.azure.com/openai/v1/`) is recommended and does not require `api_version`
- The model name should match your deployment name in Azure
- Legacy Azure OpenAI endpoints with `api_version` are still supported for backward compatibility

## Using .env File

For local development, you can create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your settings
nano .env
```

**Example `.env` for GitHub Models:**
```
OPENAI_API_KEY=github_pat_...
OPENAI_BASE_URL=https://models.inference.ai.azure.com
OPENAI_MODEL=gpt-4o
```

**Example `.env` for Azure OpenAI:**
```
OPENAI_API_KEY=your-azure-key
OPENAI_BASE_URL=https://YOUR_RESOURCE.openai.azure.com/
OPENAI_API_VERSION=2024-02-15-preview
OPENAI_MODEL=gpt-4o
```

The tool will automatically load settings from `.env` if `python-dotenv` is installed.

## Model Selection

### Recommended Models

| Model | Use Case | Speed | Quality | Cost |
|-------|----------|-------|---------|------|
| `gpt-4o` | **Recommended** - Best balance | Fast | Excellent | Medium |
| `gpt-4o-mini` | Quick tests, simple transformations | Fastest | Good | Low |
| `gpt-4-turbo` | Complex transformations | Medium | Excellent | Medium-High |
| `gpt-4` | Maximum accuracy needed | Slower | Excellent | High |

### Switching Models

**Via environment variable:**
```bash
export OPENAI_MODEL=gpt-4o-mini
```

**Via command line:**
```bash
python -m invitation.ai_normalizer_cli input.csv --model gpt-4o-mini
```

## Configuration Priority

Settings are applied in this order (highest to lowest priority):

1. **Command-line arguments** (`--api-key`, `--model`, etc.)
2. **Environment variables** (`OPENAI_API_KEY`, `OPENAI_MODEL`, etc.)
3. **Default values** (e.g., model defaults to `gpt-4o`)

This allows you to:
- Set defaults via environment variables
- Override for specific runs with CLI arguments

## Security Best Practices

### API Keys

❌ **Never:**
- Commit API keys to version control
- Share API keys in documentation or examples
- Hardcode API keys in scripts

✅ **Always:**
- Use environment variables or `.env` files
- Add `.env` to `.gitignore`
- Rotate keys regularly
- Use separate keys for dev/test/production

### Azure OpenAI

For production use with Azure OpenAI:
- Use Azure Key Vault for secrets management
- Enable Azure Active Directory authentication
- Configure network restrictions
- Monitor usage with Azure Monitor

## Troubleshooting

### "Error initializing AI service"

**Possible causes:**
1. API key not set
2. Invalid API key
3. Wrong base URL
4. Network connectivity issues

**Solutions:**
```bash
# Check if API key is set
echo $OPENAI_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     $OPENAI_BASE_URL/models
```

### "Model not found"

**For Azure OpenAI:**
- Ensure the model is deployed in your Azure resource
- Use the **deployment name**, not the model name
- Check the deployment is active

**For GitHub Models:**
- Verify the model is available in GitHub Models
- Check your GitHub token has the required permissions

### Rate Limiting

If you encounter rate limits:

**OpenAI:**
- Consider upgrading your plan
- Implement retry logic with exponential backoff
- Use a cheaper/faster model for development

**GitHub Models:**
- Rate limits are per-token; wait and retry
- Switch to paid Azure OpenAI for production

**Azure OpenAI:**
- Increase TPM (tokens per minute) quota in Azure
- Use multiple deployments for load balancing

## Environment-Specific Configurations

### Development
```bash
# Use GitHub Models for free access
export OPENAI_API_KEY=github_pat_...
export OPENAI_BASE_URL=https://models.inference.ai.azure.com
export OPENAI_MODEL=gpt-4o-mini  # Faster, cheaper
```

### Testing
```bash
# Use GitHub Models with full model
export OPENAI_API_KEY=github_pat_...
export OPENAI_BASE_URL=https://models.inference.ai.azure.com
export OPENAI_MODEL=gpt-4o
```

### Production
```bash
# Use Azure OpenAI for reliability
export OPENAI_API_KEY=your-azure-key
export OPENAI_BASE_URL=https://YOUR_RESOURCE.openai.azure.com/
export OPENAI_API_VERSION=2024-02-15-preview
export OPENAI_MODEL=gpt-4o
```

## Validating Configuration

Test your configuration:

```bash
# Run the demo (uses mocked LLM, no API calls)
python examples/ai_normalization_demo.py

# Test with a real CSV (makes API calls)
python -m invitation.ai_normalizer_cli test.csv

# Check help for available options
python -m invitation.ai_normalizer_cli --help
```

## Advanced: Multiple Configurations

For managing multiple environments, create separate `.env` files:

```bash
.env.dev         # GitHub Models configuration
.env.test        # GitHub Models with full model
.env.production  # Azure OpenAI configuration
```

Load the appropriate one:
```bash
# Development
ln -sf .env.dev .env

# Production
ln -sf .env.production .env
```

Or use a tool like `direnv` for automatic environment switching.

## Summary

- **Development/Test:** Use GitHub Models (free, easy setup)
- **Production:** Use Azure OpenAI (enterprise-grade, secure)
- **Default Model:** `gpt-4o` (best balance of speed/quality/cost)
- **Configuration:** Environment variables > CLI arguments > defaults
- **Security:** Never commit secrets, use environment variables

For more information, see:
- [User Guide](AI_NORMALIZATION.md)
- [Integration Examples](INTEGRATION_EXAMPLE.md)
- [Feature Summary](FEATURE_SUMMARY.md)
