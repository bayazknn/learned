## Project Overview

The project's aim is to create a web app to collect YouTube videos under defined projects. Users can watch videos and chat with an agentic AI chatbot that uses a RAG system. The RAG system processes video description, video transcripts and link sources placed in video description. All link sources (pdf, web) are crawled as text and then the texts are sent to the RAG system. During chat conversations, important information can be stored in the memory layer of agentic AI. The project has frontend and backend layers. All database operation, AI chat services, crawling, RAG process are managed by backend layer.

### Current Implementation Status (Updated: September 3, 2025)

**Backend Status: COMPLETE WITH ADVANCED AI INTEGRATION**
- ✅ FastAPI server with CORS middleware
- ✅ SQLAlchemy database models (Video, Project, KnowledgeItem, ScrapedContent)
- ✅ Pydantic schemas for request/response validation
- ✅ CRUD operations for all entities
- ✅ YouTube video processing with yt-dlp integration
- ✅ Background task processing with Celery
- ✅ Database migrations with Alembic
- ✅ API endpoints for videos, projects, knowledge, scraping, and chat
- ✅ PostgreSQL database integration
- ✅ Qdrant vector database setup
- ✅ **COMPLETE RAG service with LlamaIndex integration**
- ✅ **LangGraph agent system with 3-step RAG workflow**
- ✅ **Real embedding generation (Ollama/Google GenAI)**
- ✅ **Tavily web search integration**
- ✅ **YouTube transcript API dependency added**
- ✅ **RAG storage fully implemented in background tasks**

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

**Current Dependencies (COMPLETE AI STACK):**
- `fastapi==0.116.1`: Backend server framework
- `sqlalchemy==2.0.43`: Database ORM
- `psycopg2-binary==2.9.10`: PostgreSQL driver
- `yt-dlp==2024.12.13`: YouTube video processing
- `beautifulsoup4==4.13.5`: Web scraping
- `qdrant-client==1.15.1`: Vector database
- `celery==5.5.3`: Background task processing
- `redis==6.4.0`: Celery broker
- `alembic==1.14.1`: Database migrations
- `pydantic==2.11.7`: Data validation
- `google-api-python-client==2.179.0`: YouTube API integration
- `webvtt-py==0.5.1`: WebVTT subtitle handling
- `pytest==8.4.1`: Testing framework
- `youtube-transcript-api==1.2.2`: YouTube transcript extraction ✅ **ADDED**

**Content Processing Dependencies (NEWLY ADDED):**
- `PyMuPDF==1.24.14`: PDF text extraction (fitz)
- `pdfplumber==0.11.4`: Alternative PDF processor
- `arxiv==2.1.3`: Arxiv paper search and retrieval
- `requests-html==0.10.0`: HTML scraping with JavaScript support
- `lxml==5.3.0`: XML and HTML parsing
- `html5lib==1.1`: HTML parser
- `fake-useragent==1.5.1`: User agent rotation for scraping
- `urllib3==2.2.3`: HTTP client
- `python-multipart==0.0.20`: Multipart form data handling
- `arize-phoenix==11.30.0`: AI observability and monitoring

**AI/ML Dependencies (NEWLY ADDED):**
- `llama-index-core==0.13.3`: LlamaIndex core functionality
- `llama-index-embeddings-ollama==0.8.2`: Ollama embeddings integration
- `llama-index-embeddings-google-genai==0.3.0`: Google GenAI embeddings
- `llama-index-vector-stores-qdrant==0.8.2`: Qdrant vector store integration
- `langgraph==0.6.6`: LangGraph for agent workflows
- `langchain-community==0.3.29`: LangChain community tools
- `langchain-core==0.3.75`: LangChain core functionality
- `langchain-openai==0.3.32`: OpenAI integration
- `tavily-python==0.7.11`: Tavily web search API ✅ **ADDED**
- `langchain-anthropic==0.3.19`: Anthropic integration
- `langchain-google-genai==2.1.10`: Google GenAI integration
- `langgraph-checkpoint-sqlite==2.0.11`: SQLite checkpointer for LangGraph
- `fastembed==0.7.3`: Fast embedding generation

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

**Chat API (`/api/chat`) - NEW:**
- `POST /research`: Research agent with tool access
- `POST /langgraph`: LangGraph agent with 3-step RAG workflow
- `GET /tools`: Get available agent tools
- `POST /test`: Test endpoint

## Main Workflows

#### Project, Video CRUD and RAG Operations

**Implemented:**
- ✅ Project CRUD operations
- ✅ Video creation with background processing
- ✅ YouTube video info extraction
- ✅ Database storage for videos and metadata
- ✅ Background task system with Celery
- ✅ YouTube transcript extraction ✅ **FIXED**
- ✅ **COMPLETE RAG service with LlamaIndex** ✅ **IMPLEMENTED**
- ✅ **Real embedding generation (Ollama/Google GenAI)** ✅ **IMPLEMENTED**
- ✅ **RAG storage in background tasks** ✅ **ENABLED**

**Infrastructure Ready (Packages Installed):**
- ✅ PDF processing packages installed (PyMuPDF, pdfplumber)
- ✅ Arxiv search package installed (arxiv)
- ✅ Advanced web scraping packages installed (requests-html, lxml, html5lib)
- ✅ AI observability package installed (arize-phoenix)

