from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from . import models, schemas


# Video CRUD operations
def create_video(db: Session, video: schemas.VideoBase) -> models.Video:
    # Check if video already exists
    existing_video = get_video_by_project(db, video.youtube_id, video.project_id)
    if existing_video:
        # Update existing video with new data (except transcript and metadata if they already exist)
        for field, value in video.__dict__.items():
            if value is not None and hasattr(existing_video, field):
                setattr(existing_video, field, value)
        db.commit()
        db.refresh(existing_video)
        return existing_video
    
    db_video = models.Video(**video.model_dump())
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

def get_video(db: Session, video_id: str) -> Optional[models.Video]:
    return db.query(models.Video).filter(models.Video.id == video_id).first()

def get_video_by_project(db: Session, video_id: str, project_id: str) -> Optional[models.Video]:
    from uuid import UUID
    try:
        # Convert project_id string to UUID object
        project_uuid = UUID(project_id)
        return db.query(models.Video).filter(models.Video.youtube_id == video_id).filter(models.Video.project_id == project_uuid).first()
    except ValueError:
        # If project_id is not a valid UUID, return None
        return None

def get_videos(db: Session, skip: int = 0, limit: int = 100) -> List[models.Video]:
    return db.query(models.Video).offset(skip).limit(limit).all()

def get_videos_by_project(db: Session, project_id: UUID, skip: int = 0, limit: int = 100) -> List[models.Video]:
    return db.query(models.Video).filter(models.Video.project_id == project_id).offset(skip).limit(limit).all()

def update_video_transcript(db: Session, video_id: str, transcript: str) -> Optional[models.Video]:
    db_video = get_video(db, video_id)
    if db_video:
        db_video.transcript = transcript
        db.commit()
        db.refresh(db_video)
    return db_video






# Project CRUD operations
def create_project(db: Session, project: schemas.ProjectCreate | schemas.ProjectUpdate) -> models.Project:
    project_id = getattr(project, 'id', None)
    if project_id:
        existing_project = get_project(db, project_id)
        if existing_project:
            for field in project.__dict__:
                if field != "id" and hasattr(existing_project, field):
                    setattr(existing_project, field, getattr(project, field))
            db.commit()
            db.refresh(existing_project)
            return existing_project
    
    db_project = models.Project(
        name=project.name,
        description=project.description
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def update_project(db: Session, project: schemas.ProjectUpdate) -> Optional[models.Project]:
    db_project = get_project(db, project.id)
    if db_project:
        for field in project.__dict__:
            if field != "id" and hasattr(db_project, field):
                setattr(db_project, field, getattr(project, field))
        db.commit()
        db.refresh(db_project)
    return db_project

def get_project(db: Session, project_id: UUID) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[models.Project]:
    return db.query(models.Project).offset(skip).limit(limit).all()





# KnowledgeItem CRUD operations
def create_knowledge_item(db: Session, knowledge_item: schemas.KnowledgeItemCreate) -> models.KnowledgeItem:
    from uuid import UUID
    # Convert video_id from string to UUID if provided
    video_id_uuid = None
    if knowledge_item.video_id:
        try:
            video_id_uuid = UUID(knowledge_item.video_id)
        except ValueError:
            # If video_id is not a valid UUID, keep it as None
            video_id_uuid = None
    
    db_knowledge_item = models.KnowledgeItem(
        project_id=knowledge_item.project_id,
        video_id=video_id_uuid,
        content=knowledge_item.content,
        source_url=knowledge_item.source_url,
        source_type=knowledge_item.source_type,
        processing_status=knowledge_item.processing_status,
        embedding_model=knowledge_item.embedding_model,
        task_id=knowledge_item.task_id
    )
    db.add(db_knowledge_item)
    db.commit()
    db.refresh(db_knowledge_item)
    return db_knowledge_item

def get_knowledge_items_by_project(db: Session, project_id: UUID) -> List[models.KnowledgeItem]:
    return db.query(models.KnowledgeItem).filter(models.KnowledgeItem.project_id == project_id).all()

def get_knowledge_item_video_transcript(db: Session, video_id: str) -> models.KnowledgeItem:
    return db.query(models.KnowledgeItem).filter(models.KnowledgeItem.video_id == video_id).filter(models.KnowledgeItem.source_type == "transcript").first()

def get_knowledge_item(db: Session, knowledge_item_id: UUID) -> Optional[models.KnowledgeItem]:
    return db.query(models.KnowledgeItem).filter(models.KnowledgeItem.id == knowledge_item_id).first()

def update_knowledge_item_status(db: Session, knowledge_item_id: UUID, 
                               processing_status: str, 
                               embedding_model: Optional[str] = None,
                               task_id: Optional[str] = None) -> Optional[models.KnowledgeItem]:
    """
    Update knowledge item processing status and related fields.
    
    Args:
        knowledge_item_id: KnowledgeItem ID to update
        processing_status: New processing status
        embedding_model: Embedding model used (optional)
        task_id: Celery task ID (optional)
        
    Returns:
        Updated KnowledgeItem or None if not found
    """
    db_knowledge_item = get_knowledge_item(db, knowledge_item_id)
    if db_knowledge_item:
        db_knowledge_item.processing_status = processing_status
        if embedding_model:
            db_knowledge_item.embedding_model = embedding_model
        if task_id:
            db_knowledge_item.task_id = task_id
        
        # Update processed_at timestamp if status is completed or failed
        if processing_status in ["completed", "failed"]:
            from datetime import datetime
            db_knowledge_item.processed_at = datetime.now().isoformat()
        
        db.commit()
        db.refresh(db_knowledge_item)
    return db_knowledge_item





# ScrapedContent CRUD operations
def create_scraped_content(db: Session, scraped_content: schemas.ScrapedContentCreate) -> models.ScrapedContent:
    db_scraped_content = models.ScrapedContent(
        url=scraped_content.url,
        content=scraped_content.content
    )
    db.add(db_scraped_content)
    db.commit()
    db.refresh(db_scraped_content)
    return db_scraped_content

def get_scraped_content(db: Session, url: str) -> Optional[models.ScrapedContent]:
    return db.query(models.ScrapedContent).filter(models.ScrapedContent.url == url).first()

def get_all_scraped_content(db: Session, skip: int = 0, limit: int = 100) -> List[models.ScrapedContent]:
    return db.query(models.ScrapedContent).offset(skip).limit(limit).all()
