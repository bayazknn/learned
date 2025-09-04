from typing import Dict, List, Any
from langchain_core.tools import tool
from tavily import TavilyClient
from backend.config import settings

@tool
def tavily_search_tool(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """
    Search the web using Tavily API to find external information and resources.
    Useful for finding current information, documentation, or additional context.
    
    Args:
        query: The search query to find information about
        max_results: Number of results to return (default: 3)
        
    Returns:
        List of search results with content, title, URL, and relevance score
    """
    try:
        # Create Tavily client inside the function to ensure proper authentication
        tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = tavily_client.search(query=query, max_results=max_results)
        results = []
        
        for result in response.get('results', []):
            results.append({
                "content": result.get('content', ''),
                "title": result.get('title', ''),
                "url": result.get('url', ''),
                "score": result.get('score', 0.0)
            })
        
        return results
    except Exception as e:
        # Fallback to empty results if Tavily fails
        print(f"Tavily search failed: {str(e)}")
        return []
