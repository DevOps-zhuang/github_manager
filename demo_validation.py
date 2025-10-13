"""Demonstration script for user validation module.

This script demonstrates how to use the user validation module.
"""

from auth.service import validate_user
from auth.validators import is_valid_id_card, is_valid_phone


def main():
    """Demonstrate user validation functionality."""
    print("=" * 60)
    print("User Identity Validation Module - Demo")
    print("=" * 60)
    print()
    
    # Test cases
    test_cases = [
        ("13812345678", "110101199003078515", "Valid phone and valid ID card"),
        ("13812345678", "", "Valid phone only"),
        ("", "110101199003078515", "Valid ID card only"),
        ("12345", "invalid", "Both invalid"),
        ("", "", "Both empty"),
    ]
    
    print("Testing validate_user function:")
    print("-" * 60)
    
    for phone, id_card, description in test_cases:
        result = validate_user(phone, id_card)
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} | {description}")
        print(f"     Phone: {phone or '(empty)'}")
        print(f"     ID Card: {id_card or '(empty)'}")
        print()
    
    print("-" * 60)
    print("\nTesting individual validators:")
    print("-" * 60)
    
    # Test phone validator
    print("\nPhone Number Validation:")
    phones = ["13812345678", "12012345678", "138123456"]
    for phone in phones:
        result = is_valid_phone(phone)
        status = "✓" if result else "✗"
        print(f"{status} {phone}: {'Valid' if result else 'Invalid'}")
    
    # Test ID card validator
    print("\nID Card Validation:")
    id_cards = [
        "110101199003078515",  # Valid, over 18
        "110101199003078516",  # Invalid checksum
        "11010119900307",      # Too short
    ]
    for id_card in id_cards:
        result = is_valid_id_card(id_card)
        status = "✓" if result else "✗"
        print(f"{status} {id_card}: {'Valid' if result else 'Invalid'}")
    
    print()
    print("=" * 60)
    print("Demo complete. Check logs/validation_failures.log for failure logs.")
    print("=" * 60)


if __name__ == "__main__":
    main()
