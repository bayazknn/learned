from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.database import get_db
from backend import crud, schemas

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=schemas.ProjectResponse)
async def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new research project.
    """
    db_project = crud.create_project(db, project)
    # Return with video count and created_at
    return schemas.ProjectResponse(
        id=db_project.id,
        name=db_project.name,
        description=db_project.description,
        created_at=db_project.created_at,
        video_count=0  # New project has 0 videos
    )

@router.put("/{project_id}", response_model=schemas.ProjectResponse)
async def update_project(project: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    """
    Update an existing project.
    """
    db_project = crud.get_project(db, project.id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    updated_project = crud.update_project(db, project)
    
    return schemas.ProjectResponse(
        id=updated_project.id,
        name=updated_project.name,
        description=updated_project.description,
        created_at=updated_project.created_at,
        video_count=len(updated_project.videos)  # Return current video count
    )

@router.get("/", response_model=List[schemas.ProjectResponse])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all projects with pagination and video count.
    """
    projects = crud.get_projects(db, skip=skip, limit=limit)
    
    # Convert to response models with video count
    project_responses = []
    for project in projects:
        video_count = len(project.videos)
        project_response = schemas.ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            video_count=video_count
        )
        project_responses.append(project_response)
    
    return project_responses

@router.get("/{project_id}", response_model=schemas.ProjectWithVideoKnowledge)
async def get_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific project by ID with its knowledge items.
    """
    db_project = crud.get_project(db, project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get video items for this project
    video_items = crud.get_videos_by_project(db, project_id)

    # Convert to video response models
    video_responses = [
        schemas.VideoResponse(
            id=video.id,
            project_id=video.project_id,
            title=video.title,
            description=video.description,
            url=video.url,
            transcript=video.transcript,
            duration=video.duration,
            uploaded_date=video.uploaded_date,
            views=video.views,
            thumbnail_url=video.thumbnail_url
        )
        for video in video_items
    ]


    # Get knowledge items for this project
    knowledge_items = crud.get_knowledge_items_by_project(db, project_id)
    
    # Convert to response models
    knowledge_responses = [
        schemas.KnowledgeItemResponse(
            id=item.id,
            project_id=item.project_id,
            content=item.content,
            source_url=item.source_url,
            source_type=item.source_type,
            video_id=item.video_id
        )
        for item in knowledge_items
    ]
    
    return schemas.ProjectWithVideoKnowledge(
        id=db_project.id,
        name=db_project.name,
        description=db_project.description,
        created_at=db_project.created_at,
        video_count=len(db_project.videos),
        knowledge_items=knowledge_responses,
        videos=video_responses,
    )

@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a project by ID.
    """
    db_project = crud.get_project(db, project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete associated knowledge items first
    knowledge_items = crud.get_knowledge_items_by_project(db, project_id)
    for item in knowledge_items:
        db.delete(item)
    
    db.delete(db_project)
    db.commit()
    
    # Delete from RAG (placeholder - would need RAG integration)
    # from backend.services.rag import delete_project_knowledge
    # delete_project_knowledge(str(project_id))
    
    return {"message": "Project deleted successfully"}
