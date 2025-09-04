from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from backend.database import get_db
from backend import crud, schemas

router = APIRouter(prefix="/scrape", tags=["scraping"])


@router.post("/source")
async def scrape_sources_for_video(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """
    Scrape additional sources for a video using background Celery tasks.
    If source_url and source_type are provided, it scrapes content from that specific source.
    If only video_id and project_id are provided, it triggers bulk scraping.
    """
    from backend.tasks.background import scrape_sources_task

    # Extract parameters from request body
    knowledge_item_id_str = request_data.get("id")


    # Convert kno string to UUID if provided
    if knowledge_item_id_str:
        try:
            knowledge_item_id = UUID(knowledge_item_id_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid knowledge_item_id format")

    knowledge_item = crud.get_knowledge_item(db, knowledge_item_id)
        # Trigger scraping task asynchronously
    if knowledge_item:
        scrape_sources_task.apply_async(args=[str(knowledge_item.id)])

        return {
            "message": f"Scraping initiated for source: {str(knowledge_item.id)}",
            "video_id": knowledge_item.video_id,
            "knowledge_item_id": str(knowledge_item.id),
            "source_type": knowledge_item.source_type,
            "source_url": knowledge_item.source_url,
            "status": "processing"
        }
    else:
        return {
            "message": f"Source can not be found"
        }