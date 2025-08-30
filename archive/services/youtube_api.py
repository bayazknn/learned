import httpx
import logging
import asyncio
import json
from typing import Optional, Dict, List
from urllib.parse import urlparse, parse_qs
from backend.config import settings

logger = logging.getLogger(__name__)

class YouTubeAPIClient:
    """Async client for YouTube Data API v3 with rate limiting and error handling."""
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
        self.rate_limit_semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    def _extract_video_id(self, video_url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats."""
        try:
            parsed_url = urlparse(video_url)
            if parsed_url.hostname in ('youtube.com', 'www.youtube.com', 'm.youtube.com'):
                if parsed_url.path == '/watch':
                    return parse_qs(parsed_url.query).get('v', [None])[0]
                elif parsed_url.path.startswith('/embed/'):
                    return parsed_url.path.split('/')[2]
                elif parsed_url.path.startswith('/v/'):
                    return parsed_url.path.split('/')[2]
            elif parsed_url.hostname == 'youtu.be':
                return parsed_url.path[1:]
            return None
        except Exception as e:
            logger.error(f"Error extracting video ID from {video_url}: {e}")
            return None
            
    async def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Make async HTTP request to YouTube API with rate limiting and retries."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                async with self.rate_limit_semaphore:
                    response = await self.client.get(
                        f"{self.BASE_URL}/{endpoint}",
                        params={**params, "key": self.api_key}
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 403:
                        error_data = response.json()
                        if 'quotaExceeded' in str(error_data):
                            logger.error("YouTube API quota exceeded")
                            return None
                        elif 'accessNotConfigured' in str(error_data):
                            logger.error("YouTube API not enabled for this project")
                            return None
                    elif response.status_code == 429:
                        logger.warning(f"Rate limited, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    
                    response.raise_for_status()
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e}")
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            except Exception as e:
                logger.error(f"Error making YouTube API request: {e}")
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
                
        return None
        
    async def get_video_info(self, video_url: str) -> Optional[Dict]:
        """Get video information using YouTube Data API v3."""
        video_id = self._extract_video_id(video_url)
        if not video_id:
            logger.error(f"Could not extract video ID from URL: {video_url}")
            return None
            
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": video_id
        }
        
        data = await self._make_request("videos", params)
        if not data or not data.get('items'):
            return None
            
        video_data = data['items'][0]
        snippet = video_data.get('snippet', {})
        content_details = video_data.get('contentDetails', {})
        statistics = video_data.get('statistics', {})
        
        return {
            'youtube_id': video_id,
            'title': snippet.get('title'),
            'description': snippet.get('description'),
            'url': video_url,
            'duration': self._parse_duration(content_details.get('duration')),
            'upload_date': snippet.get('publishedAt'),
            'view_count': int(statistics.get('viewCount', 0)),
            'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url') or 
                         snippet.get('thumbnails', {}).get('medium', {}).get('url') or 
                         snippet.get('thumbnails', {}).get('default', {}).get('url')
        }
        
    async def list_captions(self, video_url: str) -> List[Dict]:
        """List available caption tracks for a video."""
        video_id = self._extract_video_id(video_url)
        if not video_id:
            return []
            
        params = {
            "part": "snippet",
            "videoId": video_id
        }
        
        data = await self._make_request("captions", params)
        if not data or not data.get('items'):
            return []
            
        return data['items']
        
    async def extract_transcript(self, video_url: str) -> Optional[str]:
        """Extract transcript from video using yt-dlp as fallback since YouTube API captions require OAuth."""
        # YouTube Data API captions endpoint requires OAuth authentication
        # Fall back to yt-dlp implementation for now
        import yt_dlp
        
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'subtitlesformat': 'vtt',
            'skip_download': True,
            'quiet': True,
            'sleep_subtitles': 2,
            'sleep_interval': 5,
            'max_sleep_interval': 10,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                # Try manually created English subtitles
                if 'subtitles' in info and 'en' in info['subtitles']:
                    subtitle_url = info['subtitles']['en'][0]['url']
                    transcript = self._download_subtitle_direct(subtitle_url)
                    if transcript:
                        logger.info(f"Found manual English subtitles for video: {video_url}")
                        return transcript
                
                # Try automatic English captions
                if 'automatic_captions' in info and 'en' in info['automatic_captions']:
                    subtitle_url = info['automatic_captions']['en'][0]['url']
                    transcript = self._download_subtitle_direct(subtitle_url)
                    if transcript:
                        logger.info(f"Found auto-generated English subtitles for video: {video_url}")
                        return transcript
                
                logger.warning(f"No English subtitles found for video: {video_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting transcript from {video_url}: {e}")
            return None
            
    def _download_subtitle_direct(self, subtitle_url: str) -> Optional[str]:
        """Download subtitle content directly from URL."""
        try:
            import requests
            response = requests.get(subtitle_url)
            response.raise_for_status()
            return self._clean_transcript(response.text)
        except Exception as e:
            logger.error(f"Error downloading subtitle from {subtitle_url}: {e}")
            return None
        
    async def download_caption(self, caption_id: str, format: str = "vtt") -> Optional[str]:
        """Download caption content in specified format."""
        params = {
            "tfmt": format
        }
        
        try:
            async with self.rate_limit_semaphore:
                response = await self.client.get(
                    f"{self.BASE_URL}/captions/{caption_id}",
                    params={**params, "key": self.api_key},
                    headers={"Accept": "text/plain"}
                )
                
                if response.status_code == 200:
                    return response.text
                response.raise_for_status()
                
        except Exception as e:
            logger.error(f"Error downloading caption {caption_id}: {e}")
            return None
            
    def _parse_duration(self, duration: str) -> Optional[int]:
        """Parse ISO 8601 duration string to seconds."""
        if not duration:
            return None
            
        try:
            # Parse PT1H2M3S format
            import re
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, duration)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return hours * 3600 + minutes * 60 + seconds
            return None
        except Exception:
            return None
            
    def _clean_transcript(self, transcript: str) -> str:
        """Clean and format transcript text."""
        # Basic cleaning - remove excessive whitespace and normalize
        lines = transcript.strip().split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('WEBVTT') and not line.startswith('NOTE'):
                cleaned_lines.append(line)
                
        return ' '.join(cleaned_lines)
