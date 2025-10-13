# User Authentication Module

This module provides robust validation for Chinese user identity information.

## Features

- **Phone Number Validation**: Validates Chinese mainland mobile phone numbers (11 digits starting with 1[3-9])
- **ID Card Validation**: Validates Chinese 18-digit ID card numbers with:
  - Format verification
  - Region code validation
  - Birth date validation
  - Check digit verification
  - Age verification (must be 18+)
- **Failure Logging**: Automatically logs all validation failures to `logs/validation_failures.log`

## Installation

Add the required dependency to your `requirements.txt`:

```
id-validator
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Validation Service

The `validate_user` function provides dual validation - if either phone or ID card is valid, the user is considered validated:

```python
from auth.service import validate_user

# Validate user with both phone and ID card
result = validate_user("13812345678", "110101199003078515")
print(f"Validation result: {result}")  # True if at least one is valid

# If both fail, the failure is logged to logs/validation_failures.log
result = validate_user("invalid", "invalid")  # Returns False and logs failure
```

### Individual Validators

You can also use individual validators for specific validation needs:

```python
from auth.validators import is_valid_phone, is_valid_id_card

# Validate phone number only
if is_valid_phone("13812345678"):
    print("Phone number is valid")

# Validate ID card only
if is_valid_id_card("110101199003078515"):
    print("ID card is valid and holder is 18+")
```

## Validation Rules

### Phone Number
- Must be exactly 11 digits
- Must start with 1
- Second digit must be 3-9
- Pattern: `^1[3-9]\d{9}$`

### ID Card
- Must be exactly 18 characters
- Format: 6-digit region code + 8-digit birth date (YYYYMMDD) + 3-digit sequence + 1 check digit
- Region code must be valid
- Birth date must exist (e.g., not Feb 30)
- Check digit must be correct (calculated using official algorithm)
- **Age must be 18 or older**

## Logging

Failed validations are automatically logged to `logs/validation_failures.log` with:
- Timestamp
- Log level (INFO)
- Input values (phone and ID card)
- Failure reasons

Log format:
```
2025-10-13 06:59:00,279 - INFO - Validation failed: phone=12345, id_card=invalid, reasons=[invalid phone number, invalid ID card]
```

## Example

See `demo_validation.py` for a complete working example:

```bash
python demo_validation.py
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_validators -v
python -m unittest tests.test_service -v
```

## API Reference

### `auth.validators`

#### `is_valid_phone(phone: str) -> bool`
Validates a Chinese mainland phone number.

**Parameters:**
- `phone` (str): Phone number string to validate

**Returns:**
- `bool`: True if valid, False otherwise

**Example:**
```python
is_valid_phone("13812345678")  # True
is_valid_phone("12012345678")  # False (starts with 2)
```

#### `is_valid_id_card(id_card: str) -> bool`
Validates a Chinese 18-digit ID card number with age verification.

**Parameters:**
- `id_card` (str): ID card number string to validate

**Returns:**
- `bool`: True if valid and holder is 18+, False otherwise

**Example:**
```python
is_valid_id_card("110101199003078515")  # True (valid and over 18)
is_valid_id_card("110101199003078516")  # False (invalid checksum)
```

### `auth.service`

#### `validate_user(phone: str, id_card: str) -> bool`
Validates user identity using phone number and/or ID card.

**Parameters:**
- `phone` (str): Phone number to validate
- `id_card` (str): ID card number to validate

**Returns:**
- `bool`: True if at least one validation passes, False if both fail

**Side Effects:**
- Logs failure details to `logs/validation_failures.log` when both validations fail

**Example:**
```python
validate_user("13812345678", "")  # True (valid phone)
validate_user("", "110101199003078515")  # True (valid ID card)
validate_user("invalid", "invalid")  # False (logs failure)
```

## Notes

- The `logs/` directory and log files are automatically excluded from version control (via `.gitignore`)
- The validation uses the `id-validator` library for accurate Chinese ID card validation
- Age calculation accounts for whether the birthday has occurred in the current year
