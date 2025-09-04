"use client"

import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Bot, User, Copy, Check, FileText, Video } from "lucide-react"

interface Source {
  url: string
  content: string
  score: number
  title?: string
}

interface ChatMessageProps {
  message: any
  onCopy: (content: string, messageId: string) => void
  copiedMessageId: string | null
}

export function ChatMessage({ message, onCopy, copiedMessageId }: ChatMessageProps) {
  const isUser = message.role === "user"
  const isError = message.isError
  const sources = message.sources || []

  // Extract content from useChat message format
  const getMessageContent = () => {
    if (message.parts) {
      // useChat format with parts
      return message.parts
        .filter((part: any) => part.type === 'text')
        .map((part: any) => part.text)
        .join('')
    }
    // Fallback to direct content
    return message.content || ''
  }

  const content = getMessageContent()

  // Don't render empty assistant messages (streaming placeholders)
  if (!isUser && !isError && !content.trim()) {
    return null
  }

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className={isError ? "bg-destructive text-destructive-foreground" : "bg-primary text-primary-foreground"}>
            {isError ? (
              <span className="text-xs">⚠️</span>
            ) : (
              <Bot className="h-4 w-4" />
            )}
          </AvatarFallback>
        </Avatar>
      )}

      <div className={`max-w-[80%] ${isUser ? "order-first" : ""}`}>
        <div
          className={`rounded-lg p-3 ${
            isUser
              ? "bg-primary text-primary-foreground ml-auto"
              : isError
                ? "bg-destructive/10 border border-destructive/20"
                : "bg-muted"
          }`}
        >
          <div className="text-sm leading-relaxed whitespace-pre-wrap">
            {content}
          </div>

          {/* File attachments */}
          {message.experimental_attachments && (
            <div className="mt-2 space-y-1">
              {message.experimental_attachments.map((attachment: any, index: number) => (
                <div key={index} className="flex items-center gap-2 text-xs bg-background/50 rounded px-2 py-1">
                  <FileText className="h-3 w-3" />
                  <span>{attachment.name || "Attachment"}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Message Actions */}
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-2">
            {!isUser && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-xs"
                onClick={() => onCopy(content, message.id)}
              >
                {copiedMessageId === message.id ? (
                  <Check className="h-3 w-3" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
              </Button>
            )}
          </div>

          <span className="text-xs text-muted-foreground">
            {new Date(message.createdAt || Date.now()).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>

        {/* Sources */}
        {sources.length > 0 && (
          <div className="mt-2 p-2 bg-background/50 rounded border">
            <div className="flex items-center gap-1 mb-2">
              <Video className="h-3 w-3" />
              <span className="text-xs font-medium">Sources</span>
            </div>
            <div className="space-y-1">
              {sources.map((source: Source, index: number) => (
                <div key={index} className="text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-medium truncate flex-1">
                      {source.title || source.url}
                    </span>
                    <Badge variant="outline" className="text-xs ml-2">
                      {source.score?.toFixed(2) || "N/A"}
                    </Badge>
                  </div>
                  <p className="text-muted-foreground mt-1 line-clamp-2">
                    {source.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className="bg-secondary">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}
