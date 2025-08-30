"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  PanelLeftClose,
  PanelLeftOpen,
  Video,
  Settings,
  MessageSquare,
  Brain,
  Maximize2,
  Minimize2,
} from "lucide-react"
import { ProjectManagement } from "@/components/project-management"
import { AIChat } from "@/components/ai-chat"
import { MemoryManagement } from "@/components/memory-management"
import { VideoDisplay } from "@/components/video-display"

interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const [leftSidebarCollapsed, setLeftSidebarCollapsed] = useState(false)
  const [rightSidebarTab, setRightSidebarTab] = useState("chat")
  const [rightSidebarMaximized, setRightSidebarMaximized] = useState(false)
  const [selectedProject, setSelectedProject] = useState<string | null>(null)

  const handleProjectSelect = (projectId: string | null) => {
    setSelectedProject(projectId)
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Application Bar */}
      <header className="h-14 border-b border-border bg-card px-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Video className="h-6 w-6 text-primary" />
          <h1 className="text-lg font-semibold text-foreground">YouTube Video Collector</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <aside
          className={`bg-sidebar border-r border-sidebar-border transition-all duration-300 ${
            leftSidebarCollapsed ? "w-12" : "w-64"
          }`}
        >
          <div className="p-3 border-b border-sidebar-border">
            <div className="flex items-center justify-between">
              {!leftSidebarCollapsed && <h2 className="text-sm font-medium text-sidebar-foreground">Projects</h2>}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setLeftSidebarCollapsed(!leftSidebarCollapsed)}
                className="h-8 w-8 p-0"
              >
                {leftSidebarCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          <ProjectManagement 
            collapsed={leftSidebarCollapsed}
            onProjectSelect={handleProjectSelect}
            selectedProject={selectedProject}
          />
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 flex overflow-hidden">
          {!rightSidebarMaximized && (
            <div className="flex-1 overflow-auto">
              {React.Children.map(children, () => {
                // Simple approach: just render VideoDisplay with the projectId
                return <VideoDisplay projectId={selectedProject} />
              })}
            </div>
          )}

          {/* Right Sidebar with Tab Navigation */}
          <aside
            className={`bg-sidebar border-l border-sidebar-border flex flex-col transition-all duration-300 ${
              rightSidebarMaximized ? "flex-1" : "w-80"
            }`}
          >
            <div className="p-3 border-b border-sidebar-border">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-sm font-medium text-sidebar-foreground">AI Assistant</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setRightSidebarMaximized(!rightSidebarMaximized)}
                  className="h-6 w-6 p-0"
                >
                  {rightSidebarMaximized ? <Minimize2 className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
                </Button>
              </div>

              {/* Tab Navigation */}
              <Tabs value={rightSidebarTab} onValueChange={setRightSidebarTab} className="w-full">
                <TabsList className="grid w-full grid-cols-2 h-8">
                  <TabsTrigger value="chat" className="text-xs flex items-center gap-1">
                    <MessageSquare className="h-3 w-3" />
                    Chat
                  </TabsTrigger>
                  <TabsTrigger value="memory" className="text-xs flex items-center gap-1">
                    <Brain className="h-3 w-3" />
                    Memory
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>

            <div className="flex-1 flex flex-col overflow-hidden">
              <Tabs value={rightSidebarTab} onValueChange={setRightSidebarTab} className="flex-1 flex flex-col">
                <TabsContent value="chat" className="flex-1 p-3 mt-0">
                  <AIChat projectId={selectedProject} selectedVideoId={null} />
                </TabsContent>

                <TabsContent value="memory" className="flex-1 p-3 mt-0 overflow-hidden">
                  <div className="h-full">
                    <MemoryManagement />
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          </aside>
        </main>
      </div>
    </div>
  )
}
