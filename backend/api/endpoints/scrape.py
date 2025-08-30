from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from backend.database import get_db
from backend import crud, schemas
from backend.tasks.background import scrape_url_task

router = APIRouter(prefix="/scrape", tags=["scraping"])

@router.post("/")
async def initiate_scrape(
    url: str,
    background_tasks: BackgroundTasks,
    project_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """
    Initiate web scraping for a URL. Optionally associate with a project for RAG storage.
    """
    # Validate URL format
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    # Check if URL already exists
    existing_content = crud.get_scraped_content(db, url)
    if existing_content:
        raise HTTPException(status_code=400, detail="URL already scraped")
    
    # Verify project exists if provided
    if project_id:
        db_project = crud.get_project(db, project_id)
        if db_project is None:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # Start background task for scraping
    background_tasks.add_task(scrape_url_task, url, str(project_id) if project_id else None)
    
    return {
        "message": "Scraping initiated",
        "url": url,
        "project_id": project_id
    }

@router.get("/")
async def get_scraped_content(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all scraped content with pagination.
    """
    scraped_content = crud.get_all_scraped_content(db, skip=skip, limit=limit)
    return scraped_content

@router.get("/{url}")
async def get_scraped_content_by_url(
    url: str,
    db: Session = Depends(get_db)
):
    """
    Get scraped content for a specific URL.
    """
    scraped_content = crud.get_scraped_content(db, url)
    if scraped_content is None:
        raise HTTPException(status_code=404, detail="URL not scraped yet")
    return scraped_content

@router.delete("/{url}")
async def delete_scraped_content(
    url: str,
    db: Session = Depends(get_db)
):
    """
    Delete scraped content for a specific URL.
    """
    scraped_content = crud.get_scraped_content(db, url)
    if scraped_content is None:
        raise HTTPException(status_code=404, detail="URL not scraped yet")
    
    db.delete(scraped_content)
    db.commit()
    
    return {"message": "Scraped content deleted successfully"}
