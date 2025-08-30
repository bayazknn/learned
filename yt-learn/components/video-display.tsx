"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Play, Clock, Eye, ExternalLink, FileText, Link, Bookmark, Download, Loader2 } from "lucide-react"

import { AddVideo } from "@/components/add-video"
import { on } from "events"

interface VideoSource {
  id: string
  title: string
  url: string
  type: "pdf" | "web" | "article" | "transcript"
}

interface Video {
  id: string
  title: string
  description: string
  thumbnail_url: string | null
  duration: number | null
  views: number | null
  upload_date: string | null
  url: string
  transcript: string | null
  sources: VideoSource[]
  tags: string[]
}

interface VideoDisplayProps {
  projectId?: string | null
}

const VIDEO_API_BASE_URL = "http://localhost:8000/api/videos/"

export function VideoDisplay({ projectId }: VideoDisplayProps) {
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null)
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)


  const fetchVideos = async () => {
    if (!projectId) return;
    
    try {
      setLoading(true)
      const response = await fetch(`${VIDEO_API_BASE_URL}project/${projectId}`)
      console.log('Fetch response status:', response.status)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setVideos(data)
      setError(null)
      return

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch videos')
      console.error('Error fetching videos:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchVideos()
  }, [projectId])

  const handleVideoSelect = (video: Video) => {
    setSelectedVideo(video)
  }


  const getSourceIcon = (type: string) => {
    switch (type) {
      case "pdf":
        return <FileText className="h-4 w-4" />
      case "web":
        return <Link className="h-4 w-4" />
      default:
        return <FileText className="h-4 w-4" />
    }
  }

  // Helper function to format duration from seconds to MM:SS
  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return "0:00"
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  // Helper function to format view count
  const formatViews = (views: number | null): string => {
    if (!views) return "0"
    if (views >= 1000000) {
      return `${(views / 1000000).toFixed(1)}M`
    } else if (views >= 1000) {
      return `${(views / 1000).toFixed(1)}K`
    }
    return views.toString()
  }

  // Helper function to format upload date from YYYYMMDD to YYYY-MM-DD
  const formatUploadDate = (date: string | null): string => {
    if (!date) return "Unknown date"
    if (date.length === 8) {
      return `${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}`
    }
    return date
  }

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
              <Button variant="ghost" onClick={() => setSelectedVideo(null)}>
                ← Back to Videos
              </Button>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <Bookmark className="h-4 w-4 mr-2" />
                  Save
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
              </div>
            </div>
            <h1 className="text-2xl font-semibold text-foreground mb-2">{selectedVideo.title}</h1>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {formatDuration(selectedVideo.duration)}
              </div>
              <div className="flex items-center gap-1">
                <Eye className="h-4 w-4" />
                {formatViews(selectedVideo.views)} views
              </div>
              <span>{formatUploadDate(selectedVideo.upload_date)}</span>
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
                  {/* <div className="text-center">
                    <Play className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground mb-4">Video player would be embedded here</p>
                    <Button asChild>
                      <a href={selectedVideo.url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Watch on YouTube
                      </a>
                    </Button>
                  </div> */}
                  <iframe
                    src={`https://www.youtube.com/embed/${selectedVideo.id}`}
                    title={selectedVideo.title}
                    className="w-full h-full"
                    allowFullScreen
                  ></iframe>
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
                    <p className="text-muted-foreground leading-relaxed whitespace-pre-wrap">
                      {selectedVideo.transcript}
                    </p>
                  </ScrollArea>
                </Card>
              </TabsContent>

              <TabsContent value="sources" className="flex-1 mt-4">
                <Card className="p-6 h-full">
                  <h3 className="font-medium text-foreground mb-4">RAG Sources ({selectedVideo.sources && selectedVideo.sources.length})</h3>
                  <div className="space-y-3">
                    {selectedVideo.sources && selectedVideo.sources.map((source) => (
                      <div
                        key={source.id}
                        className="flex items-center justify-between p-3 border border-border rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          {getSourceIcon(source.type)}
                          <div>
                            <h4 className="font-medium text-foreground">{source.title}</h4>
                            <p className="text-sm text-muted-foreground capitalize">{source.type}</p>
                          </div>
                        </div>
                        <Button variant="ghost" size="sm" asChild>
                          <a href={source.url} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </Button>
                      </div>
                    ))}
                  </div>
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

          {videos.length === 0 ? (
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
                >
                  {viewMode === "grid" ? (
                    <>
                      <div className="aspect-video relative">
                        <img
                          src={video.thumbnail_url || "/placeholder.svg"}
                          alt={video.title}
                          className="w-full h-full object-cover"
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
                            <Eye className="h-3 w-3" />
                            <span>{formatViews(video.views)}</span>
                          </div>
                          <span>{formatUploadDate(video.upload_date)}</span>
                        </div>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {video.tags && (
                            <Badge key="more" variant="secondary" className="text-xs">
                              +{video.tags.length - 2} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="flex gap-4 p-4">
                      <div className="w-32 h-20 relative flex-shrink-0">
                        <img
                          src={video.thumbnail_url || "/placeholder.svg"}
                          alt={video.title}
                          className="w-full h-full object-cover rounded"
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
                            <Eye className="h-3 w-3" />
                            <span>{formatViews(video.views)}</span>
                          </div>
                          <span>{formatUploadDate(video.upload_date)}</span>
                          <span>{video.sources.length} sources</span>
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
