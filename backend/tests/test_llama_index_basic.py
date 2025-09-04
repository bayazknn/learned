#!/usr/bin/env python3
"""
Basic test script for the llama-index based RAG service.
This test focuses on core functionality without requiring external services.
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_functionality():
    """Test basic functionality of the llama-index RAG service."""
    try:
        # Test imports
        from llama_index.core.ingestion import IngestionPipeline
        from llama_index.core.node_parser import SentenceSplitter
        from llama_index.core.schema import TextNode
        from llama_index.embeddings.ollama import OllamaEmbedding
        from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
        
        logger.info("All llama-index imports successful")
        
        # Test basic text node creation
        test_node = TextNode(
            text="This is a test node",
            metadata={"test": "value", "source": "test"}
        )
        logger.info(f"Text node created successfully: {test_node.text[:50]}...")
        
        # Test sentence splitter
        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        logger.info("Sentence splitter initialized successfully")
        
        # Test that we can create the RAG service class
        from services.rag_llama_index import RAGServiceLlamaIndex
        
        rag_service = RAGServiceLlamaIndex()
        logger.info("RAGServiceLlamaIndex initialized successfully")
        
        # Test embedding generation (should use dummy vectors since no external services)
        test_text = "This is a test sentence for embedding generation."
        
        embeddings = rag_service.generate_embeddings(test_text, "ollama")
        if embeddings:
            logger.info(f"Embeddings generated successfully: {len(embeddings)} dimensions")
        else:
            logger.error("Failed to generate embeddings")
            return False
        
        # Test the convenience functions
        from services.rag_llama_index import generate_embeddings, store_embeddings
        
        emb = generate_embeddings(test_text, "ollama")
        if emb:
            logger.info("Convenience function generate_embeddings works")
        else:
            logger.error("Convenience function generate_embeddings failed")
            return False
        
        logger.info("All basic functionality tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error during basic functionality testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        logger.info("✅ Basic functionality test completed successfully!")
    else:
        logger.error("❌ Basic functionality test failed!")
    sys.exit(0 if success else 1)