**Pending Implementation:**
- ⏳ Complete link extraction from video descriptions
- ⏳ Implement web and PDF content scraping service
- ⏳ Add Arxiv paper search functionality

#### Agentic AI Chatbot

**COMPLETELY IMPLEMENTED:**
- ✅ **LangGraph agent with 3-step RAG workflow** ✅ **IMPLEMENTED**
  - Step 1: Query generation using Ollama (gemma3:270m)
  - Step 2: Context retrieval from Qdrant vector database
  - Step 3: Response generation combining query and context
- ✅ **Research agent with tool access** ✅ **IMPLEMENTED**
- ✅ **Thread ID tracking for persistent conversations** ✅ **IMPLEMENTED**
- ✅ **Checkpointer for state persistence** ✅ **IMPLEMENTED**
- ✅ Frontend chat interface structure
- ✅ Memory storage UI (simulated)

**Pending Frontend Integration:**
- ⏳ CopilotKit integration for frontend chat interface
- ⏳ Backend API integration for AI chat
- ⏳ Real-time chat interface with backend
- ⏳ Memory layer integration

## Technical Architecture

**Backend Stack:**
- FastAPI for REST API
- SQLAlchemy + PostgreSQL for relational data
- Qdrant for vector storage
- Celery + Redis for background tasks
- yt-dlp for YouTube processing
- BeautifulSoup for web scraping
- **LlamaIndex for RAG operations** ✅ **NEW**
- **LangGraph for agent workflows** ✅ **NEW**
- **Ollama/Google GenAI for embeddings** ✅ **NEW**

**Frontend Stack:**
- Next.js 15 with App Router
- TypeScript for type safety
- Shadcn/ui for component library
- Tailwind CSS for styling
- Radix UI primitives

**Development Status:**
- Database schema: Complete
- API endpoints: Complete (including new chat endpoints)
- Background processing: Complete with RAG integration
- Frontend structure: Complete (needs backend API integration)
- **AI/RAG integration: COMPLETE** ✅ **UPDATED**
- **Agent system: COMPLETE** ✅ **UPDATED**
- Memory management: Frontend structure complete, backend pending
- Chat interface: Frontend structure complete, backend integration pending

## New Architecture Components

### LlamaIndex RAG Service (`backend/services/rag_llama_index.py`)
- Real embedding generation with Ollama (all-minilm:22m) and Google GenAI
- Semantic chunking with IngestionPipeline
- Qdrant vector storage with project-specific collections
- Advanced retrieval with filtering capabilities
- Support for multiple embedding providers

### LangGraph Agent (`backend/agents/langgraph_agent.py`)
- Three-step RAG workflow:
  1. **Query Generation**: Uses Ollama (gemma3:270m) to generate search queries
  2. **Context Retrieval**: Retrieves relevant context from Qdrant
  3. **Response Generation**: Generates final response using retrieved context
- Thread persistence with SQLite checkpointer
- Configurable embedding model selection

### Research Agent (`archive/agents/research_agent_manager.py`)
- Tool-based agent with access to:
  - Project knowledge retrieval (Qdrant)
  - Web search (Tavily)
  - Video transcript analysis
- Flexible tool selection and orchestration

### Chat API (`backend/api/endpoints/chat.py`)
- `/chat/research`: Research agent endpoint
- `/chat/langgraph`: LangGraph agent endpoint
- `/chat/tools`: Available tools endpoint
- Thread ID tracking for persistent conversations

## Next Steps for Completion

### Immediate Fixes (High Priority)
1. **Install CopilotKit**: Add CopilotKit dependency to frontend package.json
2. **Frontend API Integration**: Connect frontend components to backend APIs
3. **Real chat interface**: Replace simulated responses with real AI backend

### Backend Completion
4. **Link extraction**: Implement link extraction from video descriptions
5. **Content scraping**: Complete web and PDF content extraction service
6. **Arxiv integration**: Add Arxiv paper search functionality
7. **Memory layer**: Implement long-term conversation memory storage

### Frontend Features
8. **Video transcript display**: Add transcript viewing functionality
9. **Source display**: Implement source content display from scraped data
10. **Real-time updates**: Add WebSocket support for real-time processing updates

### Testing & Deployment
11. **Add comprehensive tests**: Write unit and integration tests
12. **Documentation**: Create user and developer documentation
13. **Deployment setup**: Prepare for production deployment

## Recent Major Updates (September 3, 2025)
- ✅ Complete RAG service implementation with LlamaIndex
- ✅ Real embedding generation with Ollama/Google GenAI
- ✅ LangGraph agent system with 3-step workflow
- ✅ Tavily web search integration
- ✅ Comprehensive test suite added
- ✅ Chat API endpoints implemented
- ✅ All missing AI dependencies added to requirements.txt
- ✅ YouTube transcript API dependency fixed
- ✅ **Content Processing Infrastructure Added**: PDF processing (PyMuPDF, pdfplumber), Arxiv search (arxiv), Advanced web scraping (requests-html, lxml, html5lib)
- ✅ **AI Observability Integration**: Arize Phoenix added for monitoring and debugging
- ✅ **Updated yt-dlp to latest version (2024.12.13)**
- ✅ **Repository consolidation**: yt-learn Next.js project integrated into main repository
