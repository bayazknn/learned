from typing import List, Optional, Dict, Any
import logging
import uuid
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import SparseVector
from llama_index.core import Settings
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores import VectorStoreQuery
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding   
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core import Document
from llama_index.core import VectorStoreIndex
from llama_index.core import Settings
from llama_index.core.postprocessor import SentenceTransformerRerank
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from backend.trace.arize import tracer_provider

logger = logging.getLogger(__name__)

OLLAMA_EMBEDDING_MODEL = "all-minilm:22m"

class RAGServiceLlamaIndex:
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """
        Initialize LlamaIndex-based RAG service with Qdrant client.
        
        Args:
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
        """
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.aclient = AsyncQdrantClient(host=qdrant_host, port=qdrant_port)
        # Initialize embedding providers
        self.gemini_embeddings = None
        self.ollama_embeddings = None
        self.qdrant_fastembed = None
        self.reranker = None
        self._initialize_embedding_providers()
        Settings.llm = Ollama(model="gemma3:270m", request_timeout=120)
        LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
        
        
    def _initialize_embedding_providers(self):
        """Initialize embedding providers based on available configuration"""
        try:
            # Try to import settings from backend.config
            try:
                from backend.config import settings
                has_settings = True
            except ImportError:
                has_settings = False
                logger.warning("Backend config not available - using environment variables")
            
            # Initialize Google GenAI if API key is available
            google_api_key = None
            if has_settings:
                google_api_key = getattr(settings, 'GOOGLE_API_KEY', None)
            else:
                import os
                google_api_key = os.environ.get('GOOGLE_API_KEY')
            
            if google_api_key:
                self.gemini_embeddings = GoogleGenAIEmbedding(
                    model_name="text-embedding-004",
                    api_key=google_api_key
                )
                logger.info("Google GenAI embeddings initialized successfully")
            else:
                logger.warning("GOOGLE_API_KEY not found - Google GenAI embeddings disabled")
                
            # Initialize Ollama embeddings
            try:
                self.ollama_embeddings = OllamaEmbedding(
                    model_name=OLLAMA_EMBEDDING_MODEL,
                    base_url="http://localhost:11434",
                    request_timeout=600
                )
                logger.info(f"Ollama embeddings initialized with model: {OLLAMA_EMBEDDING_MODEL}")
            except Exception as e:
                logger.warning(f"Ollama embeddings not available: {e} - ensure Ollama is running")

            # Initialize Qdrant FastEmbed for dense embeddings
            try:
                self.qdrant_fastembed = FastEmbedEmbedding(
                    model_name="BAAI/bge-small-en"
                )
                logger.info("Qdrant FastEmbed dense embeddings initialized successfully")
            except Exception as e:
                logger.warning(f"Qdrant FastEmbed not available: {e}")

            # Initialize reranker
            try:
                self.reranker = SentenceTransformerRerank(
                    model="cross-encoder/ms-marco-TinyBERT-L-2-v2",
                    top_n=3
                )
                logger.info("TinyBERT reranker initialized successfully")
            except Exception as e:
                logger.warning(f"TinyBERT reranker not available: {e}")

        except ImportError as e:
            logger.error(f"Failed to import required packages: {e}")
        except Exception as e:
            logger.error(f"Error initializing embedding providers: {e}")
        
    def get_embedding_model(self, model_type: str = "qdrant_bm25"):
        """
        Get the appropriate embedding model instance.

        Args:
            model_type: "qdrant_bm25", "ollama", or "gemini" - defaults to "qdrant_bm25"

        Returns:
            Embedding model instance or None if not available
        """
        if model_type == "qdrant_bm25" and self.qdrant_fastembed:
            return self.qdrant_fastembed
        elif model_type == "gemini" and self.gemini_embeddings:
            return self.gemini_embeddings
        elif model_type == "ollama" and self.ollama_embeddings:
            return self.ollama_embeddings
        else:
            logger.warning(f"Embedding model {model_type} not available")
            return None
    
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
            embed_model = self.get_embedding_model(model_type)
            if embed_model:
                logger.info(f"Generating embeddings using {model_type}")
                return embed_model.get_text_embedding(text)
            else:
                # Fallback to dummy vector if no providers are available
                logger.warning(f"Embedding model {model_type} not available, using dummy vector")
                return [0.1] * 384  # 384-dimensional dummy vector
                
        except Exception as e:
            logger.error(f"Error generating embeddings with {model_type}: {e}")
            return None
    
    def store_embeddings(self, project_id: str, text: str, source_url: str,
                        video_id: Optional[str] = None,
                        embedding_model: str = "qdrant_bm25",
                        metadata: Optional[dict] = None) -> bool:
        """
        Store text embeddings in Qdrant using LlamaIndex IngestionPipeline.
        
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
            embed_model = self.get_embedding_model(embedding_model)
            if not embed_model:
                return False
            
            # Create Qdrant vector store for the project with hybrid support
            collection_name = f"project_{project_id}"
            vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=collection_name,
                enable_hybrid=True,
                fastembed_sparse_model="Qdrant/bm25"
            )
            
            # Prepare comprehensive metadata
            node_metadata = {
                "project_id": project_id,
                "source_url": source_url,
                "video_id": video_id or "unknown",
                "embedding_model": embedding_model,
                "id": str(uuid.uuid4())
            }
            if metadata:
                node_metadata.update(metadata)
            
            # Create document with metadata
            text_documnet = Document(
                text=text,
                metadata=node_metadata
            )
            
            # Create ingestion pipeline with semantic chunking
            pipeline = IngestionPipeline(
                transformations=[
                    # SentenceSplitter(chunk_size=512, chunk_overlap=50),
                    # embed_model
                    SemanticSplitterNodeParser(buffer_size=1, 
                                               breakpoint_percentile_threshold=95, 
                                               embed_model=embed_model),
                    embed_model
                ],
                vector_store=vector_store
            )
            
            # Process and store the node
            logger.info(f"Storing embeddings for project {project_id} using {embedding_model}")
            nodes = pipeline.run(documents=[text_documnet])
            
            logger.info(f"Stored {len(nodes)} embeddings for project {project_id} with model {embedding_model}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing embeddings for project {project_id}: {e}")
            return False
    
    def retrieve_knowledge(self, project_id: str, query: str, limit: int = 2,
                          filter_conditions: Optional[Dict[str, Any]] = None,
                          embedding_model: str = "qdrant_bm25") -> List[dict]:
        """
        Retrieve relevant knowledge from Qdrant using hybrid retrieval with reranking.

        Args:
            project_id: Project ID to search in
            query: Search query
            limit: Maximum number of results to return
            filter_conditions: Dictionary of field:value pairs to filter results by metadata
            embedding_model: Embedding model to use for query ("qdrant_bm25", "ollama", or "gemini")

        Returns:
            List[dict]: List of relevant knowledge items with metadata
        """
        try:
            collection_name = f"project_{project_id}"

            # Check if collection exists
            if not self.client.collection_exists(collection_name):
                logger.warning(f"Collection {collection_name} does not exist")
                return []

            # Create Qdrant vector store with hybrid search enabled
            vector_store = QdrantVectorStore(
                client=self.client,
                aclient=self.aclient,
                collection_name=collection_name,
                enable_hybrid=True,
                fastembed_sparse_model="Qdrant/bm25",
                prefer_grpc=True,
            )

            # Create index with the appropriate embedding model
            embed_model = self.get_embedding_model(embedding_model)
            if not embed_model:
                logger.warning(f"Embedding model {embedding_model} not available, falling back to qdrant_bm25")
                embed_model = self.get_embedding_model("qdrant_bm25")

            loaded_index = VectorStoreIndex.from_vector_store(
                vector_store,
                embed_model=embed_model,
            )

            logger.info(f"Retrieving knowledge for query: '{query}' using {embedding_model} model")

            # Create query engine with reranking
            query_engine = loaded_index.as_query_engine(
                llm=GoogleGenAI(model="gemini-2.0-flash"),
                similarity_top_k=limit,
                #node_postprocessors=[self.reranker] if self.reranker else []
            )

            # Execute query
            response = query_engine.query(query)

            # Format results
            results = []
            if hasattr(response, 'source_nodes'):
                for node_with_score in response.source_nodes[:limit]:
                    results.append({
                        "score": node_with_score.score,
                        "text": node_with_score.node.text,
                        "source_url": node_with_score.node.metadata.get("source_url", ""),
                        "project_id": project_id,
                        "embedding_model": embedding_model,
                        "video_id": node_with_score.node.metadata.get("video_id", "unknown"),
                    })
            else:
                # Fallback if no source_nodes available
                logger.warning("No source nodes found in response")
                results = []

            logger.info(f"Retrieved {len(results)} results after reranking")
            return results

        except Exception as e:
            logger.error(f"Error retrieving knowledge for project {project_id}: {e}")
            return []
    
    def _build_qdrant_filter(self, filter_conditions: Dict[str, Any]):
        """
        Build Qdrant filter from conditions dictionary.
        
        Args:
            filter_conditions: Dictionary of field:value pairs
            
        Returns:
            Qdrant filter object
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        conditions = []
        for key, value in filter_conditions.items():
            if isinstance(value, list):
                # Handle list values (e.g., multiple video_ids)
                for item in value:
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=item)))
            else:
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
        
        return Filter(must=conditions)
    
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
rag_service_llama = RAGServiceLlamaIndex()

