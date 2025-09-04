from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
import humps


# Video Source Schema (for frontend compatibility)
class VideoSource(BaseModel):
    id: UUID
    source_url: str
    source_type: str  # e.g., 'pdf', 'web', 'article', 'transcript'
    content: str  # Content preview or full content

    model_config = ConfigDict(
        alias_generator=humps.camelize,
        populate_by_name=True,
        from_attributes=True,
    )

# Video Schemas
class VideoCreate(BaseModel):
    url: str  # YouTube video ID
    project_id: str

    model_config = ConfigDict(
        alias_generator=humps.camelize,  # Converts snake_case to camelCase for output
        populate_by_name=True,  # Allows both snake_case and camelCase for input
    )



class VideoBase(BaseModel):
    youtube_id: str
    title: str
    url: str
    description: Optional[str] = None
    project_id: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=humps.camelize,  # Converts snake_case to camelCase for output
        populate_by_name=True,  # Allows both snake_case and camelCase for input
    )

class VideoResponse(VideoBase):
    id: UUID
    youtube_id: str
    title: str
    url: str
    description: Optional[str] = None
    transcript: Optional[str] = None
    project_id: Optional[UUID] = None
    duration: Optional[int] = None  # Duration in seconds
    upload_date: Optional[str] = None  # YYYYMMDD format
    views: Optional[int] = None  # View count
    thumbnail_url: Optional[str] = None  # Thumbnail URL
    channel: Optional[str] = None  # YouTube channel name
    channel_id: Optional[str] = None  # YouTube channel ID
    processing_status: Optional[str] = "pending"  # pending, processing, completed, failed
    processed_at: Optional[str] = None  # ISO format timestamp when processing completed
    summary: Optional[str] = None  # AI-generated summary of the transcript
    summary_processing_status: Optional[str] = "pending"  # pending, processing, completed, failed for summary generation
    summary_processed_at: Optional[str] = None  # ISO format timestamp when summary processing completed
    sources: List[VideoSource] = []  # Knowledge items as sources for frontend
    
    model_config = ConfigDict(
        from_attributes = True
    )


# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    prompt_context: Optional[str] = None


    model_config = ConfigDict(
        alias_generator=humps.camelize,  # Converts snake_case to camelCase for output
        populate_by_name=True,  # Allows both snake_case and camelCase for input
    )

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    id : UUID
    created_at: Optional[str] = None  # ISO format timestamp

class ProjectResponse(ProjectBase):
    id: UUID
    created_at: Optional[str] = None  # ISO format timestamp
    video_count: Optional[int] = 0  # Computed field for number of videos
    
    model_config = ConfigDict(
        from_attributes = True
    )


# KnowledgeItem Schemas
class KnowledgeItemBase(BaseModel):
    content: str
    source_url: str
    source_type: str  # e.g., 'video', 'scraped'

    model_config = ConfigDict(
        alias_generator=humps.camelize,  # Converts snake_case to camelCase for output
        populate_by_name=True, 
        from_attributes=True,
    )

class KnowledgeItemCreate(KnowledgeItemBase):
    project_id: UUID
    video_id: Optional[str] = None
    processing_status: Optional[str] = "pending"  # pending, processing, completed, failed
    embedding_model: Optional[str] = None  # e.g., 'ollama', 'gemini'
    task_id: Optional[str] = None  # Celery task ID for tracking

class KnowledgeItemResponse(KnowledgeItemBase):
    id: UUID
    project_id: UUID
    processing_status: Optional[str] = "pending"  # pending, processing, completed, failed
    embedding_model: Optional[str] = None  # e.g., 'ollama', 'gemini'
    task_id: Optional[str] = None  # Celery task ID for tracking
    processed_at: Optional[str] = None  # ISO format timestamp when processing completed


# Chat Schemas
class ChatMessageBase(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str
    message_type: Optional[str] = "text"  # 'text', 'file', 'tool_call', 'tool_result'
    file_url: Optional[str] = None  # For file uploads
    file_name: Optional[str] = None  # For file uploads
    file_type: Optional[str] = None  # MIME type for files
    tool_calls: Optional[str] = None  # JSON string for tool calls
    tool_results: Optional[str] = None  # JSON string for tool results
    sources: Optional[str] = None  # JSON string for RAG sources

    model_config = ConfigDict(
        alias_generator=humps.camelize,
        populate_by_name=True,
        from_attributes=True,
    )

class ChatMessageCreate(ChatMessageBase):
    thread_id: UUID

class ChatMessageResponse(ChatMessageBase):
    id: UUID
    thread_id: UUID
    created_at: str

class ChatThreadBase(BaseModel):
    title: Optional[str] = None
    project_id: Optional[UUID] = None

    model_config = ConfigDict(
        alias_generator=humps.camelize,
        populate_by_name=True,
        from_attributes=True,
    )

class ChatThreadCreate(ChatThreadBase):
    pass

class ChatThreadResponse(ChatThreadBase):
    id: UUID
    created_at: str
    updated_at: str
    message_count: Optional[int] = 0

class ChatThreadWithMessages(ChatThreadResponse):
    messages: List[ChatMessageResponse] = []

    model_config = ConfigDict(
        from_attributes=True
    )

# Chat API Request/Response Schemas
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    project_id: str
    video_ids: Optional[List[str]] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=humps.camelize,
        populate_by_name=True,
    )

class ChatResponse(BaseModel):
    thread_id: str
    message: ChatMessageResponse
    sources: Optional[List[dict]] = None

    model_config = ConfigDict(
        alias_generator=humps.camelize,
        populate_by_name=True,
    )

class ChatHistoryResponse(BaseModel):
    thread_id: str
    messages: List[dict]
    total_count: int

# Response schemas with relationships

class ProjectWithVideoKnowledge(ProjectResponse):
    knowledge_items: List[KnowledgeItemResponse] = []
    videos: List[VideoResponse] = []
    chat_threads: List[ChatThreadResponse] = []

    model_config = ConfigDict(
        alias_generator=humps.camelize,  # Converts snake_case to camelCase for output
        from_attributes = True
    )
