import logging
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

logger = logging.getLogger(__name__)

def extract_transcript(video_url: str) -> Optional[str]:
    """
    Extract transcript from a YouTube video using youtube_transcript_api.
    
    Args:
        video_url: YouTube video URL
        
    Returns:
        str: Extracted transcript text, or None if not available
    """
    try:
        # Extract video ID from URL
        video_id = _extract_video_id(video_url)
        if not video_id:
            logger.error(f"Could not extract video ID from URL: {video_url}")
            return None
        
        # Get transcript using youtube_transcript_api
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id, languages=['en'])
        
        # Combine all transcript segments into a single string
        transcript_text = ' '.join([segment.text for segment in transcript_list])
        
        logger.info(f"Successfully extracted transcript for video: {video_url}")
        return transcript_text
        
    except TranscriptsDisabled:
        logger.warning(f"Transcripts are disabled for video: {video_url}")
        return None
    except NoTranscriptFound:
        logger.warning(f"No English transcript found for video: {video_url}")
        return None
    except VideoUnavailable:
        logger.error(f"Video is unavailable: {video_url}")
        return None
    except Exception as e:
        logger.error(f"Error extracting transcript from {video_url}: {e}")
        return None

def _extract_video_id(video_url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    import re
    
    # Regular expression patterns for different YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([^&]+)',  # youtube.com/watch?v=VIDEO_ID
        r'(?:youtube\.com\/embed\/)([^?]+)',     # youtube.com/embed/VIDEO_ID
        r'(?:youtube\.com\/v\/)([^?]+)',         # youtube.com/v/VIDEO_ID
        r'(?:youtu\.be\/)([^?]+)',               # youtu.be/VIDEO_ID
        r'(?:youtube\.com\/watch\?.*v=)([^&]+)', # youtube.com/watch?other_params&v=VIDEO_ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, video_url)
        if match:
            return match.group(1)
    
    return None
