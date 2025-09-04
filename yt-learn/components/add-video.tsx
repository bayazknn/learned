"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { toast } from "sonner"

interface AddVideoProps {
  projectId: string
  onVideoAdded: () => any
}

const VIDEO_API_URL = "http://localhost:8000/api/videos/"

export function AddVideo({ projectId, onVideoAdded }: AddVideoProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [videoUrl, setVideoUrl] = useState("")
  const [isAdding, setIsAdding] = useState(false)

  const pollForProcessingCompletion = async (videoId: string) => {
    const maxAttempts = 15; // Reduced from 20 to 15 attempts for faster completion
    let consecutiveErrors = 0;
    const maxConsecutiveErrors = 3;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const statusResponse = await fetch(`${VIDEO_API_URL}${videoId}/processing-status`);
        if (statusResponse.ok) {
          const videoData = await statusResponse.json();
          consecutiveErrors = 0; // Reset error counter on success

          if (videoData.processing_status === 'completed') {
            toast.success("Video processing completed successfully");
            return true;
          } else if (videoData.processing_status === 'failed') {
            toast.warning("Video processing failed. Some metadata may be incomplete.");
            return false;
          }
          // If still processing, continue polling
        } else {
          consecutiveErrors++;
          if (consecutiveErrors >= maxConsecutiveErrors) {
            console.warn(`Too many consecutive errors (${consecutiveErrors}), stopping polling`);
            break;
          }
        }
      } catch (error) {
        consecutiveErrors++;
        console.error("Error checking processing status:", error);
        if (consecutiveErrors >= maxConsecutiveErrors) {
          console.warn(`Too many consecutive errors (${consecutiveErrors}), stopping polling`);
          break;
        }
      }

      // Dynamic polling interval with exponential backoff
      const pollInterval = Math.min(2000 + (attempt * 1000), 10000); // Start at 2s, max at 10s
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    toast.warning("Video processing is taking longer than expected. Some metadata may still be processing.");
    return false;
  }

  const handleAddVideo = async () => {
    if (!videoUrl.trim()) {
      toast.error("Please enter a valid YouTube URL")
      return
    }

    try {
      setIsAdding(true)
      const response = await fetch(VIDEO_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: videoUrl.trim(), project_id: projectId }),
      })

      if (!response.ok) {
        throw new Error("Failed to add video")
      }

      const videoData = await response.json();
      
      setVideoUrl("")
      setIsDialogOpen(false)
      toast.success("Video added successfully. Processing metadata...")
      
      // Start polling for processing completion in the background
      pollForProcessingCompletion(videoData.id).then(() => {
        onVideoAdded(); // Refresh the video list when processing is complete
      });
      
    } catch (error) {
      console.error(error)
      toast.error("An error occurred while adding the video")
    } finally {
      setIsAdding(false)
    }
  }

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogTrigger asChild>
        <Button>
          Add Video
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Add YouTube Video</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="video-url">YouTube Video URL</Label>
            <Input
              id="video-url"
              type="url"
              placeholder="https://www.youtube.com/watch?v=example"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              disabled={isAdding}
            />
          </div>
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setIsDialogOpen(false)} disabled={isAdding}>
            Cancel
          </Button>
          <Button onClick={handleAddVideo} disabled={isAdding}>
            {isAdding ? "Adding..." : "Add Video"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
