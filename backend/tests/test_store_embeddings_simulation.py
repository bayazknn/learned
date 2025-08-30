#!/usr/bin/env python3
"""
Test script to simulate store_embeddings_task function when it runs in process_video_task.
This test focuses on mocking dependencies and testing the integration between the two tasks.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
import sys
import os

# Add backend to path by going up two levels from tests directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.tasks.background import store_embeddings_task
from backend import crud, schemas
from backend.models import KnowledgeItem
from backend.database import Base, SessionLocal, engine


@pytest.fixture(scope="function")
def mock_db_session():
    """Create a mock database session"""
    with patch('backend.tasks.background.SessionLocal') as mock_session:
        mock_db = Mock(spec=Session)
        mock_session.return_value = mock_db
        yield mock_db


@pytest.fixture(scope="function")
def mock_rag_service():
    """Mock the RAG service"""
    with patch('backend.services.rag.store_embeddings_with_metadata') as mock_store:
        yield mock_store


@pytest.fixture(scope="function")
def mock_crud_operations():
    """Mock CRUD operations"""
    with patch('backend.tasks.background.crud') as mock_crud:
        yield mock_crud


def test_store_embeddings_task_success(mock_db_session, mock_rag_service, mock_crud_operations):
    """Test successful store_embeddings_task execution"""
    # Setup test data
    knowledge_item_id = str(uuid4())
    project_id = str(uuid4())
    content = "This is a test transcript content for embedding storage."
    source_url = "https://youtube.com/watch?v=test_video_123"
    video_id = str(uuid4())
    task_id = "test-task-123"
    
    # Mock the CRUD operations
    mock_knowledge_item = Mock(spec=KnowledgeItem)
    mock_crud_operations.get_knowledge_item.return_value = mock_knowledge_item
    mock_crud_operations.update_knowledge_item_status.return_value = mock_knowledge_item
    
    # Mock successful RAG storage
    mock_rag_service.return_value = True
    
    # Mock the task request context
    mock_request = Mock()
    mock_request.id = task_id
    
    # Execute the task by calling the underlying function directly
    # We need to access the actual function that would be executed by Celery
    result = store_embeddings_task.run(
        knowledge_item_id,
        project_id,
        content,
        source_url,
        video_id
    )
    
    # Verify the result
    assert result['status'] == 'success'
    assert result['knowledge_item_id'] == knowledge_item_id
    assert result['error'] is None
    
    # Verify CRUD operations were called correctly
    mock_crud_operations.update_knowledge_item_status.assert_any_call(
        mock_db_session, UUID(knowledge_item_id),
        processing_status="processing",
        task_id=None  # task_id is None when called directly without Celery context
    )
    
    mock_crud_operations.update_knowledge_item_status.assert_any_call(
        mock_db_session, UUID(knowledge_item_id),
        processing_status="completed",
        embedding_model="ollama"
    )
    
    # Verify RAG storage was called
    mock_rag_service.assert_called_once_with(
        project_id=project_id,
        text=content,
        source_url=source_url,
        video_id=video_id,
        embedding_model="ollama"
    )


def test_store_embeddings_task_rag_failure(mock_db_session, mock_rag_service, mock_crud_operations):
    """Test store_embeddings_task when RAG storage fails"""
    # Setup test data
    knowledge_item_id = str(uuid4())
    project_id = str(uuid4())
    content = "Test content for failed embedding storage."
    source_url = "https://youtube.com/watch?v=test_video_456"
    video_id = str(uuid4())
    task_id = "test-task-456"
    
    # Mock the CRUD operations
    mock_knowledge_item = Mock(spec=KnowledgeItem)
    mock_crud_operations.get_knowledge_item.return_value = mock_knowledge_item
    mock_crud_operations.update_knowledge_item_status.return_value = mock_knowledge_item
    
    # Mock failed RAG storage
    mock_rag_service.return_value = False
    
    # Mock the task request context
    mock_request = Mock()
    mock_request.id = task_id
    
    # Execute the task
    result = store_embeddings_task.run(
        knowledge_item_id,
        project_id,
        content,
        source_url,
        video_id
    )
    
    # Verify the result indicates failure
    assert result['status'] == 'failed'
    assert result['knowledge_item_id'] == knowledge_item_id
    assert result['error'] == "Failed to store embeddings in RAG"
    
    # Verify CRUD operations were called correctly
    mock_crud_operations.update_knowledge_item_status.assert_any_call(
        mock_db_session, UUID(knowledge_item_id),
        processing_status="processing",
        task_id=None  # task_id is None when called directly without Celery context
    )
    
    mock_crud_operations.update_knowledge_item_status.assert_any_call(
        mock_db_session, UUID(knowledge_item_id),
        processing_status="failed",
        embedding_model="ollama"
    )


def test_store_embeddings_task_exception_handling(mock_db_session, mock_rag_service, mock_crud_operations):
    """Test store_embeddings_task exception handling"""
    # Setup test data
    knowledge_item_id = str(uuid4())
    project_id = str(uuid4())
    content = "Test content that causes exception."
    source_url = "https://youtube.com/watch?v=test_video_789"
    video_id = str(uuid4())
    task_id = "test-task-789"
    
    # Mock the CRUD operations to raise an exception
    mock_crud_operations.update_knowledge_item_status.side_effect = Exception("Database error")
    
    # Mock the task request context
    mock_request = Mock()
    mock_request.id = task_id
    
    # Execute the task
    result = store_embeddings_task.run(
        knowledge_item_id,
        project_id,
        content,
        source_url,
        video_id
    )
    
    # Verify the result indicates failure with error message
    assert result['status'] == 'failed'
    assert result['knowledge_item_id'] == knowledge_item_id
    assert "Database error" in result['error']
    
    # Verify rollback was called
    mock_db_session.rollback.assert_called_once()


def test_store_embeddings_task_without_video_id(mock_db_session, mock_rag_service, mock_crud_operations):
    """Test store_embeddings_task without video_id parameter"""
    # Setup test data (no video_id)
    knowledge_item_id = str(uuid4())
    project_id = str(uuid4())
    content = "Test content without video ID."
    source_url = "https://youtube.com/watch?v=test_video_novid"
    task_id = "test-task-novid"
    
    # Mock the CRUD operations
    mock_knowledge_item = Mock(spec=KnowledgeItem)
    mock_crud_operations.get_knowledge_item.return_value = mock_knowledge_item
    mock_crud_operations.update_knowledge_item_status.return_value = mock_knowledge_item
    
    # Mock successful RAG storage
    mock_rag_service.return_value = True
    
    # Mock the task request context
    mock_request = Mock()
    mock_request.id = task_id
    
    # Execute the task without video_id
    result = store_embeddings_task.run(
        knowledge_item_id,
        project_id,
        content,
        source_url
        # video_id parameter omitted
    )
    
    # Verify the result
    assert result['status'] == 'success'
    
    # Verify RAG storage was called without video_id
    mock_rag_service.assert_called_once_with(
        project_id=project_id,
        text=content,
        source_url=source_url,
        video_id=None,  # Should be None when not provided
        embedding_model="ollama"
    )


def test_store_embeddings_task_cleanup_on_error(mock_db_session, mock_rag_service, mock_crud_operations):
    """Test that cleanup operations are performed even when main logic fails"""
    # Setup test data
    knowledge_item_id = str(uuid4())
    project_id = str(uuid4())
    content = "Test content for cleanup test."
    source_url = "https://youtube.com/watch?v=test_video_cleanup"
    video_id = str(uuid4())
    task_id = "test-task-cleanup"
    
    # Mock the CRUD operations to raise an exception during main processing
    def mock_update_status(*args, **kwargs):
        if kwargs.get('processing_status') == 'processing':
            return Mock()  # First call succeeds
        else:
            raise Exception("Status update failed")
    
    mock_crud_operations.update_knowledge_item_status.side_effect = mock_update_status
    
    # Mock the task request context
    mock_request = Mock()
    mock_request.id = task_id
    
    # Execute the task
    result = store_embeddings_task.run(
        knowledge_item_id,
        project_id,
        content,
        source_url,
        video_id
    )
    
    # Verify the result indicates failure
    assert result['status'] == 'failed'
    assert "Status update failed" in result['error']
    
    # Verify rollback was called
    mock_db_session.rollback.assert_called_once()


def test_simulation_with_process_video_integration(mock_db_session, mock_rag_service, mock_crud_operations):
    """
    Simulate the complete flow from process_video_task to store_embeddings_task
    This test shows how the two tasks work together
    """
    # Setup test data that would come from process_video_task
    knowledge_item_id = str(uuid4())
    project_id = str(uuid4())
    transcript_content = """
    This is a simulated transcript from a YouTube video.
    It contains multiple sentences that will be embedded.
    The store_embeddings_task should process this content.
    """
    video_url = "https://youtube.com/watch?v=integration_test"
    video_id = str(uuid4())
    task_id = "integration-task-123"
    
    # Mock the CRUD operations
    mock_knowledge_item = Mock(spec=KnowledgeItem)
    mock_knowledge_item.content = transcript_content
    mock_knowledge_item.video_id = UUID(video_id)
    mock_crud_operations.get_knowledge_item.return_value = mock_knowledge_item
    mock_crud_operations.update_knowledge_item_status.return_value = mock_knowledge_item
    
    # Mock successful RAG storage
    mock_rag_service.return_value = True
    
    # Mock the task request context (as would be provided by Celery)
    mock_request = Mock()
    mock_request.id = task_id
    
    # Simulate the store_embeddings_task call that process_video_task would make
    result = store_embeddings_task.run(
        knowledge_item_id,
        project_id,
        transcript_content,
        video_url,
        video_id
    )
    
    # Verify successful processing
    assert result['status'] == 'success'
    assert result['knowledge_item_id'] == knowledge_item_id
    
    # Verify the content was processed correctly
    mock_rag_service.assert_called_once_with(
        project_id=project_id,
        text=transcript_content,
        source_url=video_url,
        video_id=video_id,
        embedding_model="ollama"
    )
    
    # Verify status updates were made
    assert mock_crud_operations.update_knowledge_item_status.call_count == 2
    

if __name__ == "__main__":
    # Run the tests directly for demonstration
    print("Running store_embeddings_task simulation tests...")
    
    # Create a simple test runner
    test_functions = [
        test_store_embeddings_task_success,
        test_store_embeddings_task_rag_failure,
        test_store_embeddings_task_exception_handling,
        test_store_embeddings_task_without_video_id,
        test_store_embeddings_task_cleanup_on_error,
        test_simulation_with_process_video_integration
    ]
    
    for test_func in test_functions:
        try:
            # Create fresh mocks for each test
            with patch('backend.tasks.background.SessionLocal') as mock_session, \
                 patch('backend.services.rag.store_embeddings_with_metadata') as mock_rag, \
                 patch('backend.tasks.background.crud') as mock_crud:
                
                mock_db = Mock()
                mock_session.return_value = mock_db
                
                # Run the test
                test_func(mock_db, mock_rag, mock_crud)
                print(f"✓ {test_func.__name__} passed")
                
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
    
    print("\nAll simulation tests completed!")
