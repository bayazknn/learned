from celery import Celery
from sqlalchemy.orm import Session
import logging
from typing import Optional
import time

from backend.database import SessionLocal
from backend import crud, schemas
from backend.services.youtube_transcript import extract_transcript
from backend.services.youtube_info import get_video_info
from backend.services.scraping import scrape_url
from backend.services.rag import store_embeddings

logger = logging.getLogger(__name__)

# Initialize Celery app
app = Celery(
    'background_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@app.task(name='process_video_task')
def process_video_task(video_url: str, project_id: Optional[str] = None) -> dict:
    """
    Background task to process a YouTube video: extract info, transcript, and store in RAG.
    
    Args:
        video_url: YouTube video URL
        project_id: Optional project ID to associate with the video
        
    Returns:
        dict: Processing result with status, video_id, and details
    """
    db: Session = SessionLocal()
    result = {
        'status': 'failed',
        'video_id': None,
        'transcript_extracted': False,
        'error': None
    }
    
    try:
        # Get video information
        video_info = get_video_info(video_url)
        if not video_info:
            error_msg = f"Failed to get video info for: {video_url}"
            logger.error(error_msg)
            result['error'] = error_msg
            return result
        
        result['video_id'] = video_info['youtube_id']
        
        # Find existing video by youtube_id and project_id
        db_video = crud.get_video_by_project(db, video_info['youtube_id'], project_id)
        if not db_video:
            # Video doesn't exist, create it (shouldn't happen normally)
            video_create = schemas.VideoBase(
                youtube_id=video_info['youtube_id'],
                title=video_info['title'],
                url=video_url,
                description=video_info.get('description'),
                project_id=project_id
            )
            db_video = crud.create_video(db, video_create)
            logger.warning(f"Video {video_info['youtube_id']} not found, created new record")
        
        # Update video processing status to processing
        db_video.processing_status = "processing"
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        # Update video with additional metadata
        if video_info.get('duration'):
            db_video.duration = video_info['duration']
        if video_info.get('upload_date'):
            db_video.upload_date = video_info['upload_date']
        if video_info.get('view_count'):
            db_video.views = video_info['view_count']
        if video_info.get('thumbnail'):
            db_video.thumbnail_url = video_info['thumbnail']
        
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        # Extract transcript with detailed error handling
        transcript = None
        try:
            transcript = extract_transcript(video_url)
            if transcript:
                # Update video with transcript
                crud.update_video_transcript(db, db_video.id, transcript)
                
                # Create knowledge item with pending status for RAG processing
                knowledge_item = crud.create_knowledge_item(db, schemas.KnowledgeItemCreate(
                    project_id=project_id,
                    video_id=str(db_video.id),
                    content=transcript,
                    source_url=video_url,
                    source_type='transcript',
                    processing_status='pending'  # Will be updated by RAG task
                ))
                result['transcript_extracted'] = True
                result['knowledge_item_id'] = str(knowledge_item.id)
                logger.info(f"Successfully extracted transcript for video: {video_info['youtube_id']}")
                
                # Trigger RAG storage task asynchronously
                if project_id:
                    store_embeddings_task.apply_async(
                        args=[str(knowledge_item.id), project_id, transcript, video_url, str(db_video.id)],
                        queue='rag_processing'
                    )
                    logger.info(f"Triggered RAG storage task for knowledge item: {knowledge_item.id}")
                
            else:
                logger.warning(f"No transcript available for video: {video_info['youtube_id']}")
                result['error'] = "No transcript available"
                
        except Exception as transcript_error:
            logger.warning(f"Transcript extraction failed for video {video_info['youtube_id']}: {transcript_error}")
            result['error'] = f"Transcript extraction failed: {transcript_error}"
            # Continue processing even if transcript extraction fails
        
        # Set result status based on processing outcome
        result['status'] = 'success' if video_info and not result.get('error') else 'partial_success'
        
        # Update final processing status and timestamp
        from datetime import datetime
        db_video.processing_status = 'completed' if result['status'] == 'success' else 'failed'
        db_video.processed_at = datetime.now().isoformat()
        db.add(db_video)
        db.commit()
        
        logger.info(f"Processed video: {video_info['youtube_id']} - Status: {result['status']}")
        return result
        
    except Exception as e:
        db.rollback()
        error_msg = f"Error processing video {video_url}: {e}"
        logger.error(error_msg)
        result['error'] = error_msg
        return result
    finally:
        db.close()

@app.task
def scrape_url_task(url: str, project_id: Optional[str] = None) -> Optional[str]:
    """
    Background task to scrape content from a URL and optionally store in RAG.
    
    Args:
        url: URL to scrape
        project_id: Optional project ID to associate with scraped content
        
    Returns:
        str: URL if successful, None otherwise
    """
    db: Session = SessionLocal()
    try:
        # Scrape content
        content = scrape_url(url)
        if not content:
            logger.error(f"Failed to scrape content from: {url}")
            return None
        
        # Create scraped content in database
        scraped_create = schemas.ScrapedContentCreate(
            url=url,
            content=content
        )
        
        db_scraped = crud.create_scraped_content(db, scraped_create)
        
        # Store in RAG if project_id provided
        if project_id:
            success = store_embeddings(project_id, content, url)
            if success:
                logger.info(f"Successfully stored scraped content in RAG for project: {project_id}")
            else:
                logger.warning(f"Failed to store scraped content in RAG for project: {project_id}")
        
        db.commit()
        logger.info(f"Successfully scraped URL: {url}")
        return url
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error scraping URL {url}: {e}")
        return None
    finally:
        db.close()

@app.task
def process_knowledge_item_task(project_id: str, content: str, source_url: str) -> bool:
    """
    Background task to process a knowledge item and store in RAG.
    
    Args:
        project_id: Project ID to associate with the knowledge
        content: Knowledge content text
        source_url: Source URL of the knowledge
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Store in RAG
        success = store_embeddings(project_id, content, source_url)
        
        if success:
            logger.info(f"Successfully stored knowledge item in RAG for project: {project_id}")
        else:
            logger.error(f"Failed to store knowledge item in RAG for project: {project_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error processing knowledge item for project {project_id}: {e}")
        return False

@app.task(bind=True)
def store_embeddings_task(self, knowledge_item_id: str, project_id: str, content: str, source_url: str, video_id: Optional[str] = None) -> dict:
    """
    Background task to store transcript embeddings in RAG with status tracking.
    
    Args:
        knowledge_item_id: KnowledgeItem ID to update with status
        project_id: Project ID for RAG collection
        content: Transcript content to embed
        source_url: Source video URL
        video_id: Database video ID for metadata
        
    Returns:
        dict: Result with status and details
    """
    db: Session = SessionLocal()
    result = {
        'status': 'failed',
        'knowledge_item_id': knowledge_item_id,
        'error': None
    }
    
    try:
        # Update knowledge item status to processing
        from uuid import UUID
        knowledge_uuid = UUID(knowledge_item_id)
        crud.update_knowledge_item_status(
            db, knowledge_uuid, 
            processing_status="processing",
            task_id=self.request.id
        )
        
        # Store embeddings using default Ollama model
        from backend.services.rag import store_embeddings_with_metadata
        success = store_embeddings_with_metadata(
            project_id=project_id,
            text=content,
            source_url=source_url,
            video_id=video_id,
            embedding_model="ollama"
        )
        
        if success:
            # Update knowledge item status to completed
            crud.update_knowledge_item_status(
                db, knowledge_uuid,
                processing_status="completed",
                embedding_model="ollama"
            )
            result['status'] = 'success'
            logger.info(f"Successfully stored embeddings for knowledge item: {knowledge_item_id}")
        else:
            # Update knowledge item status to failed
            crud.update_knowledge_item_status(
                db, knowledge_uuid,
                processing_status="failed",
                embedding_model="ollama"
            )
            result['error'] = "Failed to store embeddings in RAG"
            logger.error(f"Failed to store embeddings for knowledge item: {knowledge_item_id}")
        
        return result
        
    except Exception as e:
        db.rollback()
        error_msg = f"Error storing embeddings for knowledge item {knowledge_item_id}: {e}"
        logger.error(error_msg)
        result['error'] = error_msg
        
        # Update knowledge item status to failed on error
        try:
            from uuid import UUID
            knowledge_uuid = UUID(knowledge_item_id)
            crud.update_knowledge_item_status(
                db, knowledge_uuid,
                processing_status="failed",
                embedding_model="ollama"
            )
        except Exception:
            pass  # Ignore errors during cleanup
        
        return result
    finally:
        db.close()

@app.task
def batch_process_videos_task(video_urls: list, project_id: Optional[str] = None) -> dict:
    """
    Background task to process multiple videos in batch.
    
    Args:
        video_urls: List of YouTube video URLs
        project_id: Optional project ID to associate with all videos
        
    Returns:
        dict: Results with success count and individual results
    """
    results = {
        'total': len(video_urls),
        'successful': 0,
        'partial_success': 0,
        'failed': 0,
        'results': []
    }
    
    for video_url in video_urls:
        try:
            result = process_video_task.apply_async(args=[video_url, project_id]).get()
            if result and result.get('status') == 'success':
                results['successful'] += 1
                results['results'].append({
                    'url': video_url, 
                    'status': 'success', 
                    'video_id': result.get('video_id'),
                    'transcript_extracted': result.get('transcript_extracted', False)
                })
            elif result and result.get('status') == 'partial_success':
                results['partial_success'] += 1
                results['results'].append({
                    'url': video_url, 
                    'status': 'partial_success', 
                    'video_id': result.get('video_id'),
                    'transcript_extracted': result.get('transcript_extracted', False),
                    'error': result.get('error')
                })
            else:
                results['failed'] += 1
                results['results'].append({
                    'url': video_url, 
                    'status': 'failed',
                    'error': result.get('error') if result else 'Unknown error'
                })
        except Exception as e:
            results['failed'] += 1
            results['results'].append({
                'url': video_url, 
                'status': 'error', 
                'error': str(e)
            })
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    return results

# Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

if __name__ == '__main__':
    app.start()
