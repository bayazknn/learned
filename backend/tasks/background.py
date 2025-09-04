from celery import Celery, chain
from sqlalchemy.orm import Session
import logging
from typing import Optional
import time

from backend.database import SessionLocal
from backend import crud, schemas, models
from backend.services.youtube_transcript import extract_transcript
from backend.services.youtube_info import get_video_info
from backend.services.scrape import scrape_content, clean_text_content
from backend.services.rag_llama_index import store_embeddings
from backend.prompts.agent_prompts import get_summary_prompt, get_resource_extraction_prompt
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
import json
from urllib.parse import urlparse

# Configure logging for Celery worker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Celery app
app = Celery(
    'background_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

@app.task(name='process_video_task')
def process_video_task(youtube_id: str, project_id: Optional[str] = None) -> dict:
    """
    Background task to process a YouTube video: extract transcript, and store in RAG.

    Args:
        youtube_id: YouTube video ID (consistent with API endpoint)
        project_id: Optional project ID to associate with the video

    Returns:
        dict: Processing result with status, video_id, and details
    """
    db: Session = SessionLocal()
    result = {
        'status': 'failed',
        'video_id': youtube_id,
        'transcript_extracted': False,
        'error': None
    }

    try:
        # Find existing video by youtube_id and project_id
        db_video = crud.get_video_by_project(db, youtube_id, project_id)
        if not db_video:
            # Video should have been created by API endpoint - this is an error
            error_msg = f"Video {youtube_id} not found in database. Video should have been created by API endpoint."
            logger.error(error_msg)
            result['error'] = error_msg
            return result

        # Update video processing status to processing
        db_video.processing_status = "processing"
        db.add(db_video)
        db.commit()
        db.refresh(db_video)

        # Get video URL for transcript extraction
        video_url = db_video.url

        # Extract video metadata first
        video_info = None
        try:
            video_info = get_video_info(video_url)
            if video_info:
                # Update video with metadata
                db_video.title = video_info.get('title', db_video.title)
                db_video.description = video_info.get('description', db_video.description)
                db_video.duration = video_info.get('duration')
                db_video.views = video_info.get('view_count')
                db_video.upload_date = video_info.get('upload_date')
                db_video.thumbnail_url = video_info.get('thumbnail')
                db_video.channel_name = video_info.get('channel')
                db.add(db_video)
                db.commit()
                db.refresh(db_video)
                logger.info(f"Successfully extracted video metadata for: {youtube_id}")
            else:
                logger.warning(f"Failed to extract video metadata for: {youtube_id}")
        except Exception as metadata_error:
            logger.warning(f"Video metadata extraction failed for {youtube_id}: {metadata_error}")
            # Continue processing even if metadata extraction fails

        # Extract transcript with detailed error handling
        transcript = None
        try:
            transcript = extract_transcript(video_url)
            if transcript:
                # Update video with transcript
                crud.update_video_transcript(db, db_video.id, transcript)

                # Only create knowledge item and trigger tasks if we have a project_id
                if project_id:
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
                    logger.info(f"Successfully extracted transcript for video: {youtube_id}")

                    # Trigger summarize task, RAG storage task, and resource extraction task asynchronously
                    chain(
                        summarize_transcript_task.si(str(db_video.id), project_id, transcript),
                        store_embeddings_task.si(str(knowledge_item.id), project_id, transcript, video_url, str(db_video.id)),
                        extract_resources_task.si(str(db_video.id), project_id, "gemini")  # Default to Gemini
                    ).apply_async()
                    logger.info(f"Triggered summarize, embedding storage, and resource extraction tasks for video: {db_video.id}")
                else:
                    # For videos without projects, just mark transcript as extracted
                    result['transcript_extracted'] = True
                    logger.info(f"Successfully extracted transcript for video: {youtube_id} (no project)")

            else:
                logger.warning(f"No transcript available for video: {youtube_id}")
                result['error'] = "No transcript available"

        except Exception as transcript_error:
            logger.warning(f"Transcript extraction failed for video {youtube_id}: {transcript_error}")
            result['error'] = f"Transcript extraction failed: {transcript_error}"
            # Continue processing even if transcript extraction fails

        # Set result status based on processing outcome
        result['status'] = 'success' if transcript and not result.get('error') else 'partial_success'

        # Update final processing status and timestamp
        from datetime import datetime
        db_video.processing_status = 'completed' if result['status'] == 'success' else 'failed'
        db_video.processed_at = datetime.now().isoformat()
        db.add(db_video)
        db.commit()

        # Ensure all datetime objects are converted to strings for JSON serialization
        if 'processed_at' in result:
            result['processed_at'] = str(result['processed_at'])

        logger.info(f"Processed video: {youtube_id} - Status: {result['status']}")
        return result

    except Exception as e:
        db.rollback()
        error_msg = f"Error processing video {youtube_id}: {e}"
        logger.error(error_msg)
        result['error'] = error_msg
        return result
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
def scrape_sources_task(self, knowledge_item_id: str) -> dict:
    """
    Background task to scrape content for a knowledge item based on its source_type.

    Args:
        knowledge_item_id: KnowledgeItem ID to scrape content for

    Returns:
        dict: Result with status and scraping details
    """
    from uuid import UUID
    from datetime import datetime
    from backend.services.scrape import scrape_content
    from backend.services.rag_llama_index import store_embeddings_with_metadata

    db: Session = SessionLocal()
    result = {
        'status': 'failed',
        'knowledge_item_id': knowledge_item_id,
        'content_scraped': False,
        'embeddings_stored': False,
        'error': None
    }

    try:
        # Get knowledge item
        knowledge_uuid = UUID(knowledge_item_id)
        db_knowledge_item = crud.get_knowledge_item(db, knowledge_uuid)

        if not db_knowledge_item:
            error_msg = f"Knowledge item not found: {knowledge_item_id}"
            logger.error(error_msg)
            result['error'] = error_msg
            return result

        # Update status to processing
        db_knowledge_item.processing_status = "processing"
        db_knowledge_item.task_id = self.request.id
        db.add(db_knowledge_item)
        db.commit()

        # Log knowledge item details for debugging
        logger.info(f"Processing knowledge item {knowledge_item_id}:")
        logger.info(f"  - Source type: {db_knowledge_item.source_type}")
        logger.info(f"  - Source URL: {db_knowledge_item.source_url}")
        logger.info(f"  - Content type: {type(db_knowledge_item.content)}")
        logger.info(f"  - Content length: {len(db_knowledge_item.content) if db_knowledge_item.content else 0}")
        logger.info(f"  - Content is None: {db_knowledge_item.content is None}")
        logger.info(f"  - Content is empty string: {db_knowledge_item.content == ''}")
        logger.info(f"  - Content repr: {repr(db_knowledge_item.content)}")
        logger.info(f"  - Content preview: '{db_knowledge_item.content[:100] if db_knowledge_item.content else 'None'}...'")

        # Scrape content based on source_type
        content_to_scrape = db_knowledge_item.content if db_knowledge_item.source_type == 'arxiv-no-link' else ""
        logger.info(f"Content to scrape for {db_knowledge_item.source_type}: '{content_to_scrape[:100] if content_to_scrape else 'None'}...'")

        scraped_content = scrape_content(
            source_url=db_knowledge_item.source_url,
            source_type=db_knowledge_item.source_type,
            content=content_to_scrape
        )

        if not scraped_content:
            # Handle different failure scenarios
            if db_knowledge_item.source_type == 'arxiv-no-link':
                if not db_knowledge_item.content or not db_knowledge_item.content.strip():
                    # Content is empty or whitespace
                    error_msg = f"No valid content provided for arxiv-no-link scraping: {knowledge_item_id}. Content: '{db_knowledge_item.content}'"
                    logger.warning(error_msg)
                else:
                    # Content exists but scraping failed
                    error_msg = f"Failed to scrape arxiv paper with title: '{db_knowledge_item.content[:100]}...' for knowledge item: {knowledge_item_id}"
                    logger.error(error_msg)
            elif db_knowledge_item.source_type == 'tool':
                # Expected - tools don't need scraping
                error_msg = f"Tool source type - no scraping needed: {knowledge_item_id}"
                logger.info(error_msg)
            elif db_knowledge_item.source_type == 'video':
                # Expected - video processing is handled separately
                error_msg = f"Video source type - no scraping needed: {knowledge_item_id}"
                logger.info(error_msg)
            else:
                # Unexpected failure
                error_msg = f"Failed to scrape content for knowledge item: {knowledge_item_id} (type: {db_knowledge_item.source_type})"
                logger.error(error_msg)

            result['error'] = error_msg

            # Update status to failed but preserve existing content
            logger.info(f"Updating knowledge item {knowledge_item_id} status to 'failed'")
            logger.info(f"Current status before update: {db_knowledge_item.processing_status}")
            logger.info(f"Current content before update: '{db_knowledge_item.content[:100] if db_knowledge_item.content else 'None'}...'")

            db_knowledge_item.processing_status = "failed"
            db.add(db_knowledge_item)
            db.commit()
            db.refresh(db_knowledge_item)

            logger.info(f"Updated knowledge item {knowledge_item_id} status to: {db_knowledge_item.processing_status}")
            logger.info(f"Content after update: '{db_knowledge_item.content[:100] if db_knowledge_item.content else 'None'}...'")

            return result

        # Clean the scraped content to remove null characters and other problematic characters
        cleaned_content = clean_text_content(scraped_content)

        # Only update content if we have new scraped content
        if cleaned_content and cleaned_content.strip():
            # Update knowledge item with cleaned scraped content
            db_knowledge_item.content = cleaned_content
            db.add(db_knowledge_item)
            db.commit()
        else:
            # If cleaned content is empty, preserve existing content and mark as failed
            logger.warning(f"Scraped content was empty after cleaning for knowledge item: {knowledge_item_id}")
            logger.info(f"Updating knowledge item {knowledge_item_id} status to 'failed' (empty content)")
            logger.info(f"Current status before update: {db_knowledge_item.processing_status}")
            logger.info(f"Current content before update: '{db_knowledge_item.content[:100] if db_knowledge_item.content else 'None'}...'")

            db_knowledge_item.processing_status = "failed"
            db.add(db_knowledge_item)
            db.commit()
            db.refresh(db_knowledge_item)

            logger.info(f"Updated knowledge item {knowledge_item_id} status to: {db_knowledge_item.processing_status}")
            logger.info(f"Content after update: '{db_knowledge_item.content[:100] if db_knowledge_item.content else 'None'}...'")

            result['error'] = "Scraped content was empty after cleaning"
            return result

        result['content_scraped'] = True
        logger.info(f"Successfully scraped content for knowledge item: {knowledge_item_id}")

        # Store embeddings with metadata
        metadata = {
            'source_type': db_knowledge_item.source_type,
            'video_id': str(db_knowledge_item.video_id) if db_knowledge_item.video_id else None
        }

        # Add title for arxiv papers
        if db_knowledge_item.source_type == 'arxiv-no-link':
            metadata['title'] = db_knowledge_item.content.split('\n')[0] if db_knowledge_item.content else ""

        success = store_embeddings_with_metadata(
            project_id=str(db_knowledge_item.project_id),
            text=cleaned_content,
            source_url=db_knowledge_item.source_url,
            video_id=str(db_knowledge_item.video_id) if db_knowledge_item.video_id else None,
            embedding_model="qdrant_bm25",  # Use qdrant_bm25 to match existing vector dimensions
            metadata=metadata
        )

        if success:
            # Update status to completed
            db_knowledge_item.processing_status = "completed"
            db_knowledge_item.processed_at = datetime.now().isoformat()
            db_knowledge_item.embedding_model = "qdrant_bm25"
            db.add(db_knowledge_item)
            db.commit()

            result['status'] = 'success'
            result['embeddings_stored'] = True
            logger.info(f"Successfully stored embeddings for knowledge item: {knowledge_item_id}")
        else:
            # Update status to failed
            logger.info(f"Updating knowledge item {knowledge_item_id} status to 'failed' (embeddings failed)")
            logger.info(f"Current status before update: {db_knowledge_item.processing_status}")
            logger.info(f"Current content before update: '{db_knowledge_item.content[:100] if db_knowledge_item.content else 'None'}...'")

            db_knowledge_item.processing_status = "failed"
            db.add(db_knowledge_item)
            db.commit()
            db.refresh(db_knowledge_item)

            logger.info(f"Updated knowledge item {knowledge_item_id} status to: {db_knowledge_item.processing_status}")
            logger.info(f"Content after update: '{db_knowledge_item.content[:100] if db_knowledge_item.content else 'None'}...'")

            result['error'] = "Failed to store embeddings"
            logger.error(f"Failed to store embeddings for knowledge item: {knowledge_item_id}")

        return result

    except Exception as e:
        db.rollback()
        error_msg = f"Error scraping sources for knowledge item {knowledge_item_id}: {e}"
        logger.error(error_msg)
        result['error'] = error_msg

        # Update status to failed on error
        try:
            logger.info(f"Updating knowledge item {knowledge_item_id} status to 'failed' (exception)")
            logger.info(f"Current status before update: {db_knowledge_item.processing_status if 'db_knowledge_item' in locals() else 'N/A'}")
            logger.info(f"Current content before update: '{db_knowledge_item.content[:100] if 'db_knowledge_item' in locals() and db_knowledge_item.content else 'N/A'}...'")

            db_knowledge_item.processing_status = "failed"
            db.add(db_knowledge_item)
            db.commit()
            db.refresh(db_knowledge_item)

            logger.info(f"Updated knowledge item {knowledge_item_id} status to: {db_knowledge_item.processing_status}")
            logger.info(f"Content after update: '{db_knowledge_item.content[:100] if db_knowledge_item.content else 'None'}...'")
        except Exception as update_error:
            logger.error(f"Failed to update knowledge item status during exception handling: {update_error}")
            pass  # Ignore errors during cleanup

        return result
    finally:
        db.close()

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
        
        # Store embeddings using default Qdrant BM25 model
        # from backend.services.rag import store_embeddings_with_metadata
        logger.info(f"Storing embeddings for knowledge item: {knowledge_item_id} using Qdrant BM25 model")
        from backend.services.rag_llama_index import store_embeddings_with_metadata
        success = store_embeddings_with_metadata(
            project_id=project_id,
            text=content,
            source_url=source_url,
            video_id=video_id,
            embedding_model="qdrant_bm25"
        )
        
        if success:
            # Update knowledge item status to completed
            crud.update_knowledge_item_status(
                db, knowledge_uuid,
                processing_status="completed",
                embedding_model="qdrant_bm25"
            )
            result['status'] = 'success'
            logger.info(f"Successfully stored embeddings for knowledge item: {knowledge_item_id}")
        else:
            # Update knowledge item status to failed
            crud.update_knowledge_item_status(
                db, knowledge_uuid,
                processing_status="failed",
                embedding_model="qdrant_bm25"
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
                embedding_model="qdrant_bm25"
            )
        except Exception:
            pass  # Ignore errors during cleanup
        
        return result
    finally:
        db.close()

@app.task(bind=True)
def summarize_transcript_task(self, video_id: str, project_id: str, transcript: str) -> dict:
    """
    Background task to summarize video transcript using Gemini Flash 2.0 model.

    Args:
        video_id: Video ID to update with summary
        project_id: Project ID for getting prompt context
        transcript: Transcript text to summarize

    Returns:
        dict: Result with status, video_id, and summary details
    """
    db: Session = SessionLocal()
    result = {
        'status': 'failed',
        'video_id': video_id,
        'summary_generated': False,
        'error': None
    }
    
    try:
        # Get video and project for context
        from uuid import UUID
        video_uuid = UUID(video_id)
        db_video = crud.get_video(db, video_id)
        
        if not db_video:
            error_msg = f"Video not found: {video_id}"
            logger.error(error_msg)
            result['error'] = error_msg
            return result
        
        # Get project for prompt context
        video_description = ""
        if db_video.project_id:
            db_project = crud.get_project(db, db_video.project_id)
            if db_project and db_project.prompt_context:
                        video_description = db_project.description
        
        # Update video summary processing status to processing
        db_video.summary_processing_status = "processing"
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        # Initialize Gemini model
        gemini_model = init_chat_model(
            model="gemini-2.0-flash-exp",
            model_provider="google-genai",
            temperature=0.1
        )

        # Get formatted summary prompt
        summary_prompt = get_summary_prompt(video_description, transcript)

        # Generate summary using Gemini
        response = gemini_model.invoke([
            HumanMessage(content=summary_prompt)
        ])
        
        summary = response.content if hasattr(response, 'content') else ""
        
        if summary:
            # Update video with summary
            db_video.summary = summary
            db_video.summary_processing_status = "completed"
            from datetime import datetime
            db_video.summary_processed_at = datetime.now().isoformat()
            db.add(db_video)
            db.commit()
            
            result['status'] = 'success'
            result['summary_generated'] = True
            result['summary_length'] = len(summary)
            logger.info(f"Successfully generated summary for video: {video_id}")
        else:
            error_msg = "No summary generated by Gemini"
            logger.error(error_msg)
            result['error'] = error_msg
            
            # Update video summary processing status to failed
            db_video.summary_processing_status = "failed"
            db.add(db_video)
            db.commit()
        
        return result
        
    except Exception as e:
        db.rollback()
        error_msg = f"Error summarizing transcript for video {video_id}: {e}"
        logger.error(error_msg)
        result['error'] = error_msg
        
        # Update video summary processing status to failed on error
        try:
            db_video.summary_processing_status = "failed"
            db.add(db_video)
            db.commit()
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
    from backend.services.youtube_info import get_video_info

    results = {
        'total': len(video_urls),
        'successful': 0,
        'partial_success': 0,
        'failed': 0,
        'results': []
    }

    for video_url in video_urls:
        try:
            # Get YouTube ID from URL for consistency
            video_info = get_video_info(video_url)
            if not video_info:
                results['failed'] += 1
                results['results'].append({
                    'url': video_url,
                    'status': 'failed',
                    'error': 'Invalid YouTube URL'
                })
                continue

            youtube_id = video_info['youtube_id']
            result = process_video_task.apply_async(args=[youtube_id, project_id]).get()

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

def detect_arxiv_pattern(content: str) -> bool:
    """
    Detect if content represents an arxiv paper based on academic formatting patterns.

    Args:
        content: The content/title to analyze

    Returns:
        bool: True if content matches arxiv paper pattern
    """
    import re

    # Convert to lowercase for pattern matching
    content_lower = content.lower()

    # Look for academic paper patterns:
    # 1. Title followed by author names (multiple names separated by commas)
    # 2. "from" followed by institution names
    # 3. Numbers indicating affiliations (like 1,2,3)

    # Pattern 1: Multiple author names followed by "from" and institutions
    author_pattern = r'[a-zA-Z\s,]+\s+from\s+[a-zA-Z\s,]+'

    # Pattern 2: Affiliation numbers (1,2,3 style)
    affiliation_pattern = r'\d{1,2},\s*\d{1,2}'

    # Pattern 3: Common academic institution keywords
    institution_keywords = [
        'university', 'institute', 'laboratory', 'lab', 'college', 'school',
        'department', 'center', 'research', 'academy', 'technical', 'technology'
    ]

    # Check for author + institution pattern
    if re.search(author_pattern, content, re.IGNORECASE):
        return True

    # Check for affiliation numbers
    if re.search(affiliation_pattern, content):
        return True

    # Check for institution keywords
    for keyword in institution_keywords:
        if keyword in content_lower:
            return True

    # Check for common academic paper formatting patterns
    # Look for patterns like "Author1, Author2, Author3 from Institution"
    if ',' in content and 'from' in content_lower:
        # Count commas (indicating multiple authors)
        comma_count = content.count(',')
        if comma_count >= 2:  # At least 3 parts (title, author1, author2)
            return True

    return False

def determine_source_type(url: Optional[str], resource_type: str, content: str = "") -> str:
    """
    Determine the source_type based on URL domain and resource type.

    Args:
        url: The URL of the resource
        resource_type: The resource type from LLM (paper, article, etc.)
        content: The content/title for additional pattern detection

    Returns:
        str: The determined source_type for the KnowledgeItem
    """
    if not url:
        # For resources without URLs, check if it's an arxiv paper pattern
        if resource_type == "arxiv-no-link" or detect_arxiv_pattern(content):
            return 'arxiv-no-link'
        # Otherwise use the resource_type directly
        return resource_type

    try:
        domain = urlparse(url).netloc.lower()

        # Specialized domains that get specific types
        if 'arxiv.org' in domain:
            return 'paper'
        elif 'github.com' in domain:
            return 'tool'
        elif 'huggingface.co' in domain:
            return 'tool'
        elif 'pypi.org' in domain:
            return 'tool'
        elif 'npmjs.com' in domain:
            return 'tool'
        elif 'tensorflow.org' in domain or 'pytorch.org' in domain:
            return 'documentation'
        elif 'kaggle.com' in domain:
            return 'tutorial'
        elif 'medium.com' in domain or 'dev.to' in domain:
            return 'article'
        elif 'wikipedia.org' in domain:
            return 'article'
        elif 'youtube.com' in domain or 'youtu.be' in domain:
            return 'video'
        else:
            # For other domains, use the resource_type from LLM
            return resource_type
    except Exception:
        # If URL parsing fails, use the resource_type
        return resource_type

def parse_llm_json_response(response_text: str) -> list:
    """
    Parse JSON response from LLM with robust fallback methods.

    Args:
        response_text: Raw text response from LLM

    Returns:
        list: Parsed JSON array

    Raises:
        ValueError: If all parsing attempts fail
    """
    import re

    # First try direct JSON parsing
    try:
        resources = json.loads(response_text)
        logger.info("Successfully parsed JSON directly")
        return resources
    except json.JSONDecodeError:
        logger.warning("Direct JSON parsing failed, trying alternative methods...")

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
    if json_match:
        logger.info(f"Found JSON in markdown code block: '{json_match.group(1)[:200]}...'")
        try:
            resources = json.loads(json_match.group(1))
            logger.info("Successfully extracted JSON from markdown code block")
            return resources
        except json.JSONDecodeError as e2:
            logger.warning(f"Failed to parse JSON from code block: {e2}")

    # Try to find JSON array directly in the text
    json_match = re.search(r'(\[.*\])', response_text, re.DOTALL)
    if json_match:
        logger.info(f"Found JSON array in text: '{json_match.group(1)[:200]}...'")
        try:
            resources = json.loads(json_match.group(1))
            logger.info("Successfully extracted JSON array from text")
            return resources
        except json.JSONDecodeError as e3:
            logger.warning(f"Failed to parse JSON array from text: {e3}")

    # Last resort: try to clean and parse
    cleaned_text = re.sub(r'[^\[\]{}"a-zA-Z0-9\s:,._/-]', '', response_text)
    logger.info(f"Trying cleaned text: '{cleaned_text[:200]}...'")
    try:
        resources = json.loads(cleaned_text)
        logger.info("Successfully parsed cleaned JSON")
        return resources
    except json.JSONDecodeError as e4:
        error_msg = f"All JSON parsing attempts failed. Raw response: {response_text[:500]}..."
        logger.error(error_msg)
        raise ValueError(error_msg)

@app.task(bind=True)
def extract_resources_task(self, video_id: str, project_id: str, llm_model: str = "gemini") -> dict:
    """
    Background task to extract resources from video description using LLM.

    Args:
        video_id: Video ID to extract resources from
        project_id: Project ID to associate resources with
        llm_model: LLM model to use ("ollama" or "gemini", default: "gemini")

    Returns:
        dict: Result with status and extracted resources details
    """
    db: Session = SessionLocal()
    result = {
        'status': 'failed',
        'video_id': video_id,
        'resources_extracted': 0,
        'error': None
    }

    try:
        # Get video from database
        from uuid import UUID
        video_uuid = UUID(video_id)
        db_video = crud.get_video(db, video_id)

        if not db_video:
            error_msg = f"Video not found: {video_id}"
            logger.error(error_msg)
            result['error'] = error_msg
            return result

        # Check if video has description
        if not db_video.description:
            error_msg = f"No description available for video: {video_id}"
            logger.warning(error_msg)
            result['error'] = error_msg
            result['status'] = 'success'  # Not an error, just no resources to extract
            return result

        # Initialize LLM model based on selection
        if llm_model == "ollama":
            model = init_chat_model(
                model="gemma3:270m",
                model_provider="ollama",
                temperature=0.1
            )
        elif llm_model == "gemini":
            # Import and initialize Gemini model directly to ensure proper API key usage
            from backend.config import settings
            from langchain_google_genai import ChatGoogleGenerativeAI

            model = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.1
            )
        else:
            # Default to gemini
            from backend.config import settings
            from langchain_google_genai import ChatGoogleGenerativeAI

            model = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.1
            )

        # Get resource extraction prompt
        extraction_prompt = get_resource_extraction_prompt(db_video.description)

        # Extract resources using LLM
        response = model.invoke([
            HumanMessage(content=extraction_prompt)
        ])

        response_text = response.content if hasattr(response, 'content') else ""

        # Debug logging
        logger.info(f"LLM response type: {type(response)}")
        logger.info(f"LLM response has content attr: {hasattr(response, 'content')}")
        if hasattr(response, 'content'):
            logger.info(f"LLM response content length: {len(response.content) if response.content else 0}")
            logger.info(f"LLM response content preview: {response.content[:500] if response.content else 'EMPTY'}")

        if not response_text:
            error_msg = "No response from LLM for resource extraction"
            logger.error(error_msg)
            result['error'] = error_msg
            return result

        # Parse JSON response with improved error handling
        resources = None
        try:
            # Clean the response text first
            response_text = response_text.strip()
            logger.info(f"Raw LLM response (first 1000 chars): '{response_text[:1000]}...'")

            # Check if response is empty
            if not response_text:
                error_msg = "LLM returned empty response - no resources to extract"
                logger.warning(error_msg)
                result['status'] = 'success'
                result['resources_extracted'] = 0
                return result

            # Parse JSON using the dedicated function
            resources = parse_llm_json_response(response_text)

            # Validate that we got a list
            if not isinstance(resources, list):
                error_msg = f"LLM response is not a valid JSON array, got {type(resources)}. Raw response: {response_text[:500]}..."
                logger.error(error_msg)
                result['error'] = error_msg
                return result

            logger.info(f"Successfully parsed {len(resources)} resources from LLM response")

            # Validate that the list is not empty
            if len(resources) == 0:
                logger.warning("LLM returned empty resources array - this is expected for some videos")
                result['status'] = 'success'
                result['resources_extracted'] = 0
                return result

        except ValueError as e:
            error_msg = f"JSON parsing failed: {e}"
            logger.error(error_msg)
            result['error'] = error_msg
            return result
        except Exception as e:
            error_msg = f"Unexpected error during JSON parsing: {e}"
            logger.error(error_msg)
            result['error'] = error_msg
            return result

        # Process each extracted resource
        created_resources = []
        for resource in resources:
            try:
                logger.info(f"Processing resource: {resource}")

                title = resource.get('title', '').strip()
                url = resource.get('url')
                resource_type = resource.get('resource_type', 'other')

                logger.info(f"Extracted - title: '{title}', url: '{url}', type: '{resource_type}'")

                # Skip resources without titles
                if not title:
                    logger.warning(f"Skipping resource with empty title: {resource}")
                    continue

                # Clean URL if provided
                if url:
                    url = url.strip()
                    if not url.startswith(('http://', 'https://')):
                        url = f"https://{url}"

                # Determine source_type based on URL domain and content pattern detection
                source_type = determine_source_type(url, resource_type, title)

                # Check if knowledge item already exists to prevent duplicates
                from uuid import UUID
                project_uuid = UUID(project_id)
                video_uuid = UUID(video_id)

                existing_item = db.query(models.KnowledgeItem).filter(
                    models.KnowledgeItem.project_id == project_uuid,
                    models.KnowledgeItem.video_id == video_uuid,
                    models.KnowledgeItem.content == title,
                    models.KnowledgeItem.source_type == source_type,
                    models.KnowledgeItem.source_url == (url or "")
                ).first()

                if existing_item:
                    logger.info(f"Knowledge item already exists for resource: {title} (ID: {existing_item.id})")
                    created_resources.append({
                        'id': str(existing_item.id),
                        'title': title,
                        'url': url,
                        'source_type': source_type,
                        'status': 'existing'
                    })
                    continue

                # Validate that we have content before creating knowledge item
                if not title or not title.strip():
                    logger.warning(f"Skipping knowledge item creation for resource with empty title: {resource}")
                    continue

                # Create knowledge item
                knowledge_item = crud.create_knowledge_item(db, schemas.KnowledgeItemCreate(
                    project_id=project_id,
                    video_id=video_id,
                    content=title,  # Use title as content for now
                    source_url=url or "",  # Empty string if no URL
                    source_type=source_type,
                    processing_status='pending',  # Will be processed by other tasks
                    embedding_model=llm_model,
                    task_id=self.request.id
                ))

                created_resources.append({
                    'id': str(knowledge_item.id),
                    'title': title,
                    'url': url,
                    'source_type': source_type
                })

                logger.info(f"Created knowledge item for resource: {title}")

            except Exception as resource_error:
                logger.warning(f"Failed to process resource: {resource_error}")
                continue

        # Update result
        result['status'] = 'success'
        result['resources_extracted'] = len(created_resources)
        result['resources'] = created_resources

        logger.info(f"Successfully extracted {len(created_resources)} resources from video: {video_id}")

        return result

    except Exception as e:
        db.rollback()
        error_msg = f"Error extracting resources from video {video_id}: {e}"
        logger.error(error_msg)
        result['error'] = error_msg
        return result
    finally:
        db.close()

