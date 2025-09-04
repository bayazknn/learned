"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { MessageSquare, Sparkles, Settings, Plus } from "lucide-react"

interface ChatSettings {
  model: "gemini" | "ollama"
  streaming: boolean
  maxTokens: number
  temperature: number
}

interface ChatHeaderProps {
  threadId: string | null
  selectedVideoId: string | null
  settings: ChatSettings
  isSettingsOpen: boolean
  setIsSettingsOpen: (open: boolean) => void
  setSettings: React.Dispatch<React.SetStateAction<ChatSettings>>
  onNewChat: () => void
}

export function ChatHeader({
  threadId,
  selectedVideoId,
  settings,
  isSettingsOpen,
  setIsSettingsOpen,
  setSettings,
  onNewChat
}: ChatHeaderProps) {
  return (
    <div className="border-b border-border flex-shrink-0">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">AI Assistant</span>
          <Badge variant="secondary">
            <Sparkles className="h-3 w-3 mr-1" />
            RAG Enabled
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onNewChat}
            className="h-8 px-2"
          >
            <Plus className="h-3 w-3 mr-1" />
            New Chat
          </Button>

          <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 px-2">
                <Settings className="h-3 w-3" />
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Chat Settings</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Model</label>
                  <Select
                    value={settings.model}
                    onValueChange={(value: "gemini" | "ollama") =>
                      setSettings(prev => ({ ...prev, model: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gemini">Gemini (Recommended)</SelectItem>
                      <SelectItem value="ollama">Ollama (Local)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-medium">Temperature</label>
                  <Input
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    value={settings.temperature}
                    onChange={(e) =>
                      setSettings(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))
                    }
                  />
                </div>

                <div>
                  <label className="text-sm font-medium">Max Tokens</label>
                  <Input
                    type="number"
                    min="256"
                    max="8192"
                    step="256"
                    value={settings.maxTokens}
                    onChange={(e) =>
                      setSettings(prev => ({ ...prev, maxTokens: parseInt(e.target.value) }))
                    }
                  />
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {selectedVideoId && (
        <p className="text-xs text-muted-foreground mt-1">
          Context: Current video and project sources
        </p>
      )}

      {threadId && (
        <p className="text-xs text-muted-foreground mt-1">
          Thread: {threadId.slice(0, 8)}...
        </p>
      )}
    </div>
  )
}
