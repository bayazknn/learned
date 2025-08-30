# RAG Storage Implementation in Background Tasks

This document describes the implementation of RAG (Retrieval Augmented Generation) storage in background tasks for the YouTube+AI Research Application.

## Overview

The implementation adds proper RAG storage functionality with status tracking to the existing video processing pipeline. When a YouTube video is processed, its transcript is now automatically stored in the Qdrant vector database with comprehensive status tracking.

## Key Changes Made

### 1. Database Model Updates (`backend/models.py`)

Added new fields to the `KnowledgeItem` model:
- `processing_status`: Tracks the RAG processing state (`pending`, `processing`, `completed`, `failed`)
- `embedding_model`: Records which embedding model was used (`ollama`, `gemini`)
- `task_id`: Stores the Celery task ID for tracking
- `processed_at`: Timestamp when processing completed

### 2. Schema Updates (`backend/schemas.py`)

Updated Pydantic schemas to include the new fields in both create and response models:
- `KnowledgeItemCreate`: Added optional fields for status tracking
- `KnowledgeItemResponse`: Added all new fields for API responses

### 3. CRUD Operations (`backend/crud.py`)

Added new function:
- `update_knowledge_item_status()`: Updates processing status and related fields

Enhanced existing function:
- `create_knowledge_item()`: Now accepts and stores the new status fields

### 4. Background Tasks (`backend/tasks/background.py`)

#### New Task: `store_embeddings_task`
- Takes `knowledge_item_id` as input for status tracking
- Uses default Ollama embedding model
- Updates KnowledgeItem status throughout processing:
  - `processing` when task starts
  - `completed` on success
  - `failed` on error
- Stores task ID and embedding model information

#### Enhanced Task: `process_video_task`
- Creates KnowledgeItem with `pending` status initially
- Triggers `store_embeddings_task` asynchronously after successful transcript extraction
- Returns `knowledge_item_id` in result for tracking

### 5. Database Migration

Created and applied Alembic migration (`2754e0bbad53_add_knowledge_item_status_fields.py`) to add the new columns to the `knowledge_items` table.

## Workflow

1. **Video Processing**: `process_video_task` extracts transcript and creates KnowledgeItem with `pending` status
2. **RAG Storage Trigger**: Task triggers `store_embeddings_task` asynchronously
3. **Status Updates**: 
   - `store_embeddings_task` updates status to `processing` when starting
   - Uses Ollama embeddings to store in Qdrant
   - Updates status to `completed` on success or `failed` on error
4. **Tracking**: All status changes, task IDs, and embedding models are recorded

## Configuration

### Default Embedding Model
The system uses Ollama as the default embedding model (`embedding_model="ollama"`). This can be easily modified in the `store_embeddings_task` function.

### Task Queues
RAG storage tasks are queued in the `rag_processing` queue for potential separate worker processing.

## Error Handling

- Comprehensive error handling in both tasks
- Status properly set to `failed` on errors
- Database transactions rolled back on failures
- Logging of all processing steps and errors

## Testing

A test script `test_rag_storage.py` is provided to verify the complete workflow:
- Video processing with transcript extraction
- KnowledgeItem creation with proper status
- RAG storage execution
- Status tracking verification

## Usage

The system automatically handles RAG storage when videos are processed through the existing API endpoints. No additional API changes are required.

## Monitoring

KnowledgeItem processing status can be monitored through:
- Database queries on the `knowledge_items` table
- Celery task monitoring using the stored `task_id`
- API endpoints that return KnowledgeItem information

## Future Enhancements

- Additional API endpoints for RAG status checking
- Retry mechanisms for failed RAG storage
- Support for multiple embedding model selection
- Batch processing optimizations
