"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "sonner"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Plus, Search, MoreVertical, Edit, Trash2, Folder, Video, Loader2 } from "lucide-react"
import { formatDate } from "@/lib/utils"



interface ProjectCreate {
  name: string
  description: string
  promptContext: string
}

interface Project extends ProjectCreate {
  id: string
  videoCount: number
  createdAt: string
}


interface ProjectManagementProps {
  collapsed: boolean
  onProjectSelect: (projectId: string | null) => void
  selectedProject: string | null
  onRefreshRequest?: () => void
}

const PROJECT_API_URL = 'http://localhost:8000/api/projects/'

export function ProjectManagement({ collapsed, onProjectSelect, selectedProject, onRefreshRequest }: ProjectManagementProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [newProject, setNewProject] = useState<ProjectCreate>({ name: "", description: "", promptContext: "" })  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProjects = async () => {
    try {
      setLoading(true)
      const response = await fetch(PROJECT_API_URL)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json() as Project[]

      setProjects(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch projects')
      console.error('Error fetching projects:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchProjectById = async (projectId: string) => {
    try {
      const response = await fetch(`${PROJECT_API_URL}${projectId}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json() as Project
      
      return data
    } catch (err) {
      console.error('Error fetching project by ID:', err)
      return null
    }
  }
  
  
  useEffect(() => {
    fetchProjects()
  }, [])

  const filteredProjects = projects.filter(
    (project) =>
      project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.description.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  const handleSelectProject = async (projectId: string) => {
    const project = await fetchProjectById(projectId)
    if (project) {
      console.log('Selected Project:', project)
      
      // Update the projects state with the latest project data
      setProjects((prevProjects) => {
        return prevProjects.map((p) =>
          p.id === projectId ? { ...project } : p
        )
      })
    }

    onProjectSelect(projectId)
    
    // Trigger refresh when project is selected
    if (onRefreshRequest) {
      onRefreshRequest()
    }
  }



  const handleCreateProject = async () => {
    if (newProject.name.trim()) {
      const project: ProjectCreate = {
        name: newProject.name,
        description: newProject.description,
        promptContext: newProject.promptContext,
      }

      // consume backend API to create project
      const response = await fetch(PROJECT_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(project),
      })

      if (!response.ok) {
        toast.error('Failed to create project')
        return
      }

      const createdProject = await response.json() as Project
      console.log('Created Project:', createdProject)
      

      toast.success('Project created successfully')

      
      setProjects([createdProject, ...projects])
      setNewProject({ name: "", description: "", promptContext: "" })
      setIsCreateDialogOpen(false)
      onProjectSelect(createdProject.id)
    }
  }

  const handleEditProject = async () => {
    if (editingProject && editingProject.name.trim()) {

      const response = await fetch(`${PROJECT_API_URL}${editingProject.id}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editingProject),
      })

      if (!response.ok) {
        toast.error('Failed to update project')
        return
      }

      const updatedProject = await response.json() as Project

      setProjects((prevProjects) => {
        console.log('Previous Projects:', prevProjects)
        console.log('Updated Project:', updatedProject)
        // Create a new array with updated project to ensure React detects the change
        return prevProjects.map((p) => 
          p.id === updatedProject.id ? { ...updatedProject } : p
        )
      })
      onProjectSelect(updatedProject.id)  
      setIsEditDialogOpen(false)
      setEditingProject(null)
      toast.success('Project updated successfully')
    }
  }

  const handleDeleteProject = async (projectId: string) => {
    try {
      // Call backend API to delete project
      const response = await fetch(`${PROJECT_API_URL}${projectId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        toast.error(`Failed to delete project: ${errorData.detail || 'Unknown error'}`)
        return
      }

      // Remove project from local state
      setProjects(projects.filter((p) => p.id !== projectId))

      // Handle project selection logic
      if (selectedProject === projectId) {
        const remainingProjects = projects.filter((p) => p.id !== projectId)
        onProjectSelect(remainingProjects.length > 0 ? remainingProjects[0].id : null)
      }

      toast.success('Project and all associated data deleted successfully')
    } catch (error) {
      console.error('Error deleting project:', error)
      toast.error('Failed to delete project')
    }
  }

  if (loading) {
    return (
      <div className="p-3 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-3 text-center text-destructive text-sm">
        Error loading projects: {error}
      </div>
    )
  }

  if (collapsed) {
    return (
      <div className="p-2 space-y-2">
        <Button variant="ghost" size="sm" className="w-full h-8 p-0" onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="h-4 w-4" />
        </Button>
        {filteredProjects.slice(0, 3).map((project) => (
          <Button
            key={project.id}
            variant={selectedProject === project.id ? "secondary" : "ghost"}
            size="sm"
            className="w-full h-8 p-0"
            onClick={() => onProjectSelect(project.id)}
          >
            <Folder className="h-4 w-4" />
          </Button>
        ))}
      </div>
    )
  }

  return (
    <div className="p-3 space-y-3">
      {/* Create Project Button */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm" className="w-full justify-start gap-2 bg-transparent">
            <Plus className="h-4 w-4" />
            New Project
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="project-name">Project Name</Label>
              <Input
                id="project-name"
                value={newProject.name}
                onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                placeholder="Enter project name..."
              />
            </div>
            <div>
              <Label htmlFor="project-description">Description</Label>
              <Textarea
                id="project-description"
                value={newProject.description}
                onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                placeholder="Enter project description..."
                rows={3}
              />
            </div>
            <div>
              <Label htmlFor="project-prompt-context">Prompt Context</Label>
              <Textarea
                id="project-prompt-context"
                value={newProject.promptContext}
                onChange={(e) => setNewProject({ ...newProject, promptContext: e.target.value })}
                placeholder="Enter project prompt context..."
                rows={20}
              />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateProject}>Create Project</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search projects..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-8"
        />
      </div>

      {/* Projects List */}
      <div className="space-y-2">
        <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Projects ({filteredProjects.length})
        </div>

        {filteredProjects.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-4">No projects found</div>
        ) : (
          <div className="space-y-1">
            {filteredProjects.map((project) => (
              <Card
                key={project.id}
                className={`p-3 cursor-pointer transition-colors hover:bg-accent/50 ${
                  selectedProject === project.id ? "bg-accent" : ""
                }`}
                onClick={async () => await handleSelectProject(project.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Folder className="h-4 w-4 text-primary flex-shrink-0" />
                      <h3 className="font-medium text-sm truncate">{project.name}</h3>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{project.description}</p>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Video className="h-3 w-3" />
                        <span>{project.videoCount}</span>
                      </div>
                      <span>{formatDate(project.createdAt)}</span>
                    </div>
                  </div>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 opacity-50 hover:opacity-100 transition-opacity"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreVertical className="h-3 w-3" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={async (e) => {
                          e.stopPropagation()
                          const latestProject = await fetchProjectById(project.id)
                          if (latestProject) {
                            console.log("latest project", latestProject)
                            setEditingProject(latestProject)
                            setIsEditDialogOpen(true)
                          } else {
                            toast.error('Failed to load project details')
                          }
                        }}
                      >
                        <Edit className="h-4 w-4 mr-2" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteProject(project.id)
                        }}
                        className="text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Edit Project Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Project</DialogTitle>
          </DialogHeader>
          {editingProject && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-project-name">Project Name</Label>
                <Input
                  id="edit-project-name"
                  value={editingProject.name}
                  onChange={(e) => setEditingProject({ ...editingProject, name: e.target.value })}
                  placeholder="Enter project name..."
                />
              </div>
              <div>
                <Label htmlFor="edit-project-description">Description</Label>
                <Textarea
                  id="edit-project-description"
                  value={editingProject.description}
                  onChange={(e) => setEditingProject({ ...editingProject, description: e.target.value })}
                  placeholder="Enter project description..."
                  rows={3}
                />
              </div>
              <div>
              <Label htmlFor="project-prompt-context">Prompt Context</Label>
              <Textarea
                id="project-prompt-context"
                value={editingProject.promptContext}
                onChange={(e) => setEditingProject({ ...editingProject, promptContext: e.target.value })}
                placeholder="Enter project prompt context..."
                rows={20}
              />
            </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleEditProject}>Save Changes</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
