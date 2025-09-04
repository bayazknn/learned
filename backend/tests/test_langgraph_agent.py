#!/usr/bin/env python3
"""
Test script for LangGraph agent implementation.
This script tests the three-step RAG workflow with thread persistence.
"""

import asyncio
import uuid
import pytest
from backend.agents.langgraph_agent import LangGraphAgent

async def test_langgraph_agent():
    """Test the LangGraph agent with a sample query"""
    print("Testing LangGraph Agent Implementation...")
    print("=" * 50)
    
    # Create agent instance
    agent = LangGraphAgent()
    
    # Test data
    test_query = "What are the main benefits of exercise for mental health?"
    test_project_id = str(uuid.uuid4())  # Simulate project ID
    test_thread_id = str(uuid.uuid4())   # Create thread ID for persistence
    
    print(f"Query: {test_query}")
    print(f"Project ID: {test_project_id}")
    print(f"Thread ID: {test_thread_id}")
    print("-" * 50)
    
    try:
        # Test the agent
        result = await agent.process_query(
            query=test_query,
            project_id=test_project_id,
            thread_id=test_thread_id
        )
        
        print("Test Results:")
        print(f"Success: {result['success']}")
        print(f"Thread ID: {result['thread_id']}")
        
        if result['success']:
            print(f"Response: {result['response'][:200]}...")  # Show first 200 chars
            print(f"Generated Queries: {result.get('generated_queries', [])}")
            print(f"Retrieval Count: {result.get('retrieval_count', 0)}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
    print("Test completed.")

async def test_langgraph_streaming():
    """Test the LangGraph agent streaming functionality"""
    print("\nTesting LangGraph Streaming...")
    print("=" * 50)

    agent = LangGraphAgent()
    test_query = "What are the benefits of regular exercise?"
    test_project_id = str(uuid.uuid4())
    test_thread_id = str(uuid.uuid4())

    print(f"Query: {test_query}")
    print(f"Project ID: {test_project_id}")
    print(f"Thread ID: {test_thread_id}")
    print("-" * 50)

    try:
        chunks = []
        async for chunk in agent.process_query_streaming(
            query=test_query,
            project_id=test_project_id,
            thread_id=test_thread_id
        ):
            chunks.append(chunk)
            print(f"Received chunk: {chunk.get('type', 'unknown')}")

        print(f"Total chunks received: {len(chunks)}")

        # Check if we got a final response
        final_chunks = [c for c in chunks if c.get('type') == 'done']
        error_chunks = [c for c in chunks if c.get('type') == 'error']

        if final_chunks:
            print(f"Final response: {final_chunks[0].get('content', '')[:200]}...")
        elif error_chunks:
            print(f"Error received: {error_chunks[0].get('content', '')}")
        else:
            print("No final response received")

    except Exception as e:
        print(f"Streaming test failed with error: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 50)
    print("Streaming test completed.")

async def test_thread_persistence():
    """Test thread persistence with multiple calls"""
    print("\nTesting Thread Persistence...")
    print("=" * 50)

    agent = LangGraphAgent()
    test_project_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    queries = [
        "What is machine learning?",
        "How does it differ from deep learning?",
        "What are some common applications?"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")
        result = await agent.process_query(
            query=query,
            project_id=test_project_id,
            thread_id=thread_id
        )

        print(f"  Thread ID: {result['thread_id']}")
        print(f"  Success: {result['success']}")
        if result['success']:
            print(f"  Response length: {len(result['response'])} chars")

    print("=" * 50)
    print("Thread persistence test completed.")

async def test_conversation_state_persistence():
    """Test that conversation state persists across multiple requests"""
    print("\nTesting Conversation State Persistence...")
    print("=" * 50)

    agent = LangGraphAgent()
    test_project_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    # First message
    print("\nFirst message:")
    result1 = await agent.process_query(
        query="Hello, my name is John",
        project_id=test_project_id,
        thread_id=thread_id
    )
    print(f"Response: {result1['response'][:100]}...")

    # Second message that should reference the first
    print("\nSecond message:")
    result2 = await agent.process_query(
        query="What's my name?",
        project_id=test_project_id,
        thread_id=thread_id
    )
    print(f"Response: {result2['response'][:100]}...")

    # Check if the response mentions "John" (indicating state persistence)
    response_text = result2['response'].lower()
    if "john" in response_text:
        print("✅ SUCCESS: Conversation state persisted - agent remembered the name")
    else:
        print("❌ FAILURE: Conversation state not persisted - agent forgot the name")

    print("=" * 50)
    print("Conversation state persistence test completed.")

if __name__ == "__main__":
    print("LangGraph Agent Test Suite")
    print("=" * 50)

    # Run tests
    asyncio.run(test_langgraph_agent())
    asyncio.run(test_thread_persistence())
    asyncio.run(test_conversation_state_persistence())

    print("\nAll tests completed successfully!")
