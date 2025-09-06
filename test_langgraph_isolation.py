#!/usr/bin/env python3
"""
Test script to isolate whether Arize Phoenix is causing LangGraph streaming issues.
Tests both with and without Phoenix instrumentation to identify the root cause.
"""

import asyncio
import sys
import os
import logging
from typing import List, Dict, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_langgraph_without_phoenix():
    """Test LangGraph streaming without Phoenix instrumentation"""
    print("🧪 Testing LangGraph WITHOUT Phoenix...")

    try:
        # Temporarily disable Phoenix by not importing it
        # Import LangGraph agent directly
        from backend.agents.langgraph_agent import LangGraphAgent

        # Create agent instance
        agent = LangGraphAgent()

        # Test thread persistence - use same thread ID for multiple runs
        thread_id = "test-thread-123"

        print(f"  📝 Using thread ID: {thread_id}")

        # First run
        print("  🔄 First run...")
        chunks1 = []
        async for chunk in agent.process_query_streaming(
            query="What is machine learning?",
            project_id="test-project",
            thread_id=thread_id,
            query_generate_llm_model="gemini",
            chat_llm_model="gemini"
        ):
            chunks1.append(chunk)
            if chunk.get("type") == "done":
                break

        print(f"  ✅ First run completed with {len(chunks1)} chunks")

        # Second run with same thread
        print("  🔄 Second run (same thread)...")
        chunks2 = []
        async for chunk in agent.process_query_streaming(
            query="Can you explain this in simpler terms?",
            project_id="test-project",
            thread_id=thread_id,
            query_generate_llm_model="gemini",
            chat_llm_model="gemini"
        ):
            chunks2.append(chunk)
            if chunk.get("type") == "done":
                break

        print(f"  ✅ Second run completed with {len(chunks2)} chunks")

        # Check chat history
        print("  📚 Checking chat history...")
        history = await agent.get_chat_history(thread_id)
        print(f"  📊 Chat history has {len(history)} entries")

        # Cleanup
        await agent.cleanup()

        return {
            "success": True,
            "chunks1": len(chunks1),
            "chunks2": len(chunks2),
            "history_length": len(history),
            "error": None
        }

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return {
            "success": False,
            "chunks1": 0,
            "chunks2": 0,
            "history_length": 0,
            "error": str(e)
        }

async def test_langgraph_with_phoenix():
    """Test LangGraph streaming with Phoenix instrumentation"""
    print("🔭 Testing LangGraph WITH Phoenix...")

    try:
        # Import Phoenix first to enable instrumentation
        from backend.trace.arize import tracer_provider
        print("  ✅ Phoenix tracer provider loaded")

        # Import LangGraph agent
        from backend.agents.langgraph_agent import LangGraphAgent

        # Create agent instance
        agent = LangGraphAgent()

        # Test thread persistence - use same thread ID for multiple runs
        thread_id = "test-thread-phoenix-456"

        print(f"  📝 Using thread ID: {thread_id}")

        # First run
        print("  🔄 First run...")
        chunks1 = []
        async for chunk in agent.process_query_streaming(
            query="What is machine learning?",
            project_id="test-project",
            thread_id=thread_id,
            query_generate_llm_model="gemini",
            chat_llm_model="gemini"
        ):
            chunks1.append(chunk)
            if chunk.get("type") == "done":
                break

        print(f"  ✅ First run completed with {len(chunks1)} chunks")

        # Second run with same thread
        print("  🔄 Second run (same thread)...")
        chunks2 = []
        async for chunk in agent.process_query_streaming(
            query="Can you explain this in simpler terms?",
            project_id="test-project",
            thread_id=thread_id,
            query_generate_llm_model="gemini",
            chat_llm_model="gemini"
        ):
            chunks2.append(chunk)
            if chunk.get("type") == "done":
                break

        print(f"  ✅ Second run completed with {len(chunks2)} chunks")

        # Check chat history
        print("  📚 Checking chat history...")
        history = await agent.get_chat_history(thread_id)
        print(f"  📊 Chat history has {len(history)} entries")

        # Cleanup
        await agent.cleanup()

        return {
            "success": True,
            "chunks1": len(chunks1),
            "chunks2": len(chunks2),
            "history_length": len(history),
            "error": None
        }

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return {
            "success": False,
            "chunks1": 0,
            "chunks2": 0,
            "history_length": 0,
            "error": str(e)
        }

