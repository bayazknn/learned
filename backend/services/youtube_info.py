import logging
from typing import Optional
import yt_dlp

logger = logging.getLogger(__name__)

def get_video_info(video_url: str) -> Optional[dict]:
    """
    Get basic video information using yt-dlp.
    
    Args:
        video_url: YouTube video URL
        
    Returns:
        dict: Video information including:
            - youtube_id: Video ID
            - title: Video title
            - description: Video description
            - url: Original video URL
            - duration: Video duration in seconds
            - upload_date: Upload date string
            - view_count: Number of views
            - thumbnail: Thumbnail URL
            - channel: Channel name (if available)
            - channel_id: Channel ID (if available)
    """
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            return {
                'youtube_id': info['id'],
                'title': info.get('title', ''),
                'description': info.get('description', ''),
                'url': video_url,
                'duration': info.get('duration'),
                'upload_date': info.get('upload_date'),
                'view_count': info.get('view_count'),
                'thumbnail': info.get('thumbnail'),
                "channel": info.get('channel'),
                "channel_id": info.get('channel_id'),
            }
            
    except Exception as e:
        logger.error(f"Error getting video info for {video_url}: {e}")
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
