#!/usr/bin/env python3
"""
Test script to identify the REAL issue with LangGraph streaming.
The isolation test showed Phoenix is NOT the problem. Let's test the actual failure scenarios.
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

async def test_with_ollama_model():
    """Test with Ollama model (no API limits)"""
    print("🧪 Testing with Ollama model (no API limits)...")

    try:
        # Import Phoenix first to enable instrumentation
        from backend.trace.arize import tracer_provider
        print("  ✅ Phoenix tracer provider loaded")

        # Import LangGraph agent
        from backend.agents.langgraph_agent import LangGraphAgent

        # Create agent instance
        agent = LangGraphAgent()

        # Test thread persistence - use same thread ID for multiple runs
        thread_id = "test-thread-ollama-789"

        print(f"  📝 Using thread ID: {thread_id}")

        # First run with Ollama
        print("  🔄 First run with Ollama...")
        chunks1 = []
        async for chunk in agent.process_query_streaming(
            query="What is machine learning?",
            project_id="test-project",
            thread_id=thread_id,
            query_generate_llm_model="ollama",
            chat_llm_model="ollama"
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
            query_generate_llm_model="ollama",
            chat_llm_model="ollama"
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

async def test_error_handling():
    """Test what happens when API calls fail"""
    print("🔥 Testing error handling scenarios...")

    try:
        # Import Phoenix first to enable instrumentation
        from backend.trace.arize import tracer_provider
        print("  ✅ Phoenix tracer provider loaded")

        # Import LangGraph agent
        from backend.agents.langgraph_agent import LangGraphAgent

        # Create agent instance
        agent = LangGraphAgent()

        # Test with invalid model to force errors
        thread_id = "test-thread-error-999"

        print(f"  📝 Using thread ID: {thread_id}")

        # Try with invalid model to see error handling
        print("  🔄 Testing with invalid model...")
        chunks = []
        try:
            async for chunk in agent.process_query_streaming(
                query="What is machine learning?",
                project_id="test-project",
                thread_id=thread_id,
                query_generate_llm_model="invalid_model",
                chat_llm_model="invalid_model"
            ):
                chunks.append(chunk)
                if chunk.get("type") == "done":
                    break
        except Exception as e:
            print(f"  ⚠️  Expected error occurred: {e}")

        print(f"  📊 Error handling produced {len(chunks)} chunks")

        # Check if state was still updated despite error
        print("  📚 Checking chat history after error...")
        history = await agent.get_chat_history(thread_id)
        print(f"  📊 Chat history has {len(history)} entries after error")

        # Cleanup
        await agent.cleanup()

        return {
            "success": True,
            "error_chunks": len(chunks),
            "history_after_error": len(history),
            "error": None
        }

    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        return {
            "success": False,
            "error_chunks": 0,
            "history_after_error": 0,
            "error": str(e)
        }

async def test_state_persistence():
    """Test if LangGraph state is properly persisted between runs"""
    print("💾 Testing state persistence...")

    try:
        # Import Phoenix first to enable instrumentation
        from backend.trace.arize import tracer_provider
        print("  ✅ Phoenix tracer provider loaded")

        # Import LangGraph agent
        from backend.agents.langgraph_agent import LangGraphAgent

        # Create agent instance
        agent = LangGraphAgent()

        # Test thread persistence
        thread_id = "test-thread-state-111"

        print(f"  📝 Using thread ID: {thread_id}")

        # First run
        print("  🔄 First run...")
        result1 = await agent.process_query(
            query="Hello, my name is John",
            project_id="test-project",
            thread_id=thread_id,
            query_generate_llm_model="ollama",
            chat_llm_model="ollama"
        )

        print(f"  ✅ First run result: {result1.get('success', False)}")

        # Check state after first run
        history1 = await agent.get_chat_history(thread_id)
        print(f"  📊 History after first run: {len(history1)} entries")

        # Second run - should remember context
        print("  🔄 Second run (should remember name)...")
        result2 = await agent.process_query(
            query="What's my name?",
            project_id="test-project",
            thread_id=thread_id,
            query_generate_llm_model="ollama",
            chat_llm_model="ollama"
        )

        print(f"  ✅ Second run result: {result2.get('success', False)}")

        # Check state after second run
        history2 = await agent.get_chat_history(thread_id)
        print(f"  📊 History after second run: {len(history2)} entries")

        # Cleanup
        await agent.cleanup()

        return {
            "success": True,
            "result1_success": result1.get('success', False),
            "result2_success": result2.get('success', False),
            "history1_length": len(history1),
            "history2_length": len(history2),
            "state_persisted": len(history2) > len(history1),
            "error": None
        }

    except Exception as e:
        print(f"  ❌ State persistence test failed: {e}")
        return {
            "success": False,
            "result1_success": False,
            "result2_success": False,
            "history1_length": 0,
            "history2_length": 0,
            "state_persisted": False,
            "error": str(e)
        }

async def main():
    """Run all tests to identify the real issue"""
    print("🚀 Starting Real Issue Investigation Tests...\n")

    # Test 1: Ollama model (no API limits)
    print("\n" + "="*50)
    ollama_result = await test_with_ollama_model()

    # Test 2: Error handling
    print("\n" + "="*50)
    error_result = await test_error_handling()

    # Test 3: State persistence
    print("\n" + "="*50)
    state_result = await test_state_persistence()

    # Results analysis
    print("\n" + "="*60)
    print("🔍 REAL ISSUE ANALYSIS")
    print("="*60)

    print("Ollama Model Test (no API limits):")
    print(f"  Success: {'✅' if ollama_result['success'] else '❌'}")
    print(f"  First run chunks: {ollama_result['chunks1']}")
    print(f"  Second run chunks: {ollama_result['chunks2']}")
    print(f"  Chat history entries: {ollama_result['history_length']}")
    if ollama_result['error']:
        print(f"  Error: {ollama_result['error']}")

    print("\nError Handling Test:")
    print(f"  Success: {'✅' if error_result['success'] else '❌'}")
    print(f"  Error chunks: {error_result['error_chunks']}")
    print(f"  History after error: {error_result['history_after_error']}")
    if error_result['error']:
        print(f"  Error: {error_result['error']}")

    print("\nState Persistence Test:")
    print(f"  Success: {'✅' if state_result['success'] else '❌'}")
    print(f"  First run success: {state_result['result1_success']}")
    print(f"  Second run success: {state_result['result2_success']}")
    print(f"  State persisted: {'✅' if state_result['state_persisted'] else '❌'}")
    if state_result['error']:
        print(f"  Error: {state_result['error']}")

    # Final analysis
    print("\n" + "="*60)
    print("🎯 ROOT CAUSE IDENTIFICATION")
    print("="*60)

    if ollama_result['success'] and ollama_result['history_length'] > 0:
        print("✅ LangGraph + Phoenix works fine with Ollama (no API limits)")
    else:
        print("❌ Issue exists even with Ollama")

    if error_result['history_after_error'] == 0:
        print("💔 ERROR FOUND: Chat history is NOT persisted when API calls fail!")
        print("   This explains why chat history is broken - failed Gemini API calls")
        print("   prevent proper state updates in LangGraph")
    else:
        print("✅ Error handling preserves chat history")

    if state_result['state_persisted']:
        print("✅ State persistence works correctly")
    else:
        print("❌ State persistence is broken")

    print("\n📋 CONCLUSION:")
    if not ollama_result['success'] or error_result['history_after_error'] == 0:
        print("🎯 The issue is NOT Phoenix - it's API failures breaking LangGraph state!")
        print("💡 Solution: Improve error handling in LangGraph agent")
    else:
        print("❓ Issue not clearly identified - needs further investigation")

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
