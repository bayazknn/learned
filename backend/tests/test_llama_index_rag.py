#!/usr/bin/env python3
"""
Test script for the new llama-index based RAG service.
This script tests the basic functionality of the RAG service with llama-index.
"""

import sys
import os
import logging

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_llama_index_rag():
    """Test the llama-index RAG service functionality."""
    try:
        from services.rag_llama_index import RAGServiceLlamaIndex
        
        # Initialize the service
        rag_service = RAGServiceLlamaIndex()
        
        # Test embedding generation
        test_text = "This is a test sentence for embedding generation."
        
        # Test Ollama embeddings (if available)
        ollama_embeddings = rag_service.generate_embeddings(test_text, "ollama")
        if ollama_embeddings:
            logger.info(f"Ollama embeddings generated successfully: {len(ollama_embeddings)} dimensions")
        else:
            logger.warning("Ollama embeddings not available - ensure Ollama is running")
        
        # Test Google GenAI embeddings (if configured)
        gemini_embeddings = rag_service.generate_embeddings(test_text, "gemini")
        if gemini_embeddings:
            logger.info(f"Google GenAI embeddings generated successfully: {len(gemini_embeddings)} dimensions")
        else:
            logger.warning("Google GenAI embeddings not available - check GOOGLE_API_KEY configuration")
        
        # Test storing embeddings
        test_project_id = "test_project_123"
        test_source_url = "https://example.com/test"
        test_content = """
        This is a test document about artificial intelligence and machine learning.
        AI has revolutionized many industries including healthcare, finance, and education.
        Machine learning algorithms can now process vast amounts of data and make predictions.
        """
        
        # Store with Ollama embeddings
        success = rag_service.store_embeddings(
            project_id=test_project_id,
            text=test_content,
            source_url=test_source_url,
            video_id="test_video_456",
            embedding_model="ollama",
            metadata={
                "title": "Test Document",
                "author": "Test Author",
                "category": "Technology"
            }
        )
        
        if success:
            logger.info("Successfully stored embeddings with Ollama")
        else:
            logger.error("Failed to store embeddings with Ollama")
        
        # Test retrieval
        query = "What industries has AI revolutionized?"
        results = rag_service.retrieve_knowledge(
            project_id=test_project_id,
            query=query,
            limit=3,
            embedding_model="ollama"
        )
        
        if results:
            logger.info(f"Retrieved {len(results)} results for query: '{query}'")
            for i, result in enumerate(results):
                logger.info(f"Result {i+1}: Score={result['score']:.4f}, Text='{result['text'][:100]}...'")
        else:
            logger.warning("No results retrieved - this might be expected if Ollama is not running")
        
        # Clean up test data
        rag_service.delete_project_knowledge(test_project_id)
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_llama_index_rag()
    sys.exit(0 if success else 1)
