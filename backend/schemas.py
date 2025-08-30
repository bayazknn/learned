from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


# Video Schemas
class VideoCreate(BaseModel):
    url: str  # YouTube video ID
    project_id: str

class VideoBase(VideoCreate):
    youtube_id: str
    title: str
    description: Optional[str] = None

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
    processing_status: Optional[str] = "pending"  # pending, processing, completed, failed
    processed_at: Optional[str] = None  # ISO format timestamp when processing completed
    
    class Config:
        from_attributes = True


# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    id : UUID
    created_at: Optional[str] = None  # ISO format timestamp

class ProjectResponse(ProjectBase):
    id: UUID
    created_at: Optional[str] = None  # ISO format timestamp
    video_count: Optional[int] = 0  # Computed field for number of videos
    
    class Config:
        from_attributes = True


# KnowledgeItem Schemas
class KnowledgeItemBase(BaseModel):
    content: str
    source_url: str
    source_type: str  # e.g., 'video', 'scraped'

class KnowledgeItemCreate(KnowledgeItemBase):
    project_id: UUID
    video_id: Optional[str] = None
    processing_status: Optional[str] = "pending"  # pending, processing, completed, failed
    embedding_model: Optional[str] = None  # e.g., 'ollama', 'gemini'
    task_id: Optional[str] = None  # Celery task ID for tracking

class KnowledgeItemResponse(KnowledgeItemBase):
    id: UUID
    project_id: UUID
    video_id: Optional[str] = None
    processing_status: Optional[str] = "pending"  # pending, processing, completed, failed
    embedding_model: Optional[str] = None  # e.g., 'ollama', 'gemini'
    task_id: Optional[str] = None  # Celery task ID for tracking
    processed_at: Optional[str] = None  # ISO format timestamp when processing completed

    
    class Config:
        from_attributes = True


# ScrapedContent Schemas
class ScrapedContentBase(BaseModel):
    url: str
    content: str

class ScrapedContentCreate(ScrapedContentBase):
    pass

class ScrapedContentResponse(ScrapedContentBase):
    id: UUID
    
    class Config:
        from_attributes = True


# Response schemas with relationships

class ProjectWithVideoKnowledge(ProjectResponse):
    knowledge_items: List[KnowledgeItemResponse] = []
    videos: List[VideoResponse] = []
    
    class Config:
        from_attributes = True
