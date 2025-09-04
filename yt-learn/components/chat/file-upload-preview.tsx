"use client"

import { Button } from "@/components/ui/button"
import { FileText, Trash2 } from "lucide-react"

interface FileUploadPreviewProps {
  uploadedFiles: File[]
  onRemoveFile: (index: number) => void
}

export function FileUploadPreview({ uploadedFiles, onRemoveFile }: FileUploadPreviewProps) {
  if (uploadedFiles.length === 0) return null

  return (
    <div className="bg-background border-t border-border py-2">
      <div className="flex flex-wrap gap-2 px-4">
        {uploadedFiles.map((file, index) => (
          <div key={index} className="flex items-center gap-2 bg-muted rounded px-2 py-1">
            <FileText className="h-3 w-3" />
            <span className="text-xs">{file.name}</span>
            <Button
              variant="ghost"
              size="sm"
              className="h-4 w-4 p-0"
              onClick={() => onRemoveFile(index)}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  )
}
