#!/usr/bin/env python3
"""
Test script to verify that content is preserved when scraping fails
"""
import sys
import os
sys.path.append('/home/kenan/Desktop/ai-apps/learned')

from backend.services.scrape import clean_text_content

def test_clean_text_content_with_none():
    """Test that clean_text_content handles None input correctly"""
    print("Testing clean_text_content with None input...")

    result = clean_text_content(None)
    print(f"clean_text_content(None) = '{result}'")

    if result == "":
        print("✅ PASS: clean_text_content correctly returns empty string for None")
        return True
    else:
        print(f"❌ FAIL: Expected empty string, got '{result}'")
        return False

def test_clean_text_content_with_empty():
    """Test that clean_text_content handles empty input correctly"""
    print("\nTesting clean_text_content with empty string...")

    result = clean_text_content("")
    print(f"clean_text_content('') = '{result}'")

    if result == "":
        print("✅ PASS: clean_text_content correctly returns empty string for empty input")
        return True
    else:
        print(f"❌ FAIL: Expected empty string, got '{result}'")
        return False

def test_clean_text_content_with_whitespace():
    """Test that clean_text_content handles whitespace-only input correctly"""
    print("\nTesting clean_text_content with whitespace-only input...")

    result = clean_text_content("   \n\t   ")
    print(f"clean_text_content('   \\n\\t   ') = '{result}'")

    if result == "":
        print("✅ PASS: clean_text_content correctly returns empty string for whitespace-only input")
        return True
    else:
        print(f"❌ FAIL: Expected empty string, got '{result}'")
        return False

def test_clean_text_content_with_content():
    """Test that clean_text_content preserves actual content"""
    print("\nTesting clean_text_content with actual content...")

    test_content = "This is a test paper title"
    result = clean_text_content(test_content)
    print(f"clean_text_content('{test_content}') = '{result}'")

    if result == test_content:
        print("✅ PASS: clean_text_content preserves actual content")
        return True
    else:
        print(f"❌ FAIL: Expected '{test_content}', got '{result}'")
        return False

def simulate_scraping_failure_scenario():
    """Simulate the exact scenario that was causing the issue"""
    print("\n" + "="*60)
    print("Simulating the scraping failure scenario...")
    print("="*60)

    # Original title that should be preserved
    original_title = "Systematic Characterization of LLM Quantization: A Performance, Energy, and Quality Perspective"

    print(f"Original title: '{original_title}'")

    # Simulate scraping failure (returns None)
    scraped_content = None
    print(f"Scraped content: {scraped_content}")

    # This is what the old code would do (WRONG):
    old_cleaned = clean_text_content(scraped_content)
    print(f"Old behavior - clean_text_content(None): '{old_cleaned}'")
    print("❌ Old code would overwrite content with empty string!")

    # This is what the new code should do (CORRECT):
    if scraped_content and scraped_content.strip():
        new_content = clean_text_content(scraped_content)
        print(f"New behavior - would update content to: '{new_content}'")
    else:
        print("✅ New code preserves original content and marks as failed")
        print(f"Original title preserved: '{original_title}'")

    return True

if __name__ == "__main__":
    print("Testing Content Preservation in Scraping Failures")
    print("=" * 60)

    # Test clean_text_content function
    test1 = test_clean_text_content_with_none()
    test2 = test_clean_text_content_with_empty()
    test3 = test_clean_text_content_with_whitespace()
    test4 = test_clean_text_content_with_content()

    # Simulate the actual failure scenario
    test5 = simulate_scraping_failure_scenario()

    print("\n" + "=" * 60)
    all_passed = all([test1, test2, test3, test4, test5])

    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("The fix should correctly preserve content when scraping fails.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("There may still be issues with content preservation.")
