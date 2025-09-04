from typing import Dict, List, Optional, Any
from langchain_core.tools import tool
from backend.services.rag_llama_index import retrieve_knowledge_with_filter
from backend.config import settings
import logging
logger = logging.getLogger(__name__)


@tool
def retriever_tool(query: str, project_id: str, video_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Retrieve relevant knowledge from Qdrant vector database for a specific project.
    Optionally filter by video_ids to search only within specific videos.
    
    Args:
        query: The search query
        project_id: The project ID to search within
        video_ids: Optional list of video IDs to filter the search by
        
    Returns:
        List of relevant knowledge items with metadata
    """
    filter_conditions = {"project_id": project_id}
    if video_ids:
        filter_conditions["video_id"] = video_ids
    
    results = retrieve_knowledge_with_filter(
        project_id=project_id,
        query=query,
        filter_conditions=filter_conditions,
        limit=5,
        embedding_model="qdrant_bm25"  # Use Qdrant BM25 for hybrid retrieval
    )

    # Convert numpy.float32 scores to regular Python floats for JSON serialization
    for result in results:
        if 'score' in result and hasattr(result['score'], 'item'):
            result['score'] = result['score'].item()
        elif 'score' in result:
            result['score'] = float(result['score'])

    # print(results)

    logger.info(f"Retrieved {len(results)} results for query '{query}' in project '{project_id}' with video_ids={video_ids}")
    logger.info(f"Retrieved result:\n {result}")
    return results
