"use client"

import { Button } from "@/components/ui/button"

interface ErrorDisplayProps {
  error: string | null
  onRetry?: () => void
}

export function ErrorDisplay({ error, onRetry }: ErrorDisplayProps) {
  if (!error) return null

  return (
    <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3">
      <p className="text-sm text-destructive">Error: {error}</p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="mt-2"
        >
          Retry
        </Button>
      )}
    </div>
  )
}
