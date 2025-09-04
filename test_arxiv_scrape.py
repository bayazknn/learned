#!/usr/bin/env python3
"""
Test script for the _scrape_arxiv_by_title method
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.scrape import scraping_service

def test_scrape_arxiv_by_title():
    """Test the _scrape_arxiv_by_title method with the specified title"""

    title = "AHELM: A Holistic Evaluation of Audio-Language Models"

    print(f"Testing _scrape_arxiv_by_title with title: '{title}'")
    print("=" * 60)

    try:
        print("Testing the improved scraping method...")
        result = scraping_service._scrape_arxiv_by_title(title)

        if result:
            print("✅ Scraping successful!")
            print(f"Content length: {len(result)} characters")

            # Extract and display paper metadata from the content
            lines = result.split('\n')[:10]  # First 10 lines usually contain title and authors
            print("\nPaper information from content:")
            print("-" * 40)
            for line in lines:
                if line.strip():
                    print(line.strip())
                    if len([l for l in lines if l.strip()]) >= 3:  # Show first few meaningful lines
                        break
            print("-" * 40)

            print("\nFirst 500 characters of content:")
            print("-" * 40)
            print(result[:500])
            print("-" * 40)
            if len(result) > 500:
                print(f"... (truncated, total length: {len(result)})")

            # Check if we got the correct paper
            if "AHELM" in result.upper() and "Audio-Language" in result:
                print("\n✅ SUCCESS: Found the correct AHELM paper!")
            else:
                print("\n❌ WARNING: Content doesn't appear to be the AHELM paper")

        else:
            print("❌ Scraping failed or returned None")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scrape_arxiv_by_title()
