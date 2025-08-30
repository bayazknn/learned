## Project Overview

The project's aim is to create a web app to collect YouTube videos under defined projects. Users can watch videos and chat with an agentic AI chatbot that uses a RAG system. The RAG system processes video description, video transcripts and link sources placed in video description. All link sources (pdf, web) are crawled as text and then the texts are sent to the RAG system. During chat conversations, important information can be stored in the memory layer of agentic AI. The project has frontend and backend layers. All database operation, AI chat services, crawling, RAG process are managed by backend layer.

### Current Implementation Status (Updated: August 30, 2025)

**Backend Status: NEARLY COMPLETE (with some issues)**
- ✅ FastAPI server with CORS middleware
- ✅ SQLAlchemy database models (Video, Project, KnowledgeItem, ScrapedContent)
- ✅ Pydantic schemas for request/response validation
- ✅ CRUD operations for all entities
- ✅ YouTube video processing with yt-dlp integration
- ✅ Background task processing with Celery
- ✅ Database migrations with Alembic
- ✅ API endpoints for videos, projects, knowledge, and scraping
- ✅ PostgreSQL database integration
- ✅ Qdrant vector database setup
- ⚠️ RAG service implemented but uses placeholder embeddings (needs Ollama/Sentence Transformers)
- ⚠️ YouTube transcript API dependency missing from requirements.txt
- ⚠️ RAG storage in background tasks currently commented out

**Frontend Status: STRUCTURE COMPLETE (needs backend integration)**
- ✅ Next.js 15 with TypeScript
- ✅ Shadcn/ui component library integration
- ✅ Complete app layout with sidebar navigation
- ✅ Project management component with CRUD operations
- ✅ Video display component
- ✅ AI chat component with simulated responses
- ✅ Memory management component structure
- ⏳ CopilotKit integration for AI chat (not installed yet)
- ⏳ Real RAG system integration (currently simulated)
- ⏳ Video transcript display integration
- ⏳ Source extraction and display integration

### Frontend Features

Frontend is a Next.js 15 app with shadcn/ui components. Current implementation includes:

**Application Structure:**
- Application bar (heading bar) with title and settings
- Left sidebar for project management (collapsible)
- Main area for video display
- Right sidebar with AI Chat and Memory tabs

**Implemented Components:**
- `AppLayout`: Main application layout with navigation
- `ProjectManagement`: Project CRUD operations
- `VideoDisplay`: Video listing and display
- `AIChat`: AI chat interface (structure complete)
- `MemoryManagement`: Memory CRUD operations (structure complete)

**UI Components Available:**
- Button, Card, Dialog, Dropdown, Input, Label, ScrollArea, Select, Separator, Tabs, Textarea
- Avatar, Badge, Sonner notifications

### Backend Features

#### Python Packages for Backend Server

**Current Dependencies:**
- `fastapi==0.116.1`: Backend server framework
- `sqlalchemy==2.0.35`: Database ORM
- `psycopg2-binary==2.9.10`: PostgreSQL driver
- `yt-dlp==2024.11.18`: YouTube video processing
- `beautifulsoup4==4.12.3`: Web scraping
- `qdrant-client==1.15.1`: Vector database
- `celery==5.4.0`: Background task processing
- `redis==5.2.1`: Celery broker
- `alembic==1.14.1`: Database migrations
- `pydantic==2.11.7`: Data validation
- `google-api-python-client==2.179.0`: YouTube API integration
- `webvtt-py==0.4.6`: WebVTT subtitle handling
- `pytest==8.4.1`: Testing framework

**Missing Dependencies (needed but not in requirements.txt):**
- `youtube-transcript-api`: For YouTube transcript extraction (imported but missing from requirements)

**Pending Dependencies for AI Features:**
- LangChain packages for RAG orchestration
- Ollama integration for embeddings and AI
- Arxiv package for paper search
- Sentence Transformers for embeddings

#### Database Schema

**Video Model:**
- youtube_id, title, url, transcript, description
- project_id (foreign key), duration, upload_date, views
- thumbnail_url, processing_status, processed_at

**Project Model:**
- name, description, created_at

**KnowledgeItem Model:**
- project_id, video_id, content, source_url, source_type

**ScrapedContent Model:**
- url (unique), content

