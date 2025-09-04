from fastapi import APIRouter
from .endpoints import videos, projects, knowledge, scrape, chat, upload

# Main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(videos.router)
api_router.include_router(projects.router)
api_router.include_router(knowledge.router)
api_router.include_router(scrape.router)
api_router.include_router(chat.router)
api_router.include_router(upload.router)
