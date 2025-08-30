import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    youtube_id = Column(String, index=True)  # YouTube video ID
    title = Column(String, index=True)
    url = Column(String, index=True)
    transcript = Column(Text)
    description = Column(Text)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    upload_date = Column(String, nullable=True)  # YYYYMMDD format
    views = Column(Integer, nullable=True)  # View count
    thumbnail_url = Column(String, nullable=True)  # Thumbnail URL
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processed_at = Column(String, nullable=True)  # ISO format timestamp when processing completed
    
    project = relationship("Project", back_populates="videos")
    knowledge_items = relationship("KnowledgeItem", back_populates="video")

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    created_at = Column(String, default=lambda: datetime.now().isoformat())  # ISO format timestamp

    knowledge_items = relationship("KnowledgeItem", back_populates="project")
    videos = relationship("Video", back_populates="project")

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=True)
    content = Column(Text)
    source_url = Column(String)
    source_type = Column(String)  # e.g., 'video', 'scraped'
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    embedding_model = Column(String, nullable=True)  # e.g., 'ollama', 'gemini'
    task_id = Column(String, nullable=True)  # Celery task ID for tracking
    processed_at = Column(String, nullable=True)  # ISO format timestamp when processing completed

    video = relationship("Video", back_populates="knowledge_items")
    project = relationship("Project", back_populates="knowledge_items")

class ScrapedContent(Base):
    __tablename__ = "scraped_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    url = Column(String, unique=True, index=True)
    content = Column(Text)
