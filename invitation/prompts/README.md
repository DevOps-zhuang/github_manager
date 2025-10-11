# Prompts Directory

This directory contains prompt templates used by the AI normalization service.

## Prompt Files

### parse_rules.txt
Template for parsing natural language transformation rules into structured format.

**Variables:**
- `{column_names}`: Comma-separated list of CSV column names
- `{user_input}`: User's natural language transformation request

**Purpose:** 
- Converts natural language to structured TransformationRule objects
- Validates column references
- Detects ambiguities and returns clarification questions

### generate_code.txt
Template for generating Python pandas transformation code.

**Variables:**
- `{column_names}`: Comma-separated list of CSV column names  
- `{rules_description}`: Formatted list of transformation rules

**Purpose:**
- Generates executable Python code from transformation rules
- Ensures code safety (no eval, exec, etc.)
- Creates well-documented, efficient pandas operations

## Modifying Prompts

To customize the AI behavior:

1. Edit the appropriate `.txt` file in this directory
2. Maintain the `{variable}` placeholders for dynamic content
3. Test changes with various CSV files and transformation scenarios
4. Update this README if you add new templates

## Adding New Prompts

To add a new prompt template:

1. Create a new `.txt` file in this directory
2. Use `{variable_name}` syntax for dynamic content
3. Load it in `ai_normalization_service.py` using `_load_prompt_template("filename")`
4. Document the template in this README

## Best Practices

- Keep prompts focused and specific
- Include clear examples in the prompt
- Specify output format requirements explicitly
- Test prompts with edge cases (empty columns, special characters, etc.)
- Version control prompt changes to track behavior modifications
