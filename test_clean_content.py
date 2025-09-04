#!/usr/bin/env python3
"""
Test script to verify the clean_text_content function works correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.scrape import clean_text_content

def test_clean_text_content():
    """Test the clean_text_content function with various inputs"""

    # Test with null characters
    text_with_nulls = "Hello\x00World\x00Test"
    cleaned = clean_text_content(text_with_nulls)
    print(f"Original: {repr(text_with_nulls)}")
    print(f"Cleaned: {repr(cleaned)}")
    assert '\x00' not in cleaned, "Null characters should be removed"
    assert cleaned == "HelloWorldTest", f"Expected 'HelloWorldTest', got '{cleaned}'"

    # Test with control characters
    text_with_controls = "Hello\x01\x02World\x03Test"
    cleaned = clean_text_content(text_with_controls)
    print(f"Original: {repr(text_with_controls)}")
    print(f"Cleaned: {repr(cleaned)}")
    assert cleaned == "HelloWorldTest", f"Expected 'HelloWorldTest', got '{cleaned}'"

    # Test with normal text (should remain unchanged)
    normal_text = "This is normal text with spaces and punctuation!"
    cleaned = clean_text_content(normal_text)
    print(f"Original: {repr(normal_text)}")
    print(f"Cleaned: {repr(cleaned)}")
    assert cleaned == normal_text, "Normal text should remain unchanged"

    # Test with empty string
    empty_text = ""
    cleaned = clean_text_content(empty_text)
    print(f"Original: {repr(empty_text)}")
    print(f"Cleaned: {repr(cleaned)}")
    assert cleaned == "", "Empty string should remain empty"

    # Test with None
    none_text = None
    cleaned = clean_text_content(none_text)
    print(f"Original: {none_text}")
    print(f"Cleaned: {repr(cleaned)}")
    assert cleaned == "", "None should return empty string"

    print("All tests passed!")

if __name__ == "__main__":
    test_clean_text_content()