async def test_simple_streaming():
    """Test simple async generator without LangGraph to isolate the issue"""
    print("🔄 Testing simple async generator...")

    try:
        async def simple_generator():
            for i in range(5):
                yield {"chunk": i, "data": f"test_data_{i}"}

        chunks = []
        async for chunk in simple_generator():
            chunks.append(chunk)

        print(f"  ✅ Simple generator completed with {len(chunks)} chunks")

        return {
            "success": True,
            "chunks": len(chunks),
            "error": None
        }

    except Exception as e:
        print(f"  ❌ Simple generator test failed: {e}")
        return {
            "success": False,
            "chunks": 0,
            "error": str(e)
        }

async def main():
    """Run all tests and compare results"""
    print("🚀 Starting LangGraph Isolation Tests...\n")

    # Test 1: Simple async generator
    simple_result = await test_simple_streaming()

    # Test 2: LangGraph without Phoenix
    print("\n" + "="*50)
    without_phoenix = await test_langgraph_without_phoenix()

    # Test 3: LangGraph with Phoenix
    print("\n" + "="*50)
    with_phoenix = await test_langgraph_with_phoenix()

    # Results comparison
    print("\n" + "="*60)
    print("📊 TEST RESULTS COMPARISON")
    print("="*60)

    print("Simple Async Generator:")
    print(f"  Success: {'✅' if simple_result['success'] else '❌'}")
    print(f"  Chunks: {simple_result['chunks']}")
    if simple_result['error']:
        print(f"  Error: {simple_result['error']}")

    print("\nLangGraph WITHOUT Phoenix:")
    print(f"  Success: {'✅' if without_phoenix['success'] else '❌'}")
    print(f"  First run chunks: {without_phoenix['chunks1']}")
    print(f"  Second run chunks: {without_phoenix['chunks2']}")
    print(f"  Chat history entries: {without_phoenix['history_length']}")
    if without_phoenix['error']:
        print(f"  Error: {without_phoenix['error']}")

    print("\nLangGraph WITH Phoenix:")
    print(f"  Success: {'✅' if with_phoenix['success'] else '❌'}")
    print(f"  First run chunks: {with_phoenix['chunks1']}")
    print(f"  Second run chunks: {with_phoenix['chunks2']}")
    print(f"  Chat history entries: {with_phoenix['history_length']}")
    if with_phoenix['error']:
        print(f"  Error: {with_phoenix['error']}")

    # Analysis
    print("\n" + "="*60)
    print("🔍 ANALYSIS")
    print("="*60)

    if simple_result['success'] and not without_phoenix['success']:
        print("⚠️  Issue is NOT with Phoenix - LangGraph itself has problems")
    elif simple_result['success'] and without_phoenix['success'] and not with_phoenix['success']:
        print("🎯 Issue IS with Phoenix - it interferes with LangGraph streaming")
    elif simple_result['success'] and without_phoenix['success'] and with_phoenix['success']:
        print("✅ No issues detected - both configurations work")
    else:
        print("❓ Complex issue - needs further investigation")

    # Chat history analysis
    if without_phoenix['history_length'] > 0 and with_phoenix['history_length'] == 0:
        print("💔 Chat history is BROKEN with Phoenix - state not persisting")
    elif without_phoenix['history_length'] > 0 and with_phoenix['history_length'] > 0:
        print("✅ Chat history works in both configurations")
    elif without_phoenix['history_length'] == 0:
        print("⚠️  Chat history not working even without Phoenix")

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
