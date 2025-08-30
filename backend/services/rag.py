from typing import List, Optional, Dict, Any
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import numpy as np
import asyncio

logger = logging.getLogger(__name__)

OLLAMA_EMBEDDING_MODEL = "all-minilm:22m"

class RAGService:
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """
        Initialize RAG service with Qdrant client.
        
        Args:
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
        """
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
        # Initialize embedding providers
        self.gemini_embeddings = None
        self.ollama_embeddings = None
        self._initialize_embedding_providers()
        
    def _initialize_embedding_providers(self):
        """Initialize embedding providers based on available configuration"""
        try:
            from backend.config import settings
            
            # Initialize Gemini if API key is available
            if settings.GOOGLE_API_KEY:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                self.gemini_embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=settings.GOOGLE_API_KEY
                )
                logger.info("Google Gemini embeddings initialized successfully")
            else:
                logger.warning("GOOGLE_API_KEY not found - Gemini embeddings disabled")
                
            # Always try to initialize Ollama (local)
            try:
                from langchain_ollama import OllamaEmbeddings
                # Try multiple common embedding models

                try:
                    self.ollama_embeddings = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)
                    logger.info(f"Ollama embeddings initialized with model: {OLLAMA_EMBEDDING_MODEL}")
                    
                except Exception:
                    logger.warning(f"Failed to initialize Ollama with model: {OLLAMA_EMBEDDING_MODEL}")
                
            except Exception as e:
                logger.warning(f"Ollama embeddings not available: {e} - ensure Ollama is running")
                
        except ImportError as e:
            logger.error(f"Failed to import required packages: {e}")
        except Exception as e:
            logger.error(f"Error initializing embedding providers: {e}")
        
    def generate_embeddings(self, text: str, model_type: str = "ollama") -> Optional[List[float]]:
        """
        Generate embeddings for text using specified provider.
        
        Args:
            text: Text to generate embeddings for
            model_type: "ollama" or "gemini" - defaults to "ollama"
            
        Returns:
            List[float]: Embedding vector, or None if generation fails
        """
        try:
            if model_type == "gemini" and self.gemini_embeddings:
                return self.gemini_embeddings.embed_query(text)
            elif model_type == "ollama" and self.ollama_embeddings:
                return self.ollama_embeddings.embed_query(text)
            else:
                # Fallback to dummy vector if no providers are available
                logger.warning(f"Embedding model {model_type} not available, using dummy vector")
                return [0.1] * 384  # 384-dimensional dummy vector
                
        except Exception as e:
            logger.error(f"Error generating embeddings with {model_type}: {e}")
            return None
    
    def store_embeddings(self, project_id: str, text: str, source_url: str, 
                        video_id: Optional[str] = None, 
                        embedding_model: str = "ollama",
                        metadata: Optional[dict] = None) -> bool:
        """
        Store text embeddings in Qdrant for a specific project with enhanced metadata.
        
        Args:
            project_id: Project ID to associate with the embeddings
            text: Text content to store
            source_url: Source URL of the content
            video_id: Database video ID for tracking (required for video content)
            embedding_model: "ollama" or "gemini" - defaults to "ollama"
            metadata: Additional metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate embeddings with specified model
            embeddings = self.generate_embeddings(text, embedding_model)
            if not embeddings:
                return False
            
            # Ensure collection exists
            collection_name = f"project_{project_id}"
            if not self.client.collection_exists(collection_name):
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=len(embeddings), distance=Distance.COSINE)
                )
            
            # Prepare enhanced metadata with video_id and embedding_model
            point_metadata = {
                "project_id": project_id,
                "source_url": source_url,
                "text": text[:1000],  # Store first 1000 chars for reference
                "embedding_model": embedding_model,
                "video_id": video_id or "unknown"  # Always include video_id
            }
            if metadata:
                point_metadata.update(metadata)
            
            # Create point ID from text hash (simplified)
            point_id = hash(text) % (2**63 - 1)  # Simple hash for demo
            
            # Store in Qdrant
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embeddings,
                        payload=point_metadata
                    )
                ]
            )
            
            logger.info(f"Stored embeddings for project {project_id} with model {embedding_model}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing embeddings for project {project_id}: {e}")
            return False
    
    def retrieve_knowledge(self, project_id: str, query: str, limit: int = 5,
                          filter_conditions: Optional[Dict[str, Any]] = None,
                          embedding_model: str = "gemini") -> List[dict]:
        """
        Retrieve relevant knowledge from Qdrant based on query with optional filtering.
        
        Args:
            project_id: Project ID to search in
            query: Search query
            limit: Maximum number of results to return
            filter_conditions: Dictionary of field:value pairs to filter results by metadata
            embedding_model: Embedding model to use for query ("gemini" or "ollama")
            
        Returns:
            List[dict]: List of relevant knowledge items with metadata
        """
        try:
            collection_name = f"project_{project_id}"
            
            # Check if collection exists
            if not self.client.collection_exists(collection_name):
                return []
            
            # Generate query embeddings with specified model
            query_embedding = self.generate_embeddings(query, embedding_model)
            if not query_embedding:
                return []
            
            # Build Qdrant filter from conditions
            qdrant_filter = None
            if filter_conditions:
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
                qdrant_filter = Filter(must=conditions)
            
            # Search in Qdrant with optional filter
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True,
                query_filter=qdrant_filter
            )
            
            # Format results with enhanced metadata
            results = []
            for hit in search_result:
                results.append({
                    "score": hit.score,
                    "text": hit.payload.get("text", ""),
                    "source_url": hit.payload.get("source_url", ""),
                    "project_id": hit.payload.get("project_id", ""),
                    "embedding_model": hit.payload.get("embedding_model", "unknown"),
                    "video_id": hit.payload.get("video_id", "unknown")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving knowledge for project {project_id}: {e}")
            return []
    
    def delete_project_knowledge(self, project_id: str) -> bool:
        """
        Delete all knowledge items for a specific project.
        
        Args:
            project_id: Project ID to delete knowledge for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection_name = f"project_{project_id}"
            
            if self.client.collection_exists(collection_name):
                self.client.delete_collection(collection_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting knowledge for project {project_id}: {e}")
            return False

# Global RAG service instance
rag_service = RAGService()

# Convenience functions (maintain backward compatibility)
def generate_embeddings(text: str, model_type: str = "ollama") -> Optional[List[float]]:
    """Generate embeddings for text using specified provider."""
    return rag_service.generate_embeddings(text, model_type)

def store_embeddings(project_id: str, text: str, source_url: str, metadata: Optional[dict] = None) -> bool:
    """Store text embeddings in Qdrant (backward compatible)."""
    # Extract video_id and embedding_model from metadata if provided
    video_id = metadata.pop("video_id", None) if metadata else None
    embedding_model = metadata.pop("embedding_model", "ollama") if metadata else "ollama"
    
    return rag_service.store_embeddings(
        project_id, text, source_url, 
        video_id=video_id, 
        embedding_model=embedding_model,
        metadata=metadata
    )

def store_embeddings_with_metadata(project_id: str, text: str, source_url: str, 
                                  video_id: Optional[str] = None, 
                                  embedding_model: str = "ollama",
                                  metadata: Optional[dict] = None) -> bool:
    """Store text embeddings with enhanced metadata tracking."""
    return rag_service.store_embeddings(
        project_id, text, source_url, 
        video_id=video_id, 
        embedding_model=embedding_model,
        metadata=metadata
    )

def retrieve_knowledge(project_id: str, query: str, limit: int = 5) -> List[dict]:
    """Retrieve relevant knowledge from Qdrant (backward compatible)."""
    return rag_service.retrieve_knowledge(project_id, query, limit, embedding_model="gemini")

def retrieve_knowledge_with_filter(project_id: str, query: str, limit: int = 5,
                                 filter_conditions: Optional[Dict[str, Any]] = None,
                                 embedding_model: str = "gemini") -> List[dict]:
    """Retrieve relevant knowledge from Qdrant with optional filtering."""
    return rag_service.retrieve_knowledge(project_id, query, limit, filter_conditions, embedding_model)

def delete_project_knowledge(project_id: str) -> bool:
    """Delete all knowledge items for a project."""
    return rag_service.delete_project_knowledge(project_id)
