from fastapi import APIRouter
from .endpoints import videos, projects, knowledge, scrape

# Main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(videos.router)
api_router.include_router(projects.router)
api_router.include_router(knowledge.router)
api_router.include_router(scrape.router)
