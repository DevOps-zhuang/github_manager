"""Core validation functions for phone numbers and ID cards."""

from __future__ import annotations

import re
from datetime import datetime

from id_validator import validator


def is_valid_phone(phone: str) -> bool:
    """Validate Chinese mainland phone number.
    
    Args:
        phone: Phone number string to validate
        
    Returns:
        True if phone number is valid, False otherwise
    """
    if not phone:
        return False
    
    # Chinese mainland phone number pattern: starts with 1, second digit is 3-9, followed by 9 digits
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


def is_valid_id_card(id_card: str) -> bool:
    """Validate Chinese 18-digit ID card number with age verification.
    
    Uses id-validator library to check format, region code, birth date, and check digit.
    Additionally verifies that the person is at least 18 years old.
    
    Args:
        id_card: ID card number string to validate
        
    Returns:
        True if ID card is valid and holder is at least 18 years old, False otherwise
    """
    if not id_card:
        return False
    
    # First, validate using id-validator library
    try:
        if not validator.is_valid(id_card):
            return False
    except (ValueError, Exception):
        # Handle any validation errors from the library
        return False
    
    # Extract birth date from ID card
    # Format: XXXXXX YYYYMMDD XXXX
    # Positions 6-13 contain birth date (YYYYMMDD)
    try:
        birth_year = int(id_card[6:10])
        birth_month = int(id_card[10:12])
        birth_day = int(id_card[12:14])
        
        birth_date = datetime(birth_year, birth_month, birth_day)
        current_date = datetime.now()
        
        # Calculate age
        age = current_date.year - birth_date.year
        # Adjust if birthday hasn't occurred this year yet
        if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        # Check if age is at least 18
        return age >= 18
    except (ValueError, IndexError):
        return False