#### API Endpoints

**Videos API (`/api/videos`):**
- `POST /`: Create video and start background processing
- `GET /`: Get all videos with pagination
- `GET /project/{project_id}`: Get videos by project
- `GET /{video_id}`: Get specific video
- `GET /{video_id}/processing-status`: Check processing status
- `DELETE /{video_id}`: Delete video

**Projects API (`/api/projects`):**
- CRUD operations for projects

**Knowledge API (`/api/knowledge`):**
- CRUD operations for knowledge items

**Scrape API (`/api/scrape`):**
- Web scraping operations

## Main Workflows

#### Project, Video CRUD and RAG Operations

**Implemented:**
- ✅ Project CRUD operations
- ✅ Video creation with background processing
- ✅ YouTube video info extraction
- ✅ Database storage for videos and metadata
- ✅ Background task system with Celery
- ✅ YouTube transcript extraction (functional but missing dependency)
- ✅ Basic RAG service structure (with placeholder embeddings)

**Partially Implemented/Issues:**
- ⚠️ RAG integration with Qdrant: Service exists but uses dummy embeddings
- ⚠️ RAG storage in background tasks: Implemented but commented out
- ⚠️ YouTube transcript API: Imported but missing from requirements.txt

**Pending:**
- ⏳ Real embedding generation (Ollama/Sentence Transformers)
- ⏳ Link extraction from video descriptions
- ⏳ Arxiv paper search integration
- ⏳ Web and PDF content scraping
- ⏳ Complete RAG knowledge retrieval

#### Agentic AI Chatbot

**Partially Implemented:**
- ✅ Frontend chat interface structure
- ✅ Simulated AI responses with sources
- ✅ Memory storage UI (simulated)

**Pending Implementation:**
- ⏳ ReAct type agent with tools
- ⏳ Real RAG tool for querying Qdrant vector database
- ⏳ Memory layer for long-term conversation storage
- ⏳ CopilotKit integration for frontend chat interface
- ⏳ Backend API integration for AI chat

## Technical Architecture

**Backend Stack:**
- FastAPI for REST API
- SQLAlchemy + PostgreSQL for relational data
- Qdrant for vector storage
- Celery + Redis for background tasks
- yt-dlp for YouTube processing
- BeautifulSoup for web scraping

**Frontend Stack:**
- Next.js 15 with App Router
- TypeScript for type safety
- Shadcn/ui for component library
- Tailwind CSS for styling
- Radix UI primitives

**Development Status:**
- Database schema: Complete
- API endpoints: Complete
- Background processing: Complete (with RAG integration commented out)
- Frontend structure: Complete (needs backend API integration)
- AI/RAG integration: Partially implemented (placeholder embeddings, missing dependencies)
- Memory management: Frontend structure complete, backend pending
- Chat interface: Frontend structure complete, backend integration pending

## Next Steps for Completion

### Immediate Fixes (High Priority)
1. **Add missing dependencies**: Add `youtube-transcript-api` to requirements.txt
2. **Fix RAG embeddings**: Replace placeholder embeddings with real embedding generation (Ollama/Sentence Transformers)
3. **Enable RAG storage**: Uncomment RAG storage calls in background tasks
4. **Install CopilotKit**: Add CopilotKit dependency to frontend package.json

### AI Integration
5. **Add AI dependencies**: Install LangChain, Ollama client, and Sentence Transformers
6. **Implement embedding service**: Create proper embedding generation service
7. **Build RAG retrieval**: Complete knowledge retrieval with real embeddings

### Backend Completion
8. **Link extraction**: Implement link extraction from video descriptions
9. **Content scraping**: Complete web and PDF content extraction service
10. **Arxiv integration**: Add Arxiv paper search functionality
11. **Memory layer**: Implement long-term conversation memory storage

### Frontend Integration
12. **API integration**: Connect frontend components to backend APIs
13. **Real chat interface**: Replace simulated responses with real AI backend
14. **Video transcript display**: Add transcript viewing functionality
15. **Source display**: Implement source content display from scraped data

### Testing & Deployment
16. **Add comprehensive tests**: Write unit and integration tests
17. **Documentation**: Create user and developer documentation
18. **Deployment setup**: Prepare for production deployment
