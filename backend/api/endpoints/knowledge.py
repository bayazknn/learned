from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.database import get_db
from backend import crud, schemas
from backend.tasks.background import process_knowledge_item_task

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.post("/", response_model=schemas.KnowledgeItemResponse)
async def create_knowledge_item(
    knowledge_item: schemas.KnowledgeItemCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new knowledge item and store in RAG.
    """
    # Verify project exists
    db_project = crud.get_project(db, knowledge_item.project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create knowledge item in database
    db_knowledge_item = crud.create_knowledge_item(db, knowledge_item)
    
    # Start background task for RAG processing
    background_tasks.add_task(
        process_knowledge_item_task,
        str(knowledge_item.project_id),
        knowledge_item.content,
        knowledge_item.source_url
    )
    
    return db_knowledge_item

@router.get("/project/{project_id}", response_model=List[schemas.KnowledgeItemResponse])
async def get_knowledge_items_by_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all knowledge items for a specific project.
    """
    # Verify project exists
    db_project = crud.get_project(db, project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    knowledge_items = crud.get_knowledge_items_by_project(db, project_id)
    return knowledge_items

@router.get("/{knowledge_item_id}", response_model=schemas.KnowledgeItemResponse)
async def get_knowledge_item(
    knowledge_item_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific knowledge item by ID.
    """
    db_knowledge_item = crud.get_knowledge_item(db, knowledge_item_id)
    if db_knowledge_item is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return db_knowledge_item

@router.delete("/{knowledge_item_id}")
async def delete_knowledge_item(
    knowledge_item_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a knowledge item by ID.
    """
    db_knowledge_item = crud.get_knowledge_item(db, knowledge_item_id)
    if db_knowledge_item is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    
    db.delete(db_knowledge_item)
    db.commit()
    
    # Note: RAG deletion would require additional logic to remove from vector store
    # This would need to track which RAG entries correspond to which knowledge items
    
    return {"message": "Knowledge item deleted successfully"}
