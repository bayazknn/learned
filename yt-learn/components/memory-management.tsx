"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Brain, Trash2, Calendar, Tag, Plus, Search, Edit, Filter } from "lucide-react"

interface Memory {
  id: string
  content: string
  source: string
  tags: string[]
  createdAt: Date
  importance: "low" | "medium" | "high"
}

export function MemoryManagement() {
  const [memories, setMemories] = useState<Memory[]>([
    {
      id: "1",
      content:
        "Machine learning requires proper data preprocessing including normalization, handling missing values, and feature scaling for optimal model performance.",
      source: "ML Tutorial Video",
      tags: ["machine-learning", "preprocessing", "data-science"],
      createdAt: new Date("2024-01-15"),
      importance: "high",
    },
    {
      id: "2",
      content:
        "React render props pattern allows sharing code between components by using a prop whose value is a function that returns a React element.",
      source: "React Patterns Video",
      tags: ["react", "patterns", "components"],
      createdAt: new Date("2024-01-12"),
      importance: "medium",
    },
    {
      id: "3",
      content:
        "Color theory fundamentals: complementary colors create contrast, analogous colors create harmony, and triadic colors provide vibrant balance.",
      source: "Design Principles Video",
      tags: ["design", "color-theory", "ui-ux"],
      createdAt: new Date("2024-01-10"),
      importance: "medium",
    },
  ])

  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingMemory, setEditingMemory] = useState<Memory | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [importanceFilter, setImportanceFilter] = useState<string>("all")

  const [newMemory, setNewMemory] = useState({
    content: "",
    source: "",
    tags: "",
    importance: "medium" as const,
  })

  const filteredMemories = memories.filter((memory) => {
    const matchesSearch =
      memory.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      memory.source.toLowerCase().includes(searchQuery.toLowerCase()) ||
      memory.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))

    const matchesImportance = importanceFilter === "all" || memory.importance === importanceFilter

    return matchesSearch && matchesImportance
  })

  const deleteMemory = (memoryId: string) => {
    setMemories(memories.filter((m) => m.id !== memoryId))
  }

  const createMemory = () => {
    if (!newMemory.content.trim()) return

    const memory: Memory = {
      id: Date.now().toString(),
      content: newMemory.content,
      source: newMemory.source || "Manual Entry",
      tags: newMemory.tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
      createdAt: new Date(),
      importance: newMemory.importance,
    }

    setMemories([memory, ...memories])
    setNewMemory({ content: "", source: "", tags: "", importance: "medium" })
    setIsCreateDialogOpen(false)
  }

  const editMemory = () => {
    if (!editingMemory || !editingMemory.content.trim()) return

    setMemories(memories.map((m) => (m.id === editingMemory.id ? editingMemory : m)))
    setIsEditDialogOpen(false)
    setEditingMemory(null)
  }

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case "high":
        return "bg-red-100 text-red-800 border-red-200"
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "low":
        return "bg-green-100 text-green-800 border-green-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-accent" />
          <span className="text-sm font-medium text-sidebar-foreground">Memory Bank</span>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm" className="bg-transparent">
              <Plus className="h-3 w-3 mr-1" />
              Add
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Memory</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="memory-content">Content</Label>
                <Textarea
                  id="memory-content"
                  value={newMemory.content}
                  onChange={(e) => setNewMemory({ ...newMemory, content: e.target.value })}
                  placeholder="Enter the information you want to remember..."
                  rows={4}
                />
              </div>
              <div>
                <Label htmlFor="memory-source">Source</Label>
                <Input
                  id="memory-source"
                  value={newMemory.source}
                  onChange={(e) => setNewMemory({ ...newMemory, source: e.target.value })}
                  placeholder="Video title, document name, etc."
                />
              </div>
              <div>
                <Label htmlFor="memory-tags">Tags (comma-separated)</Label>
                <Input
                  id="memory-tags"
                  value={newMemory.tags}
                  onChange={(e) => setNewMemory({ ...newMemory, tags: e.target.value })}
                  placeholder="react, tutorial, advanced"
                />
              </div>
              <div>
                <Label htmlFor="memory-importance">Importance</Label>
                <Select
                  value={newMemory.importance}
                  onValueChange={(value: any) => setNewMemory({ ...newMemory, importance: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={createMemory}>Create Memory</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="space-y-2 mb-4">
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8"
          />
        </div>
        <div className="flex gap-2">
          <Select value={importanceFilter} onValueChange={setImportanceFilter}>
            <SelectTrigger className="w-full">
              <div className="flex items-center gap-1">
                <Filter className="h-3 w-3" />
                <SelectValue />
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Importance</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="space-y-3">
            {filteredMemories.length === 0 ? (
              <div className="text-center py-8">
                <Brain className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground text-sm">
                  {searchQuery || importanceFilter !== "all"
                    ? "No memories match your filters"
                    : "No memories stored yet"}
                </p>
              </div>
            ) : (
              filteredMemories.map((memory) => (
                <Card key={memory.id} className="p-3">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={`text-xs ${getImportanceColor(memory.importance)}`}>
                        {memory.importance}
                      </Badge>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        {memory.createdAt.toLocaleDateString()}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => {
                          setEditingMemory({
                            ...memory,
                            tags: [...memory.tags],
                          })
                          setIsEditDialogOpen(true)
                        }}
                      >
                        <Edit className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 text-destructive hover:text-destructive"
                        onClick={() => deleteMemory(memory.id)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>

                  <p className="text-sm text-foreground mb-3 leading-relaxed">{memory.content}</p>

                  <div className="flex items-center justify-between mb-2">
                    <div className="text-xs text-muted-foreground">Source: {memory.source}</div>
                  </div>

                  {memory.tags.length > 0 && (
                    <div className="flex items-center gap-1">
                      <Tag className="h-3 w-3 text-muted-foreground" />
                      <div className="flex flex-wrap gap-1">
                        {memory.tags.map((tag) => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </Card>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Edit Memory Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Memory</DialogTitle>
          </DialogHeader>
          {editingMemory && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-memory-content">Content</Label>
                <Textarea
                  id="edit-memory-content"
                  value={editingMemory.content}
                  onChange={(e) => setEditingMemory({ ...editingMemory, content: e.target.value })}
                  rows={4}
                />
              </div>
              <div>
                <Label htmlFor="edit-memory-source">Source</Label>
                <Input
                  id="edit-memory-source"
                  value={editingMemory.source}
                  onChange={(e) => setEditingMemory({ ...editingMemory, source: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit-memory-tags">Tags (comma-separated)</Label>
                <Input
                  id="edit-memory-tags"
                  value={editingMemory.tags.join(", ")}
                  onChange={(e) =>
                    setEditingMemory({
                      ...editingMemory,
                      tags: e.target.value
                        .split(",")
                        .map((tag) => tag.trim())
                        .filter(Boolean),
                    })
                  }
                />
              </div>
              <div>
                <Label htmlFor="edit-memory-importance">Importance</Label>
                <Select
                  value={editingMemory.importance}
                  onValueChange={(value: any) => setEditingMemory({ ...editingMemory, importance: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={editMemory}>Save Changes</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
