from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional, AsyncGenerator
from uuid import UUID
import asyncio
import json
import logging
from datetime import datetime

from backend.agents.langgraph_agent import process_with_langgraph_streaming, process_with_langgraph, get_chat_history
from backend.database import get_db, SessionLocal
from backend import crud
from backend.schemas import (
    ChatRequest, ChatResponse, ChatThreadResponse,
    ChatThreadWithMessages, ChatMessageResponse, ChatHistoryResponse
)
from sqlalchemy.orm import Session
from backend.models import ChatThread, ChatMessage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

async def create_or_get_thread(db: Session, thread_id: Optional[str], project_id: Optional[UUID]) -> ChatThread:
    """Create a new thread or get existing one"""
    if thread_id:
        try:
            thread_uuid = UUID(thread_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid thread ID format")
        thread = db.query(ChatThread).filter(ChatThread.id == thread_uuid).first()
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        return thread

    # Create new thread
    thread = ChatThread(
        title="New Chat",
        project_id=project_id
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread

async def save_message(db: Session, thread_id: UUID, role: str, content: str,
                      message_type: str = "text", **kwargs) -> ChatMessage:
    """Save a message to the database"""
    message = ChatMessage(
        thread_id=thread_id,
        role=role,
        content=content,
        message_type=message_type,
        **kwargs
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

async def generate_streaming_response(
    query: str,
    project_id: str,
    thread_id: str,
    video_ids: Optional[List[str]] = None
) -> AsyncGenerator[str, None]:
    """Generate streaming response from LangGraph agent"""
    db = None
    try:
        # Validate thread_id
        try:
            thread_uuid = UUID(thread_id)
        except ValueError:
            yield f"data: {json.dumps({'type': 'error', 'content': 'Invalid thread ID format'})}\n\n"
            return

        # Save user message first
        db = SessionLocal()
        await save_message(db, thread_uuid, "user", query)

        # Process with streaming
        async for chunk in process_with_langgraph_streaming(
            query=query,
            project_id=project_id,
            thread_id=thread_id,
            video_ids=video_ids,
            chat_llm_model="ollama", # TODO pass with request value
            query_generate_llm_model="ollama" # TODO pass with request value
        ):
            if isinstance(chunk, dict):
                # Handle different chunk types
                if chunk.get("type") == "text":
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk.get("type") == "sources":
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk.get("type") == "done":
                    # Save assistant message with full content
                    if chunk.get("content"):
                        await save_message(db, thread_uuid, "assistant", chunk["content"])
                    yield f"data: {json.dumps(chunk)}\n\n"
                    break
            else:
                # Raw text chunk
                yield f"data: {json.dumps({'type': 'text', 'content': str(chunk)})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    finally:
        # Ensure database session is properly closed
        if db:
            try:
                db.close()
            except Exception as close_error:
                logger.warning(f"Error closing database session: {close_error}")

@router.post("/stream", response_class=StreamingResponse)
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Stream chat responses using LangGraph agent with real-time updates.

    Features:
    - Real-time streaming responses
    - Chat history persistence
    - Thread management
    - RAG integration
    """
    try:
        # Validate project_id
        if not request.project_id or request.project_id.strip() == "":
            raise HTTPException(status_code=400, detail="Project ID is required and cannot be empty")

        try:
            project_id_uuid = UUID(request.project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project ID format")

        # Verify project exists
        project = crud.get_project(db, project_id_uuid)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Create or get thread
        thread = await create_or_get_thread(db, request.thread_id, project_id_uuid)

        # Convert video IDs to strings
        video_ids_str = [str(vid) for vid in request.video_ids] if request.video_ids else None

        return StreamingResponse(
            generate_streaming_response(
                query=request.message,
                project_id=str(request.project_id),
                thread_id=str(thread.id),
                video_ids=video_ids_str
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Process chat message without streaming (for compatibility).

    This endpoint processes the entire response before returning it.
    For real-time responses, use the /stream endpoint instead.
    """
    try:
        # Validate project_id
        if not request.project_id or request.project_id.strip() == "":
            raise HTTPException(status_code=400, detail="Project ID is required and cannot be empty")

        try:
            project_id_uuid = UUID(request.project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project ID format")

        # Verify project exists
        project = crud.get_project(db, project_id_uuid)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Create or get thread
        thread = await create_or_get_thread(db, request.thread_id, project_id_uuid)

        # Save user message
        await save_message(db, thread.id, "user", request.message)

        # Process query (non-streaming for now)
        result = await process_with_langgraph(
            query=request.message,
            project_id=str(request.project_id),
            thread_id=str(thread.id),
            video_ids=[str(vid) for vid in request.video_ids] if request.video_ids else None
        )


        await save_message(db, thread.id, "assistant", str(result["response"]))

        return ChatResponse(
            thread_id=str(thread.id),
            message=ChatMessageResponse(
                id=UUID(),  # This would be the actual message ID
                thread_id=thread.id,
                role="assistant",
                content=result.get("response", "Error processing request"),
                created_at=datetime.now().isoformat()
            ),
            sources=result.get("sources", [])
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@router.get("/threads/{thread_id}", response_model=ChatThreadWithMessages)
async def get_thread(
    thread_id: str,
    db: Session = Depends(get_db)
):
    """Get a chat thread with all its messages"""
    try:
        try:
            thread_uuid = UUID(thread_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid thread ID format")

        thread = db.query(ChatThread).filter(ChatThread.id == thread_uuid).first()
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

        return ChatThreadWithMessages.model_validate(thread)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving thread: {str(e)}")

@router.get("/threads", response_model=List[ChatThreadResponse])
async def list_threads(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all chat threads, optionally filtered by project"""
    try:
        query = db.query(ChatThread)
        if project_id:
            try:
                project_uuid = UUID(project_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid project ID format")
            query = query.filter(ChatThread.project_id == project_uuid)

        threads = query.order_by(ChatThread.updated_at.desc()).all()
        return [ChatThreadResponse.from_orm(thread) for thread in threads]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing threads: {str(e)}")


@router.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    db: Session = Depends(get_db)
):
    """Delete a chat thread and all its messages"""
    try:
        try:
            thread_uuid = UUID(thread_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid thread ID format")

        thread = db.query(ChatThread).filter(ChatThread.id == thread_uuid).first()
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

        # Delete all messages in the thread
        db.query(ChatMessage).filter(ChatMessage.thread_id == thread_uuid).delete()

        # Delete the thread
        db.delete(thread)
        db.commit()

        return {"success": True, "message": "Thread deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting thread: {str(e)}")


@router.get("/checkpoint/{thread_id}", response_model=ChatHistoryResponse)
async def get_chat_history_endpoint(thread_id: str, limit: Optional[int] = 50):
    """Get chat history for a specific thread from checkpoint postgresql db"""
    try:
        messages = await get_chat_history(thread_id, limit)
        
        return ChatHistoryResponse(
            thread_id=thread_id,
            messages=messages,
            total_count=len(messages)
        )
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))