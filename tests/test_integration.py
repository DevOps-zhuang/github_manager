"""Integration test demonstrating the complete validation workflow."""

from __future__ import annotations

import unittest
from pathlib import Path

from auth.service import validate_user
from auth.validators import is_valid_id_card, is_valid_phone


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete validation workflow."""
    
    def test_complete_validation_workflow(self):
        """Test the complete validation workflow from validators to service."""
        # Test case 1: User with valid phone and valid ID card
        phone1 = "13812345678"
        id_card1 = "110101199003078515"
        
        # Individual validators should pass
        self.assertTrue(is_valid_phone(phone1))
        self.assertTrue(is_valid_id_card(id_card1))
        
        # Service validation should pass
        self.assertTrue(validate_user(phone1, id_card1))
        
        # Test case 2: User with invalid phone but valid ID card
        phone2 = "12345"
        id_card2 = "110101199003078515"
        
        self.assertFalse(is_valid_phone(phone2))
        self.assertTrue(is_valid_id_card(id_card2))
        
        # Service should still pass (OR logic)
        self.assertTrue(validate_user(phone2, id_card2))
        
        # Test case 3: User with valid phone but invalid ID card
        phone3 = "13812345678"
        id_card3 = "invalid"
        
        self.assertTrue(is_valid_phone(phone3))
        self.assertFalse(is_valid_id_card(id_card3))
        
        # Service should still pass (OR logic)
        self.assertTrue(validate_user(phone3, id_card3))
        
        # Test case 4: User with both invalid
        phone4 = "invalid"
        id_card4 = "invalid"
        
        self.assertFalse(is_valid_phone(phone4))
        self.assertFalse(is_valid_id_card(id_card4))
        
        # Service should fail and log
        self.assertFalse(validate_user(phone4, id_card4))
    
    def test_logging_functionality(self):
        """Verify that logging works correctly for failed validations."""
        log_file = Path("logs/validation_failures.log")
        
        # Ensure log directory exists
        log_file.parent.mkdir(exist_ok=True)
        
        # Get initial log size
        initial_size = log_file.stat().st_size if log_file.exists() else 0
        
        # Trigger a validation failure
        validate_user("invalid_phone", "invalid_id")
        
        # Verify log file was written to
        self.assertTrue(log_file.exists())
        new_size = log_file.stat().st_size
        self.assertGreater(new_size, initial_size)
        
        # Verify log content
        with log_file.open("r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Validation failed", content)
            self.assertIn("invalid_phone", content)
            self.assertIn("invalid_id", content)
    
    def test_edge_cases(self):
        """Test various edge cases that might occur in production."""
        # Empty strings
        self.assertFalse(validate_user("", ""))
        
        # None values (should be handled gracefully)
        self.assertFalse(validate_user(None, None))
        
        # Whitespace
        self.assertFalse(validate_user("   ", "   "))
        
        # Very long strings
        long_phone = "1" * 100
        long_id = "1" * 100
        self.assertFalse(validate_user(long_phone, long_id))
    
    def test_real_world_scenarios(self):
        """Test realistic scenarios that might occur in production."""
        # Scenario 1: New user registration with both credentials
        new_user_phone = "13912345678"
        new_user_id = "110101199003078515"
        self.assertTrue(validate_user(new_user_phone, new_user_id))
        
        # Scenario 2: User only provides phone (e.g., quick signup)
        quick_signup_phone = "15812345678"
        self.assertTrue(validate_user(quick_signup_phone, ""))
        
        # Scenario 3: User only provides ID card (e.g., government verification)
        gov_verify_id = "110101199003078515"
        self.assertTrue(validate_user("", gov_verify_id))
        
        # Scenario 4: Typo in phone number
        typo_phone = "1381234567"  # Missing one digit
        valid_id = "110101199003078515"
        # Should still pass because ID is valid
        self.assertTrue(validate_user(typo_phone, valid_id))
        
        # Scenario 5: Typo in ID card
        valid_phone = "13812345678"
        typo_id = "110101199003078516"  # Wrong check digit
        # Should still pass because phone is valid
        self.assertTrue(validate_user(valid_phone, typo_id))
        
        # Scenario 6: Both credentials have typos (validation fails)
        self.assertFalse(validate_user(typo_phone, typo_id))


if __name__ == "__main__":
    unittest.main()