# Convenience functions (maintain same signatures as original)
def generate_embeddings(text: str, model_type: str = "ollama") -> Optional[List[float]]:
    """Generate embeddings for text using specified provider."""
    return rag_service_llama.generate_embeddings(text, model_type)

def store_embeddings(project_id: str, text: str, source_url: str, metadata: Optional[dict] = None) -> bool:
    """Store text embeddings in Qdrant (backward compatible)."""
    # Extract video_id and embedding_model from metadata if provided
    video_id = metadata.pop("video_id", None) if metadata else None
    embedding_model = metadata.pop("embedding_model", "qdrant_bm25") if metadata else "qdrant_bm25"
    
    return rag_service_llama.store_embeddings(
        project_id, text, source_url, 
        video_id=video_id, 
        embedding_model=embedding_model,
        metadata=metadata
    )

def store_embeddings_with_metadata(project_id: str, text: str, source_url: str,
                                  video_id: Optional[str] = None,
                                  embedding_model: str = "qdrant_bm25",
                                  metadata: Optional[dict] = None) -> bool:
    """Store text embeddings with enhanced metadata tracking."""
    return rag_service_llama.store_embeddings(
        project_id, text, source_url,
        video_id=video_id,
        embedding_model=embedding_model,
        metadata=metadata
    )

def retrieve_knowledge(project_id: str, query: str, limit: int = 5) -> List[dict]:
    """Retrieve relevant knowledge from Qdrant (backward compatible)."""
    return rag_service_llama.retrieve_knowledge(project_id, query, limit, embedding_model="qdrant_bm25")

def retrieve_knowledge_with_filter(project_id: str, query: str, limit: int = 5,
                                 filter_conditions: Optional[Dict[str, Any]] = None,
                                 embedding_model: str = "qdrant_bm25") -> List[dict]:
    """Retrieve relevant knowledge from Qdrant with optional filtering."""
    return rag_service_llama.retrieve_knowledge(project_id, query, limit, filter_conditions, embedding_model)

def delete_project_knowledge(project_id: str) -> bool:
    """Delete all knowledge items for a project."""
    return rag_service_llama.delete_project_knowledge(project_id)
