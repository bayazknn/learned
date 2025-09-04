from fastapi import FastAPI
from backend.api.api import api_router
from backend.agents.langgraph_agent import initialize_global_agent
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from backend.agents.langgraph_agent import initialize_global_agent, cleanup_global_agent

logger = logging.getLogger(__name__)

# Lifespan manager for proper startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting up LangGraph Agent...")
    try:
        await initialize_global_agent()
        logger.info("LangGraph Agent initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize LangGraph Agent: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down LangGraph Agent...")
        try:
            await cleanup_global_agent()
            logger.info("LangGraph Agent cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


app = FastAPI(
    title="learned: Youtube Video AI Collection",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust origins as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}

# Include all API routers
app.include_router(api_router, prefix="/api")

@app.get("/")
async def read_root():
    return {"message": "Welcome to YouTube+AI Research API", "docs": "/docs"}
