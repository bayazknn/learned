#!/usr/bin/env python3
"""
Test script to specifically test arxiv-no-link scraping with the provided content
"""
import sys
import os
sys.path.append('/home/kenan/Desktop/ai-apps/learned')

from backend.services.scrape import scrape_content

def test_specific_arxiv_content():
    """Test the specific arxiv content provided by the user"""
    content = "GRAPH-R1: TOWARDS AGENTIC GRAPHRAG FRAMEWORK VIA END-TO-END REINFORCEMENT LEARNING"

    print("Testing arxiv-no-link scraping with specific content:")
    print(f"'{content}'")
    print("-" * 80)

    try:
        # Test the scraping function directly
        result = scrape_content(
            source_url="",  # Empty URL for arxiv-no-link
            source_type="arxiv-no-link",
            content=content
        )

        if result:
            print("✅ SUCCESS: Content scraped successfully!")
            print(f"Content length: {len(result)} characters")
            print(f"First 500 characters:\n{result[:500]}...")

            # Check if the result contains expected academic content
            if "abstract" in result.lower() or "introduction" in result.lower():
                print("✅ SUCCESS: Result appears to contain academic paper content")
            else:
                print("⚠️  WARNING: Result may not contain expected academic content")

            return True
        else:
            print("❌ FAILED: No content returned from scraping")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test various edge cases for arxiv-no-link scraping"""
    test_cases = [
        ("", "Empty content"),
        ("   ", "Whitespace only"),
        ("A", "Single character"),
        ("GRAPH-R1: TOWARDS AGENTIC GRAPHRAG FRAMEWORK VIA END-TO-END REINFORCEMENT LEARNING", "Original test case"),
        ("Some random title that doesn't exist on arxiv", "Non-existent paper"),
        ("Quantum Computing: A Gentle Introduction", "Generic academic title"),
    ]

    print("\n" + "="*80)
    print("Testing edge cases for arxiv-no-link scraping:")
    print("="*80)

    results = []
    for test_content, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"Content: '{test_content}'")

        try:
            result = scrape_content(
                source_url="",
                source_type="arxiv-no-link",
                content=test_content
            )

            if result:
                print(f"✅ Result: {len(result)} characters")
                results.append(True)
            else:
                print("❌ No result")
                results.append(False)

        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(False)

    success_count = sum(results)
    total_count = len(results)
    print(f"\nEdge case results: {success_count}/{total_count} successful")

    return success_count > 0  # At least one should work

if __name__ == "__main__":
    print("Testing Arxiv-no-link Scraping with Specific Content")
    print("=" * 80)

    # Test the specific content provided
    success1 = test_specific_arxiv_content()

    # Test edge cases
    success2 = test_edge_cases()

    print("\n" + "=" * 80)
    if success1:
        print("✅ OVERALL SUCCESS: The specific arxiv content scraping works!")
        print("The fix should handle this case correctly.")
    else:
        print("❌ OVERALL FAILURE: Issues with arxiv content scraping.")

    if success2:
        print("✅ Edge case testing completed.")
    else:
        print("❌ All edge cases failed - there may be broader issues.")
