# YouTube Research Assistant

An AI-powered web application for collecting, analyzing, and researching YouTube videos with intelligent chat capabilities. Built with FastAPI backend and Next.js frontend.

## 🚀 Features

### Core Functionality
- **Video Management**: Add YouTube videos to organized projects
- **Transcript Extraction**: Automatic extraction and processing of video transcripts
- **AI-Powered Research**: RAG (Retrieval Augmented Generation) system for intelligent video analysis
- **Web Scraping**: Automatic extraction of content from links in video descriptions
- **Vector Storage**: Qdrant vector database for semantic search and retrieval

### AI Chat Capabilities
- **Contextual Conversations**: Chat with AI about video content using retrieved context
- **Memory Management**: Long-term conversation memory for persistent research sessions
- **Source Attribution**: AI responses include citations from video transcripts and scraped content

### Technical Features
- **FastAPI Backend**: High-performance Python API with async support
- **Next.js Frontend**: Modern React framework with TypeScript
- **PostgreSQL Database**: Relational data storage for projects and videos
- **Celery Background Tasks**: Asynchronous processing of videos and content
- **Docker Ready**: Containerized deployment setup

## 🛠️ Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Qdrant** - Vector database
- **Celery** - Background tasks
- **Redis** - Message broker
- **yt-dlp** - YouTube video processing
- **BeautifulSoup** - Web scraping
- **LangChain** - AI orchestration
- **Ollama** - Local AI models

### Frontend
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **shadcn/ui** - Component library
- **Tailwind CSS** - Styling
- **Radix UI** - Primitive components

## 📦 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis
- Docker (optional)
- Ollama (for local AI models)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd learned
   ```

2. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file in the backend directory:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/yt_research
   REDIS_URL=redis://localhost:6379/0
   QDRANT_URL=http://localhost:6333
   OLLAMA_BASE_URL=http://localhost:11434
   GOOGLE_API_KEY=your_google_api_key_optional
   ```

4. **Set up databases**
   ```bash
   # Start PostgreSQL and Redis (using Docker or local install)
   docker run -d --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:14
   docker run -d --name redis -p 6379:6379 redis:7-alpine
   docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend services**
   ```bash
   # Terminal 1: Start FastAPI server
   uvicorn main:app --reload --host 0.0.0.0 --port 8000

   # Terminal 2: Start Celery worker
   celery -A tasks.background worker --loglevel=info

   # Terminal 3: Start Ollama (if using local models)
   ollama serve
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd yt-learn
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   Create a `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🎯 Usage

### Adding Videos
1. Create a project in the left sidebar
2. Click "Add Video" and paste a YouTube URL
3. The system will automatically:
   - Extract video metadata
   - Download and process transcripts
   - Scrape links from video description
   - Generate embeddings for semantic search

### Research Chat
1. Select a project to focus your research
2. Use the AI chat interface to ask questions about:
   - Specific video content
   - Themes across multiple videos
   - Technical concepts discussed
   - Research recommendations

### Memory Management
- Save important insights from conversations
- Organize research findings by topics
- Retrieve previous research sessions

## 🔧 API Endpoints

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{project_id}` - Get project details
- `PUT /api/projects/{project_id}` - Update project
- `DELETE /api/projects/{project_id}` - Delete project

### Videos
- `GET /api/videos` - List all videos
- `POST /api/videos` - Add new video
- `GET /api/videos/{video_id}` - Get video details
- `GET /api/videos/project/{project_id}` - Get videos by project
- `DELETE /api/videos/{video_id}` - Delete video

### Knowledge
- `GET /api/knowledge` - List knowledge items
- `POST /api/knowledge` - Create knowledge item
- `GET /api/knowledge/{item_id}` - Get knowledge item
- `PUT /api/knowledge/{item_id}` - Update knowledge item
- `DELETE /api/knowledge/{item_id}` - Delete knowledge item

### Scraping
- `POST /api/scrape` - Scrape web content from URL

## 🐳 Docker Deployment

### Using Docker Compose
```bash
docker-compose up -d
```

### Manual Docker Setup
```bash
# Build and run backend
docker build -t yt-research-backend -f backend/Dockerfile .
docker run -d -p 8000:8000 yt-research-backend

# Build and run frontend
docker build -t yt-research-frontend -f yt-learn/Dockerfile .
docker run -d -p 3000:3000 yt-research-frontend
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd yt-learn
npm test
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend development
- Write tests for new functionality
- Update documentation for new features
- Use conventional commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Next.js](https://nextjs.org/) for the React framework
- [shadcn/ui](https://ui.shadcn.com/) for the component library
- [Qdrant](https://qdrant.tech/) for vector database
- [Ollama](https://ollama.ai/) for local AI models

## 📞 Support

If you have any questions or need help, please:
1. Check the [API documentation](http://localhost:8000/docs)
2. Open an issue on GitHub
3. Contact the development team

---

**Note**: This project is under active development. Some features may be experimental or subject to change.
