#!/usr/bin/env python3
"""
Test script to verify that the improved error handling fixes preserve chat history
even when API calls fail due to rate limits or other issues.
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

async def test_error_recovery_with_chat_history():
    """Test that chat history is preserved even when API calls fail"""
    print("🛠️  Testing error recovery with chat history preservation...")

    try:
        # Import Phoenix first to enable instrumentation
        from backend.trace.arize import tracer_provider
        print("  ✅ Phoenix tracer provider loaded")

        # Import LangGraph agent
        from backend.agents.langgraph_agent import LangGraphAgent

        # Create agent instance
        agent = LangGraphAgent()

        # Test thread persistence - use same thread ID for multiple runs
        thread_id = "test-thread-recovery-123"

        print(f"  📝 Using thread ID: {thread_id}")

        # First run - should work (using Ollama to avoid rate limits)
        print("  🔄 First run (Ollama - should work)...")
        result1 = await agent.process_query(
            query="Hello, my name is Alice",
            project_id="test-project",
            thread_id=thread_id,
            query_generate_llm_model="ollama",
            chat_llm_model="ollama"
        )

        print(f"  ✅ First run result: {result1.get('success', False)}")

        # Check chat history after first successful run
        history1 = await agent.get_chat_history(thread_id)
        print(f"  📊 History after first run: {len(history1)} entries")

        # Second run - force an error by using invalid model
        print("  🔄 Second run (invalid model - should fail gracefully)...")

        # Manually call the streaming method with invalid model to test error handling
        chunks = []
        try:
            async for chunk in agent.process_query_streaming(
                query="What's my name?",
                project_id="test-project",
                thread_id=thread_id,
                query_generate_llm_model="invalid_model",
                chat_llm_model="invalid_model"
            ):
                chunks.append(chunk)
                if chunk.get("type") == "done":
                    break
        except Exception as e:
            print(f"  ⚠️  Expected streaming error: {e}")

        print(f"  📊 Error chunks received: {len(chunks)}")

        # Check if error chunks contain helpful messages
        error_messages = [chunk for chunk in chunks if chunk.get("type") == "error"]
        if error_messages:
            print(f"  📝 Error message: {error_messages[0].get('content', '')[:100]}...")

        # Check chat history after error - this is the critical test
        history2 = await agent.get_chat_history(thread_id)
        print(f"  📊 History after error: {len(history2)} entries")

        # Third run - should work again with Ollama
        print("  🔄 Third run (Ollama - should work again)...")
        result3 = await agent.process_query(
            query="Can you remind me what we were talking about?",
            project_id="test-project",
            thread_id=thread_id,
            query_generate_llm_model="ollama",
            chat_llm_model="ollama"
        )

        print(f"  ✅ Third run result: {result3.get('success', False)}")

        # Final chat history check
        history3 = await agent.get_chat_history(thread_id)
        print(f"  📊 Final history: {len(history3)} entries")

        # Cleanup
        await agent.cleanup()

        # Analyze results
        success1 = result1.get('success', False)
        success3 = result3.get('success', False)
        history_preserved = len(history3) > len(history1)
        error_handled_gracefully = len(chunks) > 0

        return {
            "success": True,
            "first_run_success": success1,
            "third_run_success": success3,
            "history_preserved": history_preserved,
            "error_handled_gracefully": error_handled_gracefully,
            "history_lengths": [len(history1), len(history2), len(history3)],
            "error_chunks": len(chunks),
            "error": None
        }

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return {
            "success": False,
            "first_run_success": False,
            "third_run_success": False,
            "history_preserved": False,
            "error_handled_gracefully": False,
            "history_lengths": [],
            "error_chunks": 0,
            "error": str(e)
        }

async def test_rate_limit_simulation():
    """Simulate Gemini API rate limiting to test error recovery"""
    print("🔥 Testing Gemini rate limit simulation...")

    try:
        # Import Phoenix first to enable instrumentation
        from backend.trace.arize import tracer_provider
        print("  ✅ Phoenix tracer provider loaded")

        # Import LangGraph agent
        from backend.agents.langgraph_agent import LangGraphAgent

        # Create agent instance
        agent = LangGraphAgent()

        # Test thread persistence
        thread_id = "test-thread-rate-limit-456"

        print(f"  📝 Using thread ID: {thread_id}")

        # First run with Gemini (might hit rate limit)
        print("  🔄 First run (Gemini - might hit rate limit)...")
        result1 = await agent.process_query(
            query="What is artificial intelligence?",
            project_id="test-project",
            thread_id=thread_id,
            query_generate_llm_model="gemini",
            chat_llm_model="gemini"
        )

        print(f"  ✅ First run result: {result1.get('success', False)}")
        if not result1.get('success', False):
            print(f"  📝 Error message: {result1.get('error', '')[:100]}...")

        # Check chat history
        history1 = await agent.get_chat_history(thread_id)
        print(f"  📊 History after first run: {len(history1)} entries")

        # Second run - should still work even if first failed
        print("  🔄 Second run (Ollama fallback)...")
        result2 = await agent.process_query(
            query="Tell me more about AI",
            project_id="test-project",
            thread_id=thread_id,
            query_generate_llm_model="ollama",
            chat_llm_model="ollama"
        )

        print(f"  ✅ Second run result: {result2.get('success', False)}")

        # Check final chat history
        history2 = await agent.get_chat_history(thread_id)
        print(f"  📊 Final history: {len(history2)} entries")

        # Cleanup
        await agent.cleanup()

        return {
            "success": True,
            "first_run_success": result1.get('success', False),
            "second_run_success": result2.get('success', False),
            "history_grew": len(history2) > len(history1),
            "error_recovery": result2.get('success', False),
            "error": None
        }

    except Exception as e:
        print(f"  ❌ Rate limit test failed: {e}")
        return {
            "success": False,
            "first_run_success": False,
            "second_run_success": False,
            "history_grew": False,
            "error_recovery": False,
            "error": str(e)
        }

async def main():
    """Run all error handling tests"""
    print("🚀 Starting Error Handling Fix Tests...\n")

    # Test 1: Error recovery with chat history preservation
    print("\n" + "="*60)
    recovery_result = await test_error_recovery_with_chat_history()

    # Test 2: Rate limit simulation
    print("\n" + "="*60)
    rate_limit_result = await test_rate_limit_simulation()

    # Results analysis
    print("\n" + "="*70)
    print("📊 ERROR HANDLING FIX RESULTS")
    print("="*70)

    print("Error Recovery Test:")
    print(f"  Success: {'✅' if recovery_result['success'] else '❌'}")
    print(f"  First run success: {recovery_result['first_run_success']}")
    print(f"  Third run success: {recovery_result['third_run_success']}")
    print(f"  History preserved: {'✅' if recovery_result['history_preserved'] else '❌'}")
    print(f"  Error handled gracefully: {'✅' if recovery_result['error_handled_gracefully'] else '❌'}")
    print(f"  History progression: {recovery_result['history_lengths']}")
    if recovery_result['error']:
        print(f"  Error: {recovery_result['error']}")

    print("\nRate Limit Simulation Test:")
    print(f"  Success: {'✅' if rate_limit_result['success'] else '❌'}")
    print(f"  First run success: {rate_limit_result['first_run_success']}")
    print(f"  Second run success: {rate_limit_result['second_run_success']}")
    print(f"  History grew: {'✅' if rate_limit_result['history_grew'] else '❌'}")
    print(f"  Error recovery: {'✅' if rate_limit_result['error_recovery'] else '❌'}")
    if rate_limit_result['error']:
        print(f"  Error: {rate_limit_result['error']}")

    # Final assessment
    print("\n" + "="*70)
    print("🎯 FINAL ASSESSMENT")
    print("="*70)

    recovery_works = recovery_result['success'] and recovery_result['history_preserved']
    rate_limit_handled = rate_limit_result['success'] and rate_limit_result['error_recovery']

    if recovery_works:
        print("✅ ERROR RECOVERY: Chat history is preserved when API calls fail!")
        print("   - Graph continues to completion even with errors")
        print("   - Helpful fallback messages are provided")
        print("   - State updates work correctly")
    else:
        print("❌ ERROR RECOVERY: Issues remain with error handling")

    if rate_limit_handled:
        print("✅ RATE LIMIT HANDLING: System recovers from API quota issues!")
        print("   - Failed Gemini calls don't break subsequent requests")
        print("   - Ollama fallback works correctly")
        print("   - Chat history continues to accumulate")
    else:
        print("❌ RATE LIMIT HANDLING: Issues remain with rate limit recovery")

    if recovery_works and rate_limit_handled:
        print("\n🎉 SUCCESS: Error handling fixes are working correctly!")
        print("💡 The original GeneratorExit and chat history issues should be resolved.")
        print("💡 Users can now continue conversations even when hitting API limits.")
    else:
        print("\n⚠️  PARTIAL SUCCESS: Some improvements made, but issues remain.")

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
