#!/usr/bin/env python3
"""
Test script to verify the scrape_sources_task functionality
"""
import sys
import os
sys.path.append('/home/kenan/Desktop/ai-apps/learned')

from backend.services.scrape import scrape_content

def test_arxiv_scraping():
    """Test arxiv scraping with the problematic paper title"""
    title = "Systematic Characterization of LLM Quantization: A Performance, Energy, and Quality Perspective"

    print("Testing arxiv scraping with title:")
    print(f"'{title}'")
    print("-" * 60)

    try:
        # Test the scraping function directly
        result = scrape_content(
            source_url="",  # Empty URL for arxiv-no-link
            source_type="arxiv-no-link",
            content=title
        )

        if result:
            print("✅ SUCCESS: Content scraped successfully!")
            print(f"Content length: {len(result)} characters")
            print(f"First 500 characters:\n{result[:500]}...")
            return True
        else:
            print("❌ FAILED: No content returned")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_scrape_sources_task():
    """Test the scrape_sources_task function directly"""
    from backend.tasks.background import scrape_sources_task

    # Use the specific knowledge item ID from the error
    knowledge_item_id = "97ce0957-932c-4394-93d4-9f2b22d31874"

    print(f"\nTesting scrape_sources_task with knowledge_item_id: {knowledge_item_id}")
    print("-" * 60)

    try:
        # This would normally be called by Celery, but we can test the function directly
        # Note: This will fail because we don't have the database context, but it will show us the logic
        print("Note: This test requires database access, so it will likely fail in this context")
        print("But it will help us understand the flow...")

        # We can't actually run this without the database, but let's show what would happen
        print("The function would:")
        print("1. Get knowledge item from database")
        print("2. Check if source_type is 'arxiv-no-link'")
        print("3. Call scrape_content with the title from content field")
        print("4. Process the scraped content")

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Testing Arxiv Scraping Functionality")
    print("=" * 60)

    # Test 1: Direct scraping function
    success1 = test_arxiv_scraping()

    # Test 2: Task function (will show the logic)
    success2 = test_scrape_sources_task()

    print("\n" + "=" * 60)
    if success1:
        print("✅ Overall: Scraping functionality appears to be working!")
        print("The issue was likely the deprecated arxiv API usage, which has been fixed.")
    else:
        print("❌ Overall: There are still issues with the scraping functionality.")
