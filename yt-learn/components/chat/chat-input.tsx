"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Upload, Send, Loader2 } from "lucide-react"

interface ChatInputProps {
  input: string
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onSubmit: (e: React.FormEvent) => void
  onKeyDown: (e: React.KeyboardEvent) => void
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void
  isLoading: boolean
  uploadedFiles: File[]
  fileInputRef: React.RefObject<HTMLInputElement | null>
}

export function ChatInput({
  input,
  onInputChange,
  onSubmit,
  onKeyDown,
  onFileUpload,
  isLoading,
  uploadedFiles,
  fileInputRef
}: ChatInputProps) {
  return (
    <div className="bg-background border-t border-border">
      <form onSubmit={onSubmit} className="p-4 space-y-3">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={onInputChange}
            onKeyDown={onKeyDown}
            placeholder="Ask about your videos..."
            disabled={isLoading}
            className="flex-1"
          />

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*,.pdf,.txt,.md"
            onChange={onFileUpload}
            className="hidden"
          />

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
          >
            <Upload className="h-4 w-4" />
          </Button>

          <Button
            type="submit"
            disabled={isLoading || (!input?.trim() && uploadedFiles.length === 0)}
            size="sm"
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>

        <QuickActions onInputChange={onInputChange} isLoading={isLoading} />
      </form>
    </div>
  )
}

interface QuickActionsProps {
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  isLoading: boolean
}

function QuickActions({ onInputChange, isLoading }: QuickActionsProps) {
  const actions = [
    { label: "Summarize video", value: "Summarize the key points from this video" },
    { label: "Project overview", value: "What are the main topics covered in my project?" },
    { label: "Find related", value: "Find related videos on this topic" }
  ]

  return (
    <div className="flex flex-wrap gap-1">
      {actions.map((action, index) => (
        <Button
          key={index}
          type="button"
          variant="ghost"
          size="sm"
          className="h-6 px-2 text-xs"
          onClick={() => onInputChange({ target: { value: action.value } } as React.ChangeEvent<HTMLInputElement>)}
          disabled={isLoading}
        >
          {action.label}
        </Button>
      ))}
    </div>
  )
}
