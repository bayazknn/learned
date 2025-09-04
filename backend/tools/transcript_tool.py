from typing import List, Optional, Dict, Any
from langchain_core.tools import tool
from backend.services.youtube_transcript import extract_transcript
from backend import crud, schemas
from backend.database import SessionLocal

@tool
def transcript_tool(project_id: str, video_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Retrieve transcript text for videos in a specific project.
    If video_ids are provided, only retrieve transcripts for those specific videos.
    
    Args:
        project_id: The project ID to retrieve transcripts for
        video_ids: Optional list of specific video IDs to retrieve transcripts for
        
    Returns:
        Dictionary containing transcripts with video IDs as keys and transcript text as values
    """
    db = SessionLocal()
    try:
        # Get videos for the project
        if video_ids:
            # Get specific videos by their IDs
            videos = []
            for video_id in video_ids:
                video = crud.get_video(db, video_id)
                if video:
                    videos.append(video)
        else:
            # Get all videos for the project
            videos = crud.get_videos_by_project(db, project_id)
        
        transcripts = {}
        for video in videos:
            try:
                # Extract YouTube video ID from URL or use stored video ID
                # youtube_video_id = video.youtube_id if hasattr(video, 'youtube_id') else video.id
                # Get video URL for transcript extraction
                # video_url = video.url if hasattr(video, 'url') else f"https://www.youtube.com/watch?v={youtube_video_id}"
                # transcript_text = extract_transcript(video_url)
                
                
                transcripts[str(video.id)] = {
                    "video_title": video.title,
                    "transcript": video.transcript,
                    "video_url": video.url
                }
            except Exception as e:
                # Skip videos that fail transcript retrieval
                continue
        
        return {
            "project_id": project_id,
            "total_videos": len(videos),
            "transcripts_found": len(transcripts),
            "transcripts": transcripts
        }
        
    finally:
        db.close()
