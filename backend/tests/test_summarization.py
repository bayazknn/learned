import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from uuid import UUID

from backend.tasks.background import summarize_transcript_task
from backend import crud, models

def test_summarize_transcript_task_success():
    """Test successful transcript summarization"""
    # Create proper UUIDs
    video_id = "12345678-1234-5678-1234-567812345678"
    project_id = "87654321-4321-8765-4321-876543218765"
    
    # Mock database session
    mock_db = Mock(spec=Session)
    
    # Mock video object with proper attributes
    mock_video = Mock()
    mock_video.id = UUID(video_id)
    mock_video.project_id = UUID(project_id)
    mock_video.summary_processing_status = "pending"
    
    # Mock project with prompt context
    mock_project = Mock()
    mock_project.prompt_context = "Test project context about AI and machine learning"
    
    # Mock CRUD operations
    with patch('backend.tasks.background.crud.get_video', return_value=mock_video), \
         patch('backend.tasks.background.crud.get_project', return_value=mock_project), \
         patch('backend.tasks.background.init_chat_model') as mock_init_model, \
         patch('backend.tasks.background.SessionLocal', return_value=mock_db):
        
        # Mock Ollama response
        mock_response = Mock()
        mock_response.content = "This is a test summary of the transcript focusing on AI topics."
        mock_model = Mock()
        mock_model.invoke.return_value = mock_response
        mock_init_model.return_value = mock_model
        
        # Mock database operations
        with patch.object(mock_db, 'add'), \
             patch.object(mock_db, 'commit'), \
             patch.object(mock_db, 'refresh'):
            
            # Execute the task
            result = summarize_transcript_task(
                video_id,
                project_id,
                "Test transcript content about artificial intelligence and machine learning algorithms."
            )
            
            # Verify the result
            assert result['status'] == 'success'
            assert result['summary_generated'] == True
            assert result['summary_length'] > 0
            
            # Verify Ollama was called with the correct prompt
            mock_model.invoke.assert_called_once()
            call_args = mock_model.invoke.call_args[0][0]
            assert len(call_args) == 1
            assert isinstance(call_args[0].content, str)
            assert "Test project context" in call_args[0].content
            assert "Test transcript content" in call_args[0].content

def test_summarize_transcript_task_video_not_found():
    """Test transcript summarization when video is not found"""
    with patch('backend.tasks.background.crud.get_video', return_value=None), \
         patch('backend.tasks.background.SessionLocal', return_value=Mock(spec=Session)):
        result = summarize_transcript_task(
            "12345678-1234-5678-1234-567812345678",  # Valid UUID format
            "87654321-4321-8765-4321-876543218765",  # Valid UUID format
            "Test transcript content"
        )
        
        assert result['status'] == 'failed'
        assert "Video not found" in result['error']

def test_summarize_transcript_task_no_summary_generated():
    """Test transcript summarization when Ollama returns no summary"""
    video_id = "12345678-1234-5678-1234-567812345678"
    project_id = "87654321-4321-8765-4321-876543218765"
    
    mock_db = Mock(spec=Session)
    mock_video = Mock()
    mock_video.id = UUID(video_id)
    mock_video.project_id = UUID(project_id)
    mock_video.summary_processing_status = "pending"
    
    mock_project = Mock()
    mock_project.prompt_context = "Test project context"
    
    with patch('backend.tasks.background.crud.get_video', return_value=mock_video), \
         patch('backend.tasks.background.crud.get_project', return_value=mock_project), \
         patch('backend.tasks.background.init_chat_model') as mock_init_model, \
         patch('backend.tasks.background.SessionLocal', return_value=mock_db):
        
        # Mock Ollama response with empty content
        mock_response = Mock()
        mock_response.content = ""
        mock_model = Mock()
        mock_model.invoke.return_value = mock_response
        mock_init_model.return_value = mock_model
        
        with patch.object(mock_db, 'add'), \
             patch.object(mock_db, 'commit'), \
             patch.object(mock_db, 'refresh'):
            
            result = summarize_transcript_task(
                video_id,
                project_id,
                "Test transcript content"
            )
            
            assert result['status'] == 'failed'
            assert "No summary generated" in result['error']
            assert mock_video.summary_processing_status == "failed"

def test_summarize_transcript_task_exception_handling():
    """Test transcript summarization exception handling"""
    with patch('backend.tasks.background.crud.get_video', side_effect=Exception("Database error")), \
         patch('backend.tasks.background.SessionLocal', return_value=Mock(spec=Session)):
        result = summarize_transcript_task(
            "12345678-1234-5678-1234-567812345678",  # Valid UUID format
            "87654321-4321-8765-4321-876543218765",  # Valid UUID format
            "Test transcript content"
        )
        
        assert result['status'] == 'failed'
        assert "Error summarizing transcript" in result['error']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
