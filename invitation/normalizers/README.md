# Invitation Normalizers

This directory contains the core infrastructure for normalizing enterprise CSV data into the standard invitation format (`Mail, Organization, Team`).

## Directory Contents

- `base.py` - Base normalizer interface and common functionality
- `mapping.py` - Generic field mapping utilities for simple column name translation
- `registry.py` - Normalizer registration and discovery system
- `README.md` - This documentation

## Enterprise Integration

**Important: This directory contains NO enterprise-specific code or data.**

For enterprise-specific normalizers, create your implementation under `invitation/customize/<Enterprise>/`:

### Quick Start for New Enterprise

1. **Create enterprise directory:**
   ```
   invitation/customize/YourCompany/
   ├── normalizer.py          # Your normalizer implementation
   ├── original_data.csv      # Your raw CSV data
   └── processed_data.csv     # Output from normalization
   ```

2. **Implement your normalizer:**
   ```python
   # invitation/customize/YourCompany/normalizer.py
   from invitation.normalizers.base import BaseNormalizer
   
   class YourCompanyNormalizer(BaseNormalizer):
       def normalize_row(self, row):
           return {
               'Mail': row['EmailAddress'],  # Map your field names
               'Organization': self._map_department(row['Department']),
               'Team': row.get('Team', '')
           }
   ```

3. **Use the pipeline:**
   ```bash
   python -m invitation.pipeline yourcompany input.csv output.csv
   ```

### Dynamic Loading

The system automatically loads enterprise normalizers using this convention:
- Enterprise key: `yourcompany` 
- File path: `invitation/customize/YourCompany/normalizer.py`
- Class name: `YourCompanyNormalizer`

### Field Mapping vs Custom Logic

**Use mapping.py for simple cases:**
```python
# For simple column name translation
register_enterprise_mapping(
    "simple_corp",
    mail="EmailAddr", 
    organization="DeptName",
    team="TeamName"
)
```

**Use custom normalizer for complex cases:**
```python
# For business logic, data transformation, validation
class ComplexCorpNormalizer(BaseNormalizer):
    def normalize_row(self, row):
        # Custom parsing, validation, mapping logic
        return {...}
```

## Development Workflow

Since `invitation/customize/` is excluded from version control:

1. **Local Development**: Create and test your enterprise normalizers locally
2. **Documentation**: Document your enterprise-specific logic in your customize directory
3. **Deployment**: Share enterprise normalizers through secure channels (not git)
4. **Testing**: Use your actual enterprise data for testing (not sample data)

## Security

- All files under `invitation/customize/` are excluded from version control
- Never commit enterprise-specific data or business logic to the public repository
- Enterprise implementations should be shared through secure, private channels