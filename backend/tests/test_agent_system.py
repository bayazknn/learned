#!/usr/bin/env python3
"""
Test script for the LangGraph agent system.
This script tests the three main tools and the research agent integration.
"""

import sys
import os
from uuid import UUID

# Add the current directory to Python path for imports
sys.path.insert(0, '/home/kenan/Desktop/ai-apps/learned/backend')

from archive.agents.research_agent_manager import create_research_agent, process_research_query
from tools.retriever_tool import retriever_tool
from tools.tavily_search_tool import tavily_search_tool
from tools.transcript_tool import transcript_tool

def test_individual_tools():
    """Test each tool individually"""
    print("🧪 Testing individual tools...")
    
    # Test retriever tool
    try:
        print("\n1. Testing retriever tool...")
        results = retriever_tool.invoke({
            "query": "machine learning basics", 
            "project_id": "test-project",
            "video_ids": ["test-video-1"]
        })
        print(f"   ✅ Retriever tool working - found {len(results)} results")
        if results:
            print(f"   Sample result: {results[0].get('text', '')[:100]}...")
    except Exception as e:
        print(f"   ❌ Retriever tool failed: {e}")
    
    # Test Tavily search tool
    try:
        print("\n2. Testing Tavily search tool...")
        results = tavily_search_tool.invoke({
            "query": "latest AI developments 2024",
            "max_results": 2
        })
        print(f"   ✅ Tavily search tool working - found {len(results)} results")
        if results:
            print(f"   Sample result: {results[0].get('title', 'No title')}")
    except Exception as e:
        print(f"   ❌ Tavily search tool failed: {e}")
    
    # Test transcript tool (this might fail without actual videos)
    try:
        print("\n3. Testing transcript tool...")
        # Use a valid UUID format for testing
        results = transcript_tool.invoke({
            "project_id": "test-project",
            "video_ids": ["12345678-1234-5678-1234-567812345678"]  # Valid UUID format
        })
        print(f"   ✅ Transcript tool working - found {results.get('transcripts_found', 0)} transcripts")
    except Exception as e:
        print(f"   ❌ Transcript tool failed (expected without real videos): {e}")

def test_research_agent():
    """Test the research agent integration"""
    print("\n🧪 Testing research agent...")
    
    try:
        # Create a research agent
        agent = create_research_agent(
            project_id="test-project-123",
            project_name="Test Project",
            video_count=3
        )
        print("   ✅ Research agent created successfully")
        print(f"   Available tools: {agent.get_available_tools()}")
        
        # Test a simple query
        print("\n4. Testing agent with simple query...")
        result = process_research_query(
            query="Hello! Can you introduce yourself and explain what tools you have access to?",
            project_id="test-project-123"
        )
        
        if result['success']:
            print("   ✅ Agent query successful!")
            print(f"   Response: {result['response'][:200]}...")
            if result.get('tool_thoughts'):
                print(f"   Tool thoughts: {result['tool_thoughts']}")
        else:
            print(f"   ❌ Agent query failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Research agent test failed: {e}")

def test_api_endpoints():
    """Test the API endpoints"""
    print("\n🧪 Testing API endpoints (simulated)...")
    
    try:
        # Simulate a chat request
        from backend.api.endpoints.chat import ChatRequest
        from uuid import uuid4
        
        test_request = ChatRequest(
            message="What can you help me with?",
            project_id=uuid4(),
            video_ids=None,
            tools=None
        )
        
        print("   ✅ Chat request model validated")
        print(f"   Message: {test_request.message}")
        print(f"   Project ID: {test_request.project_id}")
        
    except Exception as e:
        print(f"   ❌ API test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting LangGraph Agent System Tests")
    print("=" * 50)
    
    test_individual_tools()
    test_research_agent()
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("\nNext steps:")
    print("1. Start the FastAPI server: uvicorn backend.main:app --reload")
    print("2. Test the chat endpoint at: POST /chat/research")
    print("3. Check available tools at: GET /chat/tools")
    print("4. Integrate with the React frontend chat component")

if __name__ == "__main__":
    main()
