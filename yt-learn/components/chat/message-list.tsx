"use client"

import { ScrollArea } from "@/components/ui/scroll-area"
import { Bot } from "lucide-react"
import { ChatMessage } from "./chat-message"
import { LoadingIndicator } from "./loading-indicator"

interface MessageListProps {
  messages: any[]
  isLoading: boolean
  error: string | null
  onCopy: (content: string, messageId: string) => void
  copiedMessageId: string | null
  messagesEndRef: React.RefObject<HTMLDivElement | null>
}

export function MessageList({
  messages,
  isLoading,
  error,
  onCopy,
  copiedMessageId,
  messagesEndRef
}: MessageListProps) {
  return (
    <div className="flex-1 min-h-0">
      <ScrollArea className="h-full">
        <div className="p-3 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-8">
              <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">Welcome to AI Chat</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Ask questions about your videos, get summaries, or explore your knowledge base.
              </p>
            </div>
          )}

          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              onCopy={onCopy}
              copiedMessageId={copiedMessageId}
            />
          ))}

          <LoadingIndicator isLoading={isLoading} messages={messages} />

          {/* Invisible element to scroll to */}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
    </div>
  )
}
