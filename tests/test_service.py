"""Unit tests for authentication service."""

from __future__ import annotations

import unittest
from pathlib import Path

from auth.service import validate_user


class TestValidationService(unittest.TestCase):
    """Test cases for validate_user function."""
    
    def test_valid_phone_only(self):
        """Test validation with valid phone and invalid ID card."""
        result = validate_user("13812345678", "")
        self.assertTrue(result)
    
    def test_valid_id_card_only(self):
        """Test validation with invalid phone and valid ID card."""
        result = validate_user("", "110101199003078515")
        self.assertTrue(result)
    
    def test_both_valid(self):
        """Test validation with both valid phone and ID card."""
        result = validate_user("13812345678", "110101199003078515")
        self.assertTrue(result)
    
    def test_both_invalid(self):
        """Test validation with both invalid phone and ID card."""
        result = validate_user("12345", "invalid")
        self.assertFalse(result)
        
        # Verify log file was created
        log_file = Path("logs/validation_failures.log")
        self.assertTrue(log_file.exists())
    
    def test_empty_inputs(self):
        """Test validation with empty inputs."""
        result = validate_user("", "")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