# Configure Celery with improved process management
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,

    # Worker process management
    worker_prefetch_multiplier=1,  # Prevent worker from prefetching too many tasks
    task_acks_late=True,  # Tasks are acknowledged after completion
    worker_max_tasks_per_child=25,  # Restart worker after 25 tasks to prevent memory leaks
    worker_max_memory_per_child=400000,  # Increased to 400MB for memory-intensive embedding tasks

    # Task execution settings
    task_reject_on_worker_lost=True,  # Reject tasks when worker is lost
    worker_cancel_long_running_tasks_on_connection_loss=True,  # Cancel long-running tasks on connection loss

    # Queue management
    worker_empty_queue_ttl=300,  # Remove empty queues after 5 minutes
    worker_disable_rate_limits=True,  # Disable rate limits for immediate task processing
    task_default_rate_limit=None,  # No default rate limiting

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_cache_max=1000,  # Maximum cached results

    # Concurrency and pool settings
    worker_concurrency=1,  # Changed to 1 - only one task runs at a time
    worker_pool_restarts=True,  # Allow pool restarts

    # Logging and monitoring
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(task_name)s[%(task_id)s]: %(message)s',

    # Cleanup settings
    worker_cleanup_interval=300,  # Cleanup every 5 minutes
)

if __name__ == '__main__':
    app.start()
