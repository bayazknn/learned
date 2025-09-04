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
    channel = Column(String, nullable=True)  # YouTube channel name
    channel_id = Column(String, nullable=True)  # YouTube channel ID
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processed_at = Column(String, nullable=True)  # ISO format timestamp when processing completed
    summary = Column(Text, nullable=True)  # AI-generated summary of the transcript
    summary_processing_status = Column(String, default="pending")  # pending, processing, completed, failed for summary generation
    summary_processed_at = Column(String, nullable=True)  # ISO format timestamp when summary processing completed
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    
    project = relationship("Project", back_populates="videos")
    knowledge_items = relationship("KnowledgeItem", back_populates="video")

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    prompt_context = Column(Text, nullable=True)  # Custom prompt context for LLMs
    created_at = Column(String, default=lambda: datetime.now().isoformat())  # ISO format timestamp

    knowledge_items = relationship("KnowledgeItem", back_populates="project")
    videos = relationship("Video", back_populates="project")
    chat_threads = relationship("ChatThread", back_populates="project")

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
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    video = relationship("Video", back_populates="knowledge_items")
    project = relationship("Project", back_populates="knowledge_items")

class ChatThread(Base):
    __tablename__ = "chat_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=True)  # Auto-generated or user-set title
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    user_id = Column(String, nullable=True)  # For future multi-user support
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, default=lambda: datetime.now().isoformat())

    project = relationship("Project", back_populates="chat_threads")
    messages = relationship("ChatMessage", back_populates="thread", order_by="ChatMessage.created_at")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("chat_threads.id"))
    role = Column(String)  # 'user', 'assistant', 'system'
    content = Column(Text)
    message_type = Column(String, default="text")  # 'text', 'file', 'tool_call', 'tool_result'
    file_url = Column(String, nullable=True)  # For file uploads
    file_name = Column(String, nullable=True)  # For file uploads
    file_type = Column(String, nullable=True)  # MIME type for files
    tool_calls = Column(Text, nullable=True)  # JSON string for tool calls
    tool_results = Column(Text, nullable=True)  # JSON string for tool results
    sources = Column(Text, nullable=True)  # JSON string for RAG sources
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    thread = relationship("ChatThread", back_populates="messages")
