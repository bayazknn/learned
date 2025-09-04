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
    # Get video info first to ensure consistent YouTube ID extraction
    from backend.services.youtube_info import get_video_info
    video_info = get_video_info(video_create.url)
    if not video_info:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    # Check if video already exists using YouTube ID from API
    existing_video = crud.get_video_by_project(db, video_info['youtube_id'], video_create.project_id)
    if existing_video:
        raise HTTPException(status_code=400, detail="Video already exists")

    # Create video with data from YouTube API
    video_data = schemas.VideoBase(
        youtube_id=video_info['youtube_id'],
        title=video_info['title'],
        url=video_create.url,
        description=video_info.get('description'),
        project_id=video_create.project_id
    )

    db_video = crud.create_video(db, video_data)

    # Start Celery background task for processing (pass YouTube ID for consistency)
    process_video_task.apply_async(args=[video_info['youtube_id'], video_create.project_id])

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
    
    # Convert videos to response models with sources
    video_responses = []
    for video in videos:
        # Get knowledge items for this video
        knowledge_items = crud.get_knowledge_items_by_video(db, str(video.id))
        
        # Convert knowledge items to video sources (exclude transcripts)
        sources = [
            schemas.VideoSource(
                id=item.id,
                source_url=item.source_url,
                source_type=item.source_type,
                content=item.content
            )
            for item in knowledge_items
            if item.source_type != "transcript"
        ]
        
        # Create video response with sources
        video_response = schemas.VideoResponse(
            id=video.id,
            youtube_id=video.youtube_id,
            title=video.title,
            url=video.url,
            description=video.description,
            transcript=video.transcript,
            project_id=video.project_id,
            duration=video.duration,
            upload_date=video.upload_date,
            views=video.views,
            thumbnail_url=video.thumbnail_url,
            channel=video.channel,
            channel_id=video.channel_id,
            processing_status=video.processing_status,
            processed_at=video.processed_at,
            summary=video.summary,
            summary_processing_status=video.summary_processing_status,
            summary_processed_at=video.summary_processed_at,
            sources=sources
        )
        video_responses.append(video_response)
    
    return video_responses

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
    
    # Convert videos to response models with sources
    video_responses = []
    for video in videos:
        # Get knowledge items for this video
        knowledge_items = crud.get_knowledge_items_by_video(db, str(video.id))
        
        # Convert knowledge items to video sources (exclude transcripts)
        sources = [
            schemas.VideoSource(
                id=item.id,
                source_url=item.source_url,
                source_type=item.source_type,
                content=item.content
            )
            for item in knowledge_items
            if item.source_type != "transcript"
        ]
        
        # Create video response with sources
        video_response = schemas.VideoResponse(
            id=video.id,
            youtube_id=video.youtube_id,
            title=video.title,
            url=video.url,
            description=video.description,
            transcript=video.transcript,
            project_id=video.project_id,
            duration=video.duration,
            upload_date=video.upload_date,
            views=video.views,
            thumbnail_url=video.thumbnail_url,
            channel=video.channel,
            channel_id=video.channel_id,
            processing_status=video.processing_status,
            processed_at=video.processed_at,
            summary=video.summary,
            summary_processing_status=video.summary_processing_status,
            summary_processed_at=video.summary_processed_at,
            sources=sources
        )
        video_responses.append(video_response)
    
    return video_responses

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
    
    # Get knowledge items for this video
    knowledge_items = crud.get_knowledge_items_by_video(db, video_id)
    
    # Convert knowledge items to video sources (exclude transcripts)
    sources = [
        schemas.VideoSource(
            id=item.id,
            source_url=item.source_url,
            source_type=item.source_type,
            content=item.content
        )
        for item in knowledge_items
        if item.source_type != "transcript"
    ]
    
    # Create video response with sources
    video_response = schemas.VideoResponse(
        id=db_video.id,
        youtube_id=db_video.youtube_id,
        title=db_video.title,
        url=db_video.url,
        description=db_video.description,
        transcript=db_video.transcript,
        project_id=db_video.project_id,
        duration=db_video.duration,
        upload_date=db_video.upload_date,
        views=db_video.views,
        thumbnail_url=db_video.thumbnail_url,
        channel=db_video.channel,
        channel_id=db_video.channel_id,
        processing_status=db_video.processing_status,
        processed_at=db_video.processed_at,
        summary=db_video.summary,
        summary_processing_status=db_video.summary_processing_status,
        summary_processed_at=db_video.summary_processed_at,
        sources=sources
    )
    
    return video_response

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
    
    # Get knowledge items for this video
    knowledge_items = crud.get_knowledge_items_by_video(db, video_id)
    
    # Convert knowledge items to video sources (exclude transcripts)
    sources = [
        schemas.VideoSource(
            id=item.id,
            source_url=item.source_url,
            source_type=item.source_type,
            content=item.content
        )
        for item in knowledge_items
        if item.source_type != "transcript"
    ]
    
    # Create video response with sources
    video_response = schemas.VideoResponse(
        id=db_video.id,
        youtube_id=db_video.youtube_id,
        title=db_video.title,
        url=db_video.url,
        description=db_video.description,
        transcript=db_video.transcript,
        project_id=db_video.project_id,
        duration=db_video.duration,
        upload_date=db_video.upload_date,
        views=db_video.views,
        thumbnail_url=db_video.thumbnail_url,
        channel=db_video.channel,
        channel_id=db_video.channel_id,
        processing_status=db_video.processing_status,
        processed_at=db_video.processed_at,
        summary=db_video.summary,
        summary_processing_status=db_video.summary_processing_status,
        summary_processed_at=db_video.summary_processed_at,
        sources=sources
    )
    
    return video_response

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
