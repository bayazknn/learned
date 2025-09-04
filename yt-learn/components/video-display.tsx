"use client"

import { useState, useEffect, useCallback, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Play, Clock, Eye, ExternalLink, FileText, Link, Loader2, RefreshCw, ArrowLeft, Globe, Plus } from "lucide-react"
import { toast } from "sonner"

import { AddVideo } from "@/components/add-video"
import { VideoGridSkeleton, VideoListSkeleton } from "@/components/ui/video-skeleton"
import {
  formatDuration,
  formatViews,
  formatUploadDate,
  getSourceIcon,
  isVideoProcessing,
  extractVideoId
} from "@/lib/video-utils"

interface VideoSource {
  id: string
  sourceUrl: string
  sourceType: string
  content: string
}

interface Video {
  id: string
  title: string
  description: string
  thumbnailUrl: string | null
  duration: number | null
  views: number | null
  uploadDate: string | null
  url: string
  transcript: string | null
  sources: VideoSource[]
  processing_status?: string // Processing status from backend
  tags?: string[] // Optional field for YouTube tags
}

interface VideoDisplayProps {
  projectId?: string | null
  onRefreshRequest?: () => void
}

const VIDEO_API_BASE_URL = "http://localhost:8000/api/videos/"

// Dynamic polling interval with exponential backoff
const getPollInterval = (attemptCount: number): number => {
  const baseInterval = 5000; // Start with 5 seconds
  const maxInterval = 30000; // Cap at 30 seconds
  const backoffMultiplier = 1.5;

  const interval = baseInterval * Math.pow(backoffMultiplier, Math.min(attemptCount, 10));
  return Math.min(interval, maxInterval);
}

