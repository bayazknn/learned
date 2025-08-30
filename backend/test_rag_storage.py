#!/usr/bin/env python3
"""
Test script to verify RAG storage functionality in background tasks.
This script tests the integration between process_video_task and store_embeddings_task.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.tasks.background import process_video_task, store_embeddings_task
from backend.database import SessionLocal
from backend import crud
from uuid import UUID
import time

def test_rag_storage_workflow():
    """Test the complete RAG storage workflow"""
    print("Testing RAG storage workflow...")
    
    # Test with a sample YouTube video URL
    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Sample URL
    test_project_id = "3cdb9bf8-3caf-4492-85b6-da3d6c10c370"  # Use existing project ID from qdrant storage
    
    print(f"Testing with video URL: {test_video_url}")
    print(f"Project ID: {test_project_id}")
    
    # Test process_video_task
    print("\n1. Testing process_video_task...")
    try:
        result = process_video_task(test_video_url, test_project_id)
        print(f"Process video result: {result}")
        
        if result['status'] in ['success', 'partial_success'] and result.get('knowledge_item_id'):
            knowledge_item_id = result['knowledge_item_id']
            print(f"✓ Knowledge item created: {knowledge_item_id}")
            
            # Verify knowledge item was created with pending status
            db = SessionLocal()
            try:
                knowledge_item = crud.get_knowledge_item(db, UUID(knowledge_item_id))
                if knowledge_item:
                    print(f"✓ Knowledge item found in database")
                    print(f"  - Status: {knowledge_item.processing_status}")
                    print(f"  - Content length: {len(knowledge_item.content) if knowledge_item.content else 0}")
                    
                    # Test store_embeddings_task
                    print("\n2. Testing store_embeddings_task...")
                    rag_result = store_embeddings_task(
                        knowledge_item_id=knowledge_item_id,
                        project_id=test_project_id,
                        content=knowledge_item.content,
                        source_url=test_video_url,
                        video_id=str(knowledge_item.video_id) if knowledge_item.video_id else None
                    )
                    
                    print(f"RAG storage result: {rag_result}")
                    
                    # Verify knowledge item status was updated
                    updated_item = crud.get_knowledge_item(db, UUID(knowledge_item_id))
                    if updated_item:
                        print(f"✓ Knowledge item status updated: {updated_item.processing_status}")
                        print(f"  - Embedding model: {updated_item.embedding_model}")
                        print(f"  - Processed at: {updated_item.processed_at}")
                        
                        if updated_item.processing_status == "completed":
                            print("✓ RAG storage completed successfully!")
                        else:
                            print("⚠ RAG storage may have failed or is still processing")
                    else:
                        print("✗ Failed to retrieve updated knowledge item")
                        
                else:
                    print("✗ Knowledge item not found in database")
                    
            except Exception as e:
                print(f"✗ Error testing RAG storage: {e}")
            finally:
                db.close()
        else:
            print("✗ Process video task did not create knowledge item successfully")
            
    except Exception as e:
        print(f"✗ Error testing process_video_task: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_rag_storage_workflow()
