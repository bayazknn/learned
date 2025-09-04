/**
 * Utility functions for video display formatting and processing
 */

/**
 * Formats duration from seconds to MM:SS format
 * @param seconds - Duration in seconds
 * @returns Formatted duration string
 */
export const formatDuration = (seconds: number | null): string => {
  if (!seconds || seconds <= 0) return "0:00"
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

/**
 * Formats view count with appropriate suffixes (K, M)
 * @param views - Number of views
 * @returns Formatted view count string
 */
export const formatViews = (views: number | null): string => {
  if (!views || views <= 0) return "0"
  if (views >= 1000000) {
    return `${(views / 1000000).toFixed(1)}M`
  } else if (views >= 1000) {
    return `${(views / 1000).toFixed(1)}K`
  }
  return views.toString()
}

/**
 * Formats upload date from YYYYMMDD to YYYY-MM-DD format
 * @param date - Date string in YYYYMMDD format
 * @returns Formatted date string
 */
export const formatUploadDate = (date: string | null): string => {
  if (!date) return "Unknown date"
  if (date.length === 8) {
    return `${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}`
  }
  return date
}

/**
 * Gets the appropriate icon component for a source type
 * @param type - Source type
 * @returns Icon component
 */
export const getSourceIcon = (type: string) => {
  switch (type) {
    case "pdf":
      return "FileText"
    case "web":
      return "Link"
    case "article":
      return "FileText"
    case "transcript":
      return "FileText"
    default:
      return "FileText"
  }
}

/**
 * Checks if a video is still processing based on processing status
 * @param video - Video object
 * @returns Boolean indicating if video is processing
 */
export const isVideoProcessing = (video: { transcript: string | null; sources?: any[]; processing_status?: string }): boolean => {
  // If processing_status is available, use it as the primary indicator
  if (video.processing_status) {
    return video.processing_status === 'pending' || video.processing_status === 'processing'
  }

  // Fallback to checking transcript and sources for backward compatibility
  return !video.transcript || !video.sources || video.sources.length === 0
}

/**
 * Safely extracts YouTube video ID from URL
 * @param url - YouTube URL
 * @returns Video ID or null if invalid
 */
export const extractVideoId = (url: string): string | null => {
  if (!url) return null

  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
    /youtube\.com\/v\/([^&\n?#]+)/
  ]

  for (const pattern of patterns) {
    const match = url.match(pattern)
    if (match && match[1]) {
      return match[1]
    }
  }

  return null
}
