#!/usr/bin/env python3
"""
Test script to verify the arxiv scraping fixes.
"""

import sys
import os
sys.path.append('backend')

from backend.services.scrape import scrape_arxiv_by_title
from backend.database import SessionLocal
from backend import crud, schemas, models
from uuid import uuid4

def test_arxiv_scraping():
    """Test the arxiv scraping functionality with the provided title."""

    title = "GRAPH-R1: TOWARDS AGENTIC GRAPHRAG FRAMEWORK VIA END-TO-END REINFORCEMENT LEARNING"

    print("Testing arxiv scraping with title:")
    print(f"'{title}'")
    print(f"Title length: {len(title)}")
    print(f"Title type: {type(title)}")
    print()

    # Test the public function
    print("Testing scrape_arxiv_by_title function...")
    try:
        result = scrape_arxiv_by_title(title)
        if result:
            print("✅ SUCCESS: Arxiv paper found and scraped!")
            print(f"Content length: {len(result)} characters")
            print(f"Content preview: {result[:200]}...")
        else:
            print("❌ FAILED: No content returned from arxiv scraping")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_empty_title_handling():
    """Test handling of empty titles."""

    print("\n" + "=" * 50)
    print("Testing empty title handling...")

    test_cases = [
        ("", "Empty string"),
        (None, "None value"),
        ("   ", "Whitespace only"),
        ("GRAPH-R1: TOWARDS AGENTIC GRAPHRAG FRAMEWORK VIA END-TO-END REINFORCEMENT LEARNING", "Valid title")
    ]

    for title, description in test_cases:
        print(f"\nTesting {description}: '{title}'")
        try:
            result = scrape_arxiv_by_title(title)
            if result:
                print("✅ SUCCESS: Content returned")
            else:
                print("ℹ️  No content (expected for invalid titles)")
        except Exception as e:
            print(f"❌ ERROR: {e}")

def test_database_operations():
    """Test database operations for knowledge items."""

    print("\n" + "=" * 50)
    print("Testing database operations...")

    db = SessionLocal()
    try:
        # Create a test project
        test_project = crud.create_project(db, schemas.ProjectCreate(
            name="Test Project",
            description="Test project for arxiv scraping"
        ))
        print(f"✅ Created test project: {test_project.id}")

        # Create a test video
        test_video = crud.create_video(db, schemas.VideoBase(
            youtube_id="test123",
            project_id=str(test_project.id),
            url="https://youtube.com/watch?v=test123",
            title="Test Video"
        ))
        print(f"✅ Created test video: {test_video.id}")

        # Test creating knowledge item with arxiv title
        title = "GRAPH-R1: TOWARDS AGENTIC GRAPHRAG FRAMEWORK VIA END-TO-END REINFORCEMENT LEARNING"
        knowledge_item = crud.create_knowledge_item(db, schemas.KnowledgeItemCreate(
            project_id=str(test_project.id),
            video_id=str(test_video.id),
            content=title,
            source_url="",
            source_type="arxiv-no-link",
            processing_status="pending"
        ))
        print(f"✅ Created knowledge item: {knowledge_item.id}")
        print(f"   Content: '{knowledge_item.content[:50]}...'")
        print(f"   Source type: {knowledge_item.source_type}")

        # Test duplicate prevention
        duplicate_item = crud.create_knowledge_item(db, schemas.KnowledgeItemCreate(
            project_id=str(test_project.id),
            video_id=str(test_video.id),
            content=title,
            source_url="",
            source_type="arxiv-no-link",
            processing_status="pending"
        ))
        print(f"✅ Created duplicate knowledge item: {duplicate_item.id}")

        # Check how many items exist
        items = crud.get_knowledge_items_by_video(db, str(test_video.id))
        print(f"📊 Total knowledge items for video: {len(items)}")

        db.commit()

    except Exception as e:
        print(f"❌ Database error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Arxiv Scraping Fix Test")
    print("=" * 50)

    test_arxiv_scraping()
    test_empty_title_handling()
    test_database_operations()

    print("\n" + "=" * 50)
    print("Test completed!")
