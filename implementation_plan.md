# Implementation Plan

Replace current yt-dlp based YouTube transcript extraction with youtube_transcript_api while maintaining video information extraction using yt-dlp. Archive existing YouTube service files and create new simplified implementations that maintain backward compatibility with the existing codebase.

The current YouTube service implementation uses yt-dlp for both transcript extraction and video information, but the transcript extraction is not working reliably. The solution is to replace transcript extraction with youtube_transcript_api while keeping yt-dlp for video metadata extraction. The new implementation should be simpler than the current complex error handling and retry logic.

## Types  
No type system changes required as function signatures will remain the same.

The implementation will maintain the existing function signatures:
- `extract_transcript(video_url: str) -> Optional[str]` - Returns transcript text or None
- `get_video_info(video_url: str) -> Optional[dict]` - Returns video metadata dict or None

## Files
Single sentence describing file modifications.

Detailed breakdown:
- **New files to be created**: 
  - `backend/services/youtube_transcript.py` - New transcript service using youtube_transcript_api
  - `backend/services/youtube_info.py` - New video info service using yt-dlp (simplified)

- **Existing files to be modified**:
  - `backend/tasks/background.py` - Update imports to use new services
  - `backend/api/endpoints/videos.py` - Update imports to use new services

- **Files to be archived**:
  - `backend/services/youtube.py` -> `archive/services/youtube.py`
  - `backend/services/youtube_api.py` -> `archive/services/youtube_api.py`

- **Configuration file updates**: None required

## Functions
Single sentence describing function modifications.

Detailed breakdown:
- **New functions**:
  - `extract_transcript(video_url: str) -> Optional[str]` in `youtube_transcript.py` - Uses youtube_transcript_api to extract English transcripts
  - `get_video_info(video_url: str) -> Optional[dict]` in `youtube_info.py` - Uses yt-dlp to extract basic video metadata

- **Modified functions**: None (maintaining same signatures)

- **Removed functions**: All functions from archived files will be replaced

## Classes
Single sentence describing class modifications.

Detailed breakdown:
- **New classes**: None (functional approach preferred for simplicity)

- **Modified classes**: None

- **Removed classes**: YouTubeAPIClient class from youtube_api.py will be archived

## Dependencies
Single sentence describing dependency modifications.

No new dependencies required as youtube_transcript_api is already installed. The existing yt-dlp dependency will continue to be used for video information extraction.

## Testing
Single sentence describing testing approach.

Basic smoke testing will be performed to ensure the new services work with the existing codebase. No formal test files will be created initially, but the implementation should be verified through manual testing of the video processing workflow.

## Implementation Order
Single sentence describing the implementation sequence.

Numbered steps showing the logical order of changes to minimize conflicts and ensure successful integration:

1. Create new youtube_transcript.py service with youtube_transcript_api implementation
2. Create new youtube_info.py service with simplified yt-dlp implementation  
3. Update background.py to import from new services instead of old ones
4. Update videos.py API endpoint to import from new services instead of old ones
5. Move old youtube.py and youtube_api.py to archive directory
6. Test the complete workflow to ensure backward compatibility

The implementation will proceed in this order to ensure that at each step, the system remains functional and any issues can be caught early.