export function VideoDisplay({ projectId, onRefreshRequest }: VideoDisplayProps) {
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null)
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [scrapingSources, setScrapingSources] = useState<Set<string>>(new Set())


  const fetchVideos = useCallback(async () => {
    if (!projectId) return;
    
    try {
      setLoading(true)
      const response = await fetch(`${VIDEO_API_BASE_URL}project/${projectId}`)
      console.log('Fetch response status:', response.status)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      
      // Only update if videos have actually changed to prevent unnecessary re-renders
      setVideos(prevVideos => {
        const videosChanged = JSON.stringify(prevVideos) !== JSON.stringify(data);
        return videosChanged ? data : prevVideos;
      })
      
      setError(null)
      return data

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch videos')
      console.error('Error fetching videos:', err)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [projectId])

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchVideos()
    if (onRefreshRequest) {
      onRefreshRequest()
    }
  }

  useEffect(() => {
    fetchVideos()
  }, [projectId, fetchVideos])

  const handleVideoSelect = (video: Video) => {
    setSelectedVideo(video)
  }

  // Memoized source icon component
  const renderSourceIcon = useCallback((type: string) => {
    const iconName = getSourceIcon(type)
    const IconComponent = iconName === "Link" ? Link : FileText
    return <IconComponent className="h-4 w-4" />
  }, [])

  // Memoized values for performance
  const hasProcessingVideos = useMemo(() =>
    videos.some(video => isVideoProcessing(video)),
    [videos]
  )

  const videoId = useMemo(() =>
    selectedVideo ? extractVideoId(selectedVideo.url) : null,
    [selectedVideo]
  )

  // Polling mechanism for video updates - optimized for better UX and efficiency
  useEffect(() => {
    if (!projectId || !hasProcessingVideos) return;

    let pollCount = 0;
    const maxPolls = 20; // Reduced from 30 to 20 attempts
    let consecutiveErrors = 0;
    const maxConsecutiveErrors = 3; // Reduced from 5 to 3

    const pollInterval = setInterval(() => {
      pollCount++;
      console.log(`Polling for video updates... (attempt ${pollCount}/${maxPolls})`);

      // Stop polling after max attempts
      if (pollCount >= maxPolls) {
        console.log('Stopping polling after maximum attempts reached');
        clearInterval(pollInterval);
        return;
      }

      fetchVideos().then((updatedVideos: Video[] | undefined) => {
        if (updatedVideos) {
          consecutiveErrors = 0; // Reset error counter on success

          // Check if all videos are completed
          const stillProcessing = updatedVideos.some((v: Video) => isVideoProcessing(v));
          if (!stillProcessing) {
            console.log('All videos completed, stopping polling');
            clearInterval(pollInterval);
            return;
          }

          if (selectedVideo) {
            // Update selected video if it exists in the updated data
            const updatedSelectedVideo = updatedVideos.find((v: Video) => v.id === selectedVideo.id);
            if (updatedSelectedVideo) {
              setSelectedVideo(updatedSelectedVideo);
            }
          }
        } else {
          consecutiveErrors++;
          if (consecutiveErrors >= maxConsecutiveErrors) {
            console.warn(`Too many consecutive errors (${consecutiveErrors}), stopping polling`);
            clearInterval(pollInterval);
          }
        }
      }).catch((error) => {
        consecutiveErrors++;
        console.error('Error during polling:', error);
        if (consecutiveErrors >= maxConsecutiveErrors) {
          console.warn(`Too many consecutive errors (${consecutiveErrors}), stopping polling`);
          clearInterval(pollInterval);
        }
      });
    }, getPollInterval(pollCount)); // Dynamic interval based on attempt count

    return () => clearInterval(pollInterval);
  }, [projectId, hasProcessingVideos, fetchVideos, selectedVideo]);

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">Loading Videos...</h3>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <div className="text-center">
          <Play className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">Error Loading Videos</h3>
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>Try Again</Button>
        </div>
      </div>
    )
  }

  if (!projectId) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <div className="text-center">
          <Play className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No Project Selected</h3>
          <p className="text-muted-foreground">Select a project from the sidebar to view its videos</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {selectedVideo ? (
        // Video Detail View
        <div className="flex-1 flex flex-col">
          {/* Video Header */}
          <div className="p-6 border-b border-border">
            <div className="flex items-center justify-between mb-4">
              <Button
                variant="ghost"
                onClick={() => setSelectedVideo(null)}
                aria-label="Back to video collection"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Videos
              </Button>
            </div>
            <h1 className="text-2xl font-semibold text-foreground mb-2">{selectedVideo.title}</h1>
            <div className="flex items-center gap-4 text-sm text-muted-foreground" role="group" aria-label="Video metadata">
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" aria-hidden="true" />
                <span aria-label={`Duration: ${formatDuration(selectedVideo.duration)}`}>
                  {formatDuration(selectedVideo.duration)}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <Eye className="h-4 w-4" aria-hidden="true" />
                <span aria-label={`${formatViews(selectedVideo.views)} views`}>
                  {formatViews(selectedVideo.views)} views
                </span>
              </div>
              <span aria-label={`Uploaded: ${formatUploadDate(selectedVideo.uploadDate)}`}>
                {formatUploadDate(selectedVideo.uploadDate)}
              </span>
            </div>
          </div>

          {/* Video Content */}
          <div className="flex-1 p-6">
            <Tabs defaultValue="video" className="h-full flex flex-col">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="video">Video</TabsTrigger>
                <TabsTrigger value="description">Description</TabsTrigger>
                <TabsTrigger value="transcript">Transcript</TabsTrigger>
                <TabsTrigger value="sources">Sources</TabsTrigger>
              </TabsList>

              <TabsContent value="video" className="flex-1 mt-4">
                <Card className="aspect-video bg-muted flex items-center justify-center">
                  {videoId ? (
                    <iframe
                      src={`https://www.youtube.com/embed/${videoId}`}
                      title={`Watch ${selectedVideo.title}`}
                      className="w-full h-full rounded-lg"
                      allowFullScreen
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      loading="lazy"
                    />
                  ) : (
                    <div className="text-center">
                      <Play className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground mb-4">Unable to load video player</p>
                      <Button asChild variant="outline">
                        <a
                          href={selectedVideo.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label={`Watch ${selectedVideo.title} on YouTube`}
                        >
                          <ExternalLink className="h-4 w-4 mr-2" />
                          Watch on YouTube
                        </a>
                      </Button>
                    </div>
                  )}
                </Card>
              </TabsContent>

              <TabsContent value="description" className="flex-1 mt-4">
                <Card className="p-6 h-full">
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-medium text-foreground mb-2">Description</h3>
                      <p className="text-muted-foreground leading-relaxed">{selectedVideo.description}</p>
                    </div>
                    <div>
                      <h3 className="font-medium text-foreground mb-2">Tags</h3>
                      <div className="flex flex-wrap gap-2">
                        {selectedVideo.tags && selectedVideo.tags.map((tag) => (
                          <Badge key={tag} variant="secondary">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
              </TabsContent>

              <TabsContent value="transcript" className="flex-1 mt-4">
                <Card className="p-6 h-full">
                  <h3 className="font-medium text-foreground mb-4">Video Transcript</h3>
                  <ScrollArea className="h-full">
                    {selectedVideo.transcript ? (
                      <p className="text-muted-foreground leading-relaxed whitespace-pre-wrap">
                        {selectedVideo.transcript}
                      </p>
                    ) : (
                      <div className="text-center py-8">
                        <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                        <p className="text-muted-foreground">
                          {isVideoProcessing(selectedVideo) ? 'Transcript is being processed...' : 'No transcript available'}
                        </p>
                      </div>
                    )}
                  </ScrollArea>
                </Card>
              </TabsContent>

              <TabsContent value="sources" className="flex-1 mt-4">
                <Card className="p-6 h-full">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-medium text-foreground">
                      RAG Sources ({selectedVideo.sources?.length || 0})
                    </h3>
                  </div>
                  <ScrollArea className="h-full">
                    <div className="space-y-4">
                      {selectedVideo.sources && selectedVideo.sources.length > 0 ? (
                        selectedVideo.sources.map((source) => (
                          <Card key={source.id} className="p-4 hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex items-center gap-3">
                                {renderSourceIcon(source.sourceType)}
                                <div>
                                  <Badge variant="secondary" className="text-xs capitalize">
                                    {source.sourceType}
                                  </Badge>
                                  <p className="text-xs text-muted-foreground mt-1 truncate max-w-xs">
                                    {source.sourceUrl}
                                  </p>
                                </div>
                              </div>
                              <div className="flex gap-1">
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="sm"
                                  disabled={scrapingSources.has(source.id)}
                                  onClick={async (e) => {
                                    e.preventDefault()
                                    e.stopPropagation()

                                    // Add source to scraping set
                                    setScrapingSources(prev => new Set(prev).add(source.id))

                                    try {
                                      const response = await fetch('http://localhost:8000/api/scrape/source', {
                                        method: 'POST',
                                        headers: {
                                          'Content-Type': 'application/json',
                                        },
                                        body: JSON.stringify({
                                          id: source.id
                                        })
                                      })

                                      if (response.ok) {
                                        const result = await response.json()
                                        console.log('Source scraping completed:', result)
                                        toast.success(`Successfully scraped content from ${source.sourceType} source`)
                                        // Refresh videos to show updated sources
                                        await fetchVideos()
                                      } else {
                                        const errorData = await response.json().catch(() => ({}))
                                        toast.error(`Failed to scrape ${source.sourceType} source: ${errorData.detail || response.statusText}`)
                                        console.error('Source scraping failed:', response.statusText)
                                      }
                                    } catch (error) {
                                      toast.error(`Error scraping ${source.sourceType} source: ${error instanceof Error ? error.message : 'Unknown error'}`)
                                      console.error('Error scraping source:', error)
                                    } finally {
                                      // Remove source from scraping set
                                      setScrapingSources(prev => {
                                        const newSet = new Set(prev)
                                        newSet.delete(source.id)
                                        return newSet
                                      })
                                    }
                                  }}
                                  aria-label={`Scrape additional content from ${source.sourceType} source`}
                                  title="Scrape additional content from this source"
                                >
                                  {scrapingSources.has(source.id) ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                  ) : (
                                    <Globe className="h-4 w-4" />
                                  )}
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  asChild
                                  aria-label={`Open ${source.sourceType} source`}
                                >
                                  <a
                                    href={source.sourceUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                  >
                                    <ExternalLink className="h-4 w-4" />
                                  </a>
                                </Button>
                              </div>
                            </div>
                            <div className="space-y-2">
                              <h4 className="text-sm font-medium text-foreground">Content Preview</h4>
                              <p className="text-sm text-muted-foreground leading-relaxed line-clamp-3">
                                {source.content || 'No content preview available'}
                              </p>
                            </div>
                          </Card>
                        ))
                      ) : (
                        <div className="text-center py-12">
,
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      ) : (
        // Video Grid View
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-semibold text-foreground mb-2">Video Collection</h1>
              <p className="text-muted-foreground">Manage and explore your YouTube videos</p>
            </div>
            <div className="flex gap-2">
              <AddVideo projectId={projectId} onVideoAdded={fetchVideos} />
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button
                variant={viewMode === "grid" ? "default" : "outline"}
                size="sm"
                onClick={() => setViewMode("grid")}
              >
                Grid
              </Button>
              <Button
                variant={viewMode === "list" ? "default" : "outline"}
                size="sm"
                onClick={() => setViewMode("list")}
              >
                List
              </Button>
            </div>
          </div>

          {loading ? (
            viewMode === "grid" ? (
              <VideoGridSkeleton count={6} />
            ) : (
              <VideoListSkeleton count={6} />
            )
          ) : videos.length === 0 ? (
            <div className="text-center py-12">
              <Play className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No Videos Yet</h3>
              <p className="text-muted-foreground mb-4">Start by adding your first YouTube video to this project</p>
              <Button>Add Video</Button>
            </div>
          ) : (
            <div className={viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" : "space-y-4"}>
              {videos.map((video) => (
                <Card
                  key={video.id}
                  className="overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => handleVideoSelect(video)}
                  role="button"
                  tabIndex={0}
                  aria-label={`Select video: ${video.title}`}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      handleVideoSelect(video)
                    }
                  }}
                >
                  {viewMode === "grid" ? (
                    <>
                      <div className="aspect-video relative">
                        <img
                          src={video.thumbnailUrl || "/placeholder.svg"}
                          alt={video.title}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                        <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded">
                          {formatDuration(video.duration)}
                        </div>
                      </div>
                      <div className="p-4">
                        <h3 className="font-medium text-foreground mb-2 line-clamp-2">{video.title}</h3>
                        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{video.description}</p>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Eye className="h-3 w-3" aria-hidden="true" />
                            <span>{formatViews(video.views)}</span>
                          </div>
                          <span>{formatUploadDate(video.uploadDate)}</span>
                        </div>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {video.tags && video.tags.length > 0 && (
                            video.tags.length <= 2 ? (
                              video.tags.map((tag) => (
                                <Badge key={tag} variant="secondary" className="text-xs">
                                  {tag}
                                </Badge>
                              ))
                            ) : (
                              <>
                                {video.tags.slice(0, 2).map((tag) => (
                                  <Badge key={tag} variant="secondary" className="text-xs">
                                    {tag}
                                  </Badge>
                                ))}
                                <Badge variant="secondary" className="text-xs">
                                  +{video.tags.length - 2} more
                                </Badge>
                              </>
                            )
                          )}
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="flex gap-4 p-4">
                      <div className="w-32 h-20 relative flex-shrink-0">
                        <img
                          src={video.thumbnailUrl || "/placeholder.svg"}
                          alt={video.title}
                          className="w-full h-full object-cover rounded"
                          loading="lazy"
                        />
                        <div className="absolute bottom-1 right-1 bg-black/80 text-white text-xs px-1 py-0.5 rounded">
                          {formatDuration(video.duration)}
                        </div>
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-foreground mb-1">{video.title}</h3>
                        <p className="text-sm text-muted-foreground mb-2 line-clamp-2">{video.description}</p>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Eye className="h-3 w-3" aria-hidden="true" />
                            <span>{formatViews(video.views)}</span>
                          </div>
                          <span>{formatUploadDate(video.uploadDate)}</span>
                          <span>{(video.sources?.length || 0)} sources</span>
                        </div>
                      </div>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
