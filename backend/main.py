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
from backend.trace.arize import tracer_provider
from openinference.instrumentation.langchain import LangChainInstrumentor

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifecycle events"""
    # Startup
    try:
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        await initialize_global_agent()
        print("✅ LangGraph agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize LangGraph agent: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    try:
        await cleanup_global_agent()
        print("✅ LangGraph agent cleaned up successfully")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")


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
