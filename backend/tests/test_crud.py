import pytest
from sqlalchemy.orm import Session
from uuid import UUID
from backend import crud, schemas
from backend.database import Base, engine
from backend.models import Video, Project, KnowledgeItem, ScrapedContent


@pytest.fixture(scope="module")
def test_db():
    """Create test database tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_video(test_db, db: Session):
    """Test creating a video"""
    video_data = schemas.VideoCreate(
        id="test_video_123",
        title="Test Video",
        url="https://youtube.com/watch?v=test_video_123"
    )
    
    video = crud.create_video(db, video_data)
    
    assert video.id == "test_video_123"
    assert video.title == "Test Video"
    assert video.url == "https://youtube.com/watch?v=test_video_123"
    assert video.transcript is None


def test_get_video(test_db, db: Session):
    """Test retrieving a video"""
    video = crud.get_video(db, "test_video_123")
    
    assert video is not None
    assert video.id == "test_video_123"
    assert video.title == "Test Video"


def test_update_video_transcript(test_db, db: Session):
    """Test updating video transcript"""
    transcript = "This is a test transcript for the video."
    updated_video = crud.update_video_transcript(db, "test_video_123", transcript)
    
    assert updated_video is not None
    assert updated_video.transcript == transcript


def test_create_project(test_db, db: Session):
    """Test creating a project"""
    project_data = schemas.ProjectCreate(
        name="Test Project",
        description="A test project for testing"
    )
    
    project = crud.create_project(db, project_data)
    
    assert project.name == "Test Project"
    assert project.description == "A test project for testing"
    assert isinstance(project.id, UUID)


def test_get_project(test_db, db: Session):
    """Test retrieving a project"""
    projects = crud.get_projects(db)
    assert len(projects) > 0
    
    project = projects[0]
    retrieved_project = crud.get_project(db, project.id)
    
    assert retrieved_project is not None
    assert retrieved_project.name == "Test Project"


def test_create_knowledge_item(test_db, db: Session):
    """Test creating a knowledge item"""
    projects = crud.get_projects(db)
    project_id = projects[0].id
    
    knowledge_data = schemas.KnowledgeItemCreate(
        project_id=project_id,
        content="Test knowledge content",
        source_url="https://example.com/test"
    )
    
    knowledge_item = crud.create_knowledge_item(db, knowledge_data)
    
    assert knowledge_item.project_id == project_id
    assert knowledge_item.content == "Test knowledge content"
    assert knowledge_item.source_url == "https://example.com/test"
    assert isinstance(knowledge_item.id, UUID)


def test_get_knowledge_items_by_project(test_db, db: Session):
    """Test retrieving knowledge items by project"""
    projects = crud.get_projects(db)
    project_id = projects[0].id
    
    knowledge_items = crud.get_knowledge_items_by_project(db, project_id)
    
    assert len(knowledge_items) > 0
    assert knowledge_items[0].project_id == project_id


def test_create_scraped_content(test_db, db: Session):
    """Test creating scraped content"""
    scraped_data = schemas.ScrapedContentCreate(
        url="https://example.com/scraped",
        content="Scraped content text"
    )
    
    scraped_content = crud.create_scraped_content(db, scraped_data)
    
    assert scraped_content.url == "https://example.com/scraped"
    assert scraped_content.content == "Scraped content text"
    assert isinstance(scraped_content.id, UUID)


def test_get_scraped_content(test_db, db: Session):
    """Test retrieving scraped content"""
    scraped_content = crud.get_scraped_content(db, "https://example.com/scraped")
    
    assert scraped_content is not None
    assert scraped_content.url == "https://example.com/scraped"
    assert scraped_content.content == "Scraped content text"
