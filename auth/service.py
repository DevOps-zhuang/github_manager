"""Validation service with logging for failed validation attempts."""

from __future__ import annotations

import logging
from pathlib import Path

from auth.validators import is_valid_id_card, is_valid_phone

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure file handler
log_file = log_dir / "validation_failures.log"
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.INFO)

# Set format: timestamp, log level, message
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)


def validate_user(phone: str, id_card: str) -> bool:
    """Validate user identity using phone number and ID card.
    
    If either phone or ID card validation passes, the user is considered valid.
    If both validations fail, logs the failure details to validation_failures.log.
    
    Args:
        phone: Phone number to validate
        id_card: ID card number to validate
        
    Returns:
        True if at least one validation passes, False if both fail
    """
    phone_valid = is_valid_phone(phone)
    id_card_valid = is_valid_id_card(id_card)
    
    # If either validation passes, return True
    if phone_valid or id_card_valid:
        return True
    
    # Both validations failed - construct failure message
    failure_reasons = []
    if not phone_valid:
        failure_reasons.append("invalid phone number")
    if not id_card_valid:
        failure_reasons.append("invalid ID card")
    
    failure_message = f"Validation failed: phone={phone}, id_card={id_card}, reasons=[{', '.join(failure_reasons)}]"
    
    # Log the failure
    logger.info(failure_message)
    
    return False
