from typing import List, Dict, Any, Optional, TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

class AgentState(TypedDict):
    """State for the LangGraph agent workflow"""
    
    # User input and conversation history
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Project context
    project_id: Optional[str]
    video_ids: Optional[List[str]]
    
    # Tool execution results
    retriever_results: Optional[List[Dict[str, Any]]]
    tavily_results: Optional[List[Dict[str, Any]]]
    transcript_results: Optional[Dict[str, Any]]
    
    # Agent decision making
    current_tool: Optional[str]
    tool_thoughts: Optional[str]
    
    # Final response
    final_response: Optional[str]
