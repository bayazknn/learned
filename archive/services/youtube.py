import logging
import asyncio
import webvtt
import requests
from typing import Optional
from functools import wraps
from .youtube_api import YouTubeAPIClient

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3, delay=2, backoff=2):
    """
    Decorator to retry a function on failure with exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Failed after {max_retries} attempts: {e}")
                        raise
                    sleep_time = delay * (backoff ** (retries - 1))
                    logger.warning(f"Attempt {retries} failed: {e}. Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def run_async(coro):
    """Run async coroutine in synchronous context."""
    return asyncio.run(coro)

@retry_on_failure(max_retries=3, delay=2, backoff=2)
def extract_transcript(video_url: str) -> Optional[str]:
    """
    Extract transcript from a YouTube video using YouTube Data API v3.
    Prioritizes English subtitles only to minimize requests and avoid rate limiting.
    
    Args:
        video_url: YouTube video URL
        
    Returns:
        str: Extracted transcript text, or None if not available
    """
    async def _async_extract():
        async with YouTubeAPIClient() as client:
            return await client.extract_transcript(video_url)
    
    try:
        transcript = run_async(_async_extract())
        if transcript:
            logger.info(f"Successfully extracted transcript using YouTube API for video: {video_url}")
        else:
            logger.warning(f"No transcript found using YouTube API for video: {video_url}")
        return transcript
    except Exception as e:
        logger.error(f"Error extracting transcript from {video_url} using YouTube API: {e}")
        return None

def _extract_transcript_fallback(video_url: str) -> Optional[str]:
    """
    Fallback method for transcript extraction when signature extraction fails.
    Uses different yt-dlp options to bypass signature issues.
    """
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],  # Only English to minimize requests
        'subtitlesformat': 'vtt',
        'skip_download': True,
        'quiet': True,
        # Different extractor options for fallback
        'extractor_args': {
            'youtube': {
                'skip': ['dash', 'hls'],
                'player_client': ['ios', 'android_embedded']
            }
        },
        # Rate limiting options
        'sleep_subtitles': 3,
        'sleep_interval': 3,
        'max_sleep_interval': 15,
        # Try different user agent
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # Check for manually created English subtitles
            if 'subtitles' in info and 'en' in info['subtitles']:
                subtitle_url = info['subtitles']['en'][0]['url']
                transcript = _download_subtitle(subtitle_url)
                if transcript:
                    return transcript
            
            # Check for automatic English captions
            if 'automatic_captions' in info and 'en' in info['automatic_captions']:
                subtitle_url = info['automatic_captions']['en'][0]['url']
                transcript = _download_subtitle(subtitle_url)
                if transcript:
                    return transcript
            
            logger.warning(f"No English subtitles found in fallback for video: {video_url}")
            return None
            
    except Exception as e:
        logger.error(f"Fallback error extracting transcript from {video_url}: {e}")
        return None

def _download_subtitle(subtitle_url: str, max_retries: int = 3, initial_delay: float = 2.0, backoff_factor: float = 2.0) -> Optional[str]:
    """
    Download and parse subtitle content from URL using proper VTT parsing.
    Handles HTTP 429 (Too Many Requests) errors with exponential backoff retry logic.
    
    Args:
        subtitle_url: URL to subtitle file
        max_retries: Maximum number of retry attempts for 429 errors
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for exponential backoff
        
    Returns:
        str: Cleaned transcript text, or None if parsing fails
    """
    import tempfile
    import os
    
    retries = 0
    delay = initial_delay
    
    while retries <= max_retries:
        try:
            response = requests.get(subtitle_url)
            
            # Handle 429 Too Many Requests specifically
            if response.status_code == 429:
                if retries < max_retries:
                    logger.warning(f"HTTP 429 Too Many Requests for {subtitle_url}. Retrying in {delay}s... (Attempt {retries + 1}/{max_retries})")
                    time.sleep(delay)
                    delay *= backoff_factor  # Exponential backoff
                    retries += 1
                    continue
                else:
                    logger.error(f"HTTP 429 Too Many Requests for {subtitle_url} after {max_retries} retries")
                    return None
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            # Create a temporary file to parse with webvtt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.vtt', delete=False) as temp_file:
                temp_file.write(response.text)
                temp_file_path = temp_file.name
            
            try:
                # Parse VTT file using webvtt library
                transcript_lines = []
                for caption in webvtt.read(temp_file_path):
                    # Clean the text by removing any remaining HTML tags and extra whitespace
                    clean_text = caption.text.strip()
                    if clean_text:
                        transcript_lines.append(clean_text)
                
                # Remove duplicate lines that can occur in auto-generated subtitles
                unique_lines = []
                seen_lines = set()
                for line in transcript_lines:
                    if line not in seen_lines:
                        seen_lines.add(line)
                        unique_lines.append(line)
                
                return ' '.join(unique_lines) if unique_lines else None
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                if retries < max_retries:
                    logger.warning(f"HTTP 429 Too Many Requests for {subtitle_url}. Retrying in {delay}s... (Attempt {retries + 1}/{max_retries})")
                    time.sleep(delay)
                    delay *= backoff_factor  # Exponential backoff
                    retries += 1
                    continue
                else:
                    logger.error(f"HTTP 429 Too Many Requests for {subtitle_url} after {max_retries} retries")
                    return None
            logger.error(f"HTTP error downloading subtitle from {subtitle_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error downloading or parsing subtitle from {subtitle_url}: {e}")
            return None
    
    return None

@retry_on_failure(max_retries=2, delay=1, backoff=2)
def get_video_info(video_url: str) -> Optional[dict]:
    """
    Get basic video information (title, ID, description, etc.) using YouTube Data API v3.
    
    Args:
        video_url: YouTube video URL
        
    Returns:
        dict: Video information including id, title, description, and url
    """
    async def _async_get_info():
        async with YouTubeAPIClient() as client:
            return await client.get_video_info(video_url)
    
    try:
        video_info = run_async(_async_get_info())
        if video_info:
            logger.info(f"Successfully retrieved video info using YouTube API for: {video_url}")
        else:
            logger.warning(f"Failed to retrieve video info using YouTube API for: {video_url}")
        return video_info
    except Exception as e:
        logger.error(f"Error getting video info for {video_url} using YouTube API: {e}")
        return None

def _get_video_info_fallback(video_url: str) -> Optional[dict]:
    """
    Fallback method for getting video info when signature extraction fails.
    """
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        # Rate limiting options
        'sleep_interval': 4,
        'max_sleep_interval': 12,
        # Different extractor options for fallback
        'extractor_args': {
            'youtube': {
                'skip': ['dash', 'hls'],
                'player_client': ['ios', 'android_embedded']
            }
        },
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            return {
                'youtube_id': info['id'],
                'title': info['title'],
                'description': info.get('description'),
                'url': video_url,
                'duration': info.get('duration'),
                'upload_date': info.get('upload_date'),
                'view_count': info.get('view_count'),
                'thumbnail': info.get('thumbnail')
            }
            
    except Exception as e:
        logger.error(f"Fallback error getting video info for {video_url}: {e}")
        return None
