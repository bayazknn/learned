from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from backend.database import get_db
from backend import crud, schemas
from backend.tasks.background import process_video_task

router = APIRouter(prefix="/videos", tags=["videos"])

@router.post("/", response_model=schemas.VideoResponse)
async def create_video(
    video_create: schemas.VideoCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new video by URL. Starts background processing for transcript extraction.
    Optionally associate with a project.
    """
    # Check if video already exists
    existing_video = crud.get_video_by_project(db, video_create.url.split("v=")[-1].split("&")[0], video_create.project_id)
    if existing_video:
        raise HTTPException(status_code=400, detail="Video already exists")
    
    # Start Celery background task for processing
    process_video_task.delay(video_create.url, video_create.project_id)
    #process_video_task.apply_async(args=[video_create.url, video_create.project_id], queue='video_processing')
    
    # Return immediate response with basic info
    from backend.services.youtube_info import get_video_info
    video_info = get_video_info(video_create.url)
    if not video_info:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    video_create = schemas.VideoBase(
        youtube_id=video_info['youtube_id'],
        title=video_info['title'],
        url=video_create.url,
        description=video_info.get('description'),
        project_id=video_create.project_id
    )
    
    db_video = crud.create_video(db, video_create)
    
    # Return response with all available metadata
    return schemas.VideoResponse(
        id=db_video.id,
        youtube_id=db_video.youtube_id,
        title=db_video.title,
        url=db_video.url,
        description=db_video.description,
        project_id=db_video.project_id,
        duration=video_info.get('duration'),
        upload_date=video_info.get('upload_date'),
        views=video_info.get('view_count'),
        thumbnail_url=video_info.get('thumbnail')
    )

@router.get("/", response_model=List[schemas.VideoResponse])
async def get_videos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all videos with pagination.
    """
    videos = crud.get_videos(db, skip=skip, limit=limit)
    return videos

@router.get("/project/{project_id}", response_model=List[schemas.VideoResponse | None])
async def get_videos_by_project(
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get videos by project ID with pagination.
    """
    videos = crud.get_videos_by_project(db, project_id, skip=skip, limit=limit)
    print(videos)
        
    return videos

@router.get("/{video_id}", response_model=schemas.VideoResponse)
async def get_video(
    video_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific video by ID.
    """
    db_video = crud.get_video(db, video_id)
    if db_video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return db_video

@router.get("/{video_id}/processing-status", response_model=schemas.VideoResponse)
async def get_video_processing_status(
    video_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the processing status of a specific video.
    This endpoint is useful for polling to check when background processing is complete.
    """
    db_video = crud.get_video(db, video_id)
    if db_video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return db_video

@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a video by ID.
    """
    db_video = crud.get_video(db, video_id)
    if db_video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    db.delete(db_video)
    db.commit()
    return {"message": "Video deleted successfully"}
