"use client"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Bot, Loader2 } from "lucide-react"

interface LoadingIndicatorProps {
  isLoading: boolean
  messages?: any[]
}

export function LoadingIndicator({ isLoading, messages = [] }: LoadingIndicatorProps) {
  if (!isLoading) return null

  // Always show loading indicator when isLoading is true
  // The empty assistant message will be replaced by streaming content

  return (
    <div className="flex gap-3 justify-start">
      <Avatar className="h-8 w-8 flex-shrink-0">
        <AvatarFallback className="bg-primary text-primary-foreground">
          <Bot className="h-4 w-4" />
        </AvatarFallback>
      </Avatar>
      <div className="bg-muted rounded-lg p-3">
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm text-muted-foreground">Thinking...</span>
        </div>
      </div>
    </div>
  )
}
