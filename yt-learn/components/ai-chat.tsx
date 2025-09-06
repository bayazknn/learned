"use client"

import type React from "react"
import { useState, useRef, useEffect, useCallback } from "react"
import { flushSync } from "react-dom"
import { toast } from "sonner"
import {
  ChatHeader,
  MessageList,
  ChatInput,
  FileUploadPreview
} from "./chat"

interface AIChatProps {
  projectId: string | null
  selectedVideoId: string | null
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: string
  parts: Array<{ type: 'text'; text: string }>
  sources?: any[]
  isError?: boolean
}

interface ChatSettings {
  model: "gemini" | "ollama"
  streaming: boolean
  maxTokens: number
  temperature: number
}

export function AIChat({ projectId, selectedVideoId }: AIChatProps) {
  const [threadId, setThreadId] = useState<string | null>(null)
  const [settings, setSettings] = useState<ChatSettings>({
    model: "gemini",
    streaming: true,
    maxTokens: 4096,
    temperature: 0.7
  })
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Manual input state
  const [input, setInput] = useState('')

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (messagesEndRef.current) {
      // Use requestAnimationFrame for better timing with DOM updates
      requestAnimationFrame(() => {
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({
            behavior: 'smooth',
            block: 'end'
          })
        }, 50) // Small delay to ensure content is rendered
      })
    }
  }, [messages])

  // Handle file upload
  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    setUploadedFiles(prev => [...prev, ...files])
    toast.success(`Uploaded ${files.length} file(s)`)
  }, [])

  // Remove uploaded file
  const removeFile = useCallback((index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }, [])

  // Copy message to clipboard
  const copyToClipboard = useCallback(async (content: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedMessageId(messageId)
      toast.success("Copied to clipboard")
      setTimeout(() => setCopiedMessageId(null), 2000)
    } catch (err) {
      toast.error("Failed to copy to clipboard")
    }
  }, [])

  // Create new chat thread
  const createNewThread = useCallback(() => {
    setThreadId(null)
    setMessages([])
    toast.success("Started new conversation")
  }, [])

  // Upload files to backend
  const uploadFiles = useCallback(async (files: File[]): Promise<string[]> => {
    const uploadedUrls: string[] = []

    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)

      try {
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          throw new Error(`Failed to upload ${file.name}`)
        }

        const result = await response.json()
        uploadedUrls.push(result.url)
      } catch (err) {
        console.error(`Error uploading ${file.name}:`, err)
        throw err
      }
    }

    return uploadedUrls
  }, [])

  // Custom submit handler to handle streaming responses
  const handleCustomSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()

    if (!input?.trim() && uploadedFiles.length === 0) return

    // Check if project is selected
    if (!projectId) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Please select a project before sending messages.',
        createdAt: new Date().toISOString(),
        parts: [{ type: 'text', text: 'Please select a project before sending messages.' }],
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
      toast.error('Please select a project first')
      return
    }

    setIsLoading(true)

    // Create assistant message placeholder
    const assistantMessageId = `assistant-${Date.now()}`

    try {
      // Upload files first if any
      let fileUrls: string[] = []
      if (uploadedFiles.length > 0) {
        fileUrls = await uploadFiles(uploadedFiles)
      }

      // Add user message to chat
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: input || "Please analyze the uploaded files",
        createdAt: new Date().toISOString(),
        parts: [{ type: 'text', text: input || "Please analyze the uploaded files" }]
      }
      setMessages(prev => [...prev, userMessage])

      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        createdAt: new Date().toISOString(),
        parts: [{ type: 'text', text: '' }],
        sources: []
      }
      setMessages(prev => [...prev, assistantMessage])

      // Make streaming API call to backend
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input || "Please analyze the uploaded files",
          thread_id: threadId,
          project_id: projectId,
          video_ids: selectedVideoId ? [selectedVideoId] : null,
          file_url: fileUrls.length > 0 ? fileUrls[0] : null,
          file_name: uploadedFiles.length > 0 ? uploadedFiles[0].name : null,
          file_type: uploadedFiles.length > 0 ? uploadedFiles[0].type : null,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`)
      }

      // Handle Server-Sent Events with improved streaming and forced updates
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let accumulatedContent = ''
      let sources: any[] = []
      let buffer = ''
      let updateCounter = 0

      if (reader) {
        try {
          while (true) {
            const { done, value } = await reader.read()
            if (done) {
              new Promise(resolve => setTimeout(resolve, 1));
              break
            }

            // Decode the chunk and add to buffer
            buffer += decoder.decode(value, { stream: true })

            // Process complete lines from buffer
            const lines = buffer.split('\n')
            buffer = lines.pop() || '' // Keep incomplete line in buffer

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6)) // Remove 'data: ' prefix

                  if (data.type === 'text') {
                    accumulatedContent += data.content

                    // Force immediate synchronous re-render
                    updateCounter++
                    flushSync(() => {
                      setMessages(prev => prev.map(msg =>
                        msg.id === assistantMessageId
                          ? {
                              ...msg,
                              content: accumulatedContent,
                              parts: [{ type: 'text', text: accumulatedContent }],
                              // Add a counter to force re-render even if content hasn't changed
                              _updateCounter: updateCounter
                            }
                          : msg
                      ))
                    })

                  } else if (data.type === 'sources') {
                    sources = data.sources
                    setMessages(prev => prev.map(msg =>
                      msg.id === assistantMessageId
                        ? { ...msg, sources }
                        : msg
                    ))
                  } else if (data.type === 'done') {
                    // Update thread ID if provided
                    if (data.thread_id && !threadId) {
                      setThreadId(data.thread_id)
                    }
                    break
                  } else if (data.type === 'error') {
                    throw new Error(data.content)
                  }
                } catch (parseError) {
                  console.warn('Failed to parse SSE data:', line, parseError)
                }
              }
            }
          }

          // Process any remaining data in buffer
          if (buffer.trim()) {
            const lines = buffer.split('\n')
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6))
                  if (data.type === 'text') {
                    accumulatedContent += data.content
                    updateCounter++
                    flushSync(() => {
                      setMessages(prev => prev.map(msg =>
                        msg.id === assistantMessageId
                          ? {
                              ...msg,
                              content: accumulatedContent,
                              parts: [{ type: 'text', text: accumulatedContent }],
                              _updateCounter: updateCounter
                            }
                          : msg
                      ))
                    })
                  }
                } catch (parseError) {
                  console.warn('Failed to parse remaining SSE data:', line, parseError)
                }
              }
            }
          }
        } finally {
          
          reader.releaseLock()
        }
      }

      // Clear input and files after successful submit
      setInput('')
      setUploadedFiles([])

    } catch (err: any) {
      console.error('Error in custom submit:', err)

      // Remove the placeholder assistant message and add error message
      setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId))

      // Create error message as chat message
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `I encountered an error: ${err.message || 'Unknown error occurred'}`,
        createdAt: new Date().toISOString(),
        parts: [{ type: 'text', text: `I encountered an error: ${err.message || 'Unknown error occurred'}` }],
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
      toast.error('Failed to send message')
    } finally {
      setIsLoading(false)
    }
  }, [input, uploadedFiles, threadId, projectId, selectedVideoId, uploadFiles])

  // Handle input change
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
  }, [])

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleCustomSubmit(e as any)
    }
  }, [handleCustomSubmit])

  return (
    <div className="h-full flex flex-col relative">
      <ChatHeader
        threadId={threadId}
        selectedVideoId={selectedVideoId}
        settings={settings}
        isSettingsOpen={isSettingsOpen}
        setIsSettingsOpen={setIsSettingsOpen}
        setSettings={setSettings}
        onNewChat={createNewThread}
      />

      <MessageList
        messages={messages}
        isLoading={isLoading}
        error={null}
        onCopy={copyToClipboard}
        copiedMessageId={copiedMessageId}
        messagesEndRef={messagesEndRef}
      />

      <FileUploadPreview
        uploadedFiles={uploadedFiles}
        onRemoveFile={removeFile}
      />

      <ChatInput
        input={input}
        onInputChange={handleInputChange}
        onSubmit={handleCustomSubmit}
        onKeyDown={handleKeyDown}
        onFileUpload={handleFileUpload}
        isLoading={isLoading}
        uploadedFiles={uploadedFiles}
        fileInputRef={fileInputRef}
      />
    </div>
  )
}
