#!/usr/bin/env python3
"""
Test script to verify the LangGraph agent fix for CancelledError.
This script tests the async retrieval functionality without the problematic run_in_executor.
"""
import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append('backend')

from backend.tools.retriever_tool import async_retriever_tool
from backend.agents.langgraph_agent import LangGraphAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_async_retriever():
    """Test the async retriever tool directly"""
    try:
        logger.info("Testing async retriever tool...")

        # Test with a simple query
        results = await async_retriever_tool(
            query="test query",
            project_id="test_project",
            video_ids=None
        )

        logger.info(f"Async retriever returned {len(results)} results")
        return True

    except Exception as e:
        logger.error(f"Async retriever test failed: {e}")
        return False

async def test_langgraph_agent():
    """Test the LangGraph agent initialization and basic functionality"""
    try:
        logger.info("Testing LangGraph agent...")

        agent = LangGraphAgent()

        # Test initialization
        await agent.initialize()
        logger.info("LangGraph agent initialized successfully")

        # Test basic query processing (this might fail if no data exists, but shouldn't crash)
        try:
            result = await agent.process_query(
                query="test query",
                project_id="test_project",
                thread_id="test_thread"
            )
            logger.info(f"LangGraph query processing completed: {result.get('success', False)}")
        except Exception as e:
            logger.warning(f"Query processing failed (expected if no data): {e}")

        await agent.cleanup()
        return True

    except Exception as e:
        logger.error(f"LangGraph agent test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("Starting LangGraph fix verification tests...")

    # Test 1: Async retriever
    test1_passed = await test_async_retriever()

    # Test 2: LangGraph agent
    test2_passed = await test_langgraph_agent()

    if test1_passed and test2_passed:
        logger.info("✅ All tests passed! The CancelledError fix appears to be working.")
        return 0
    else:
        logger.error("❌ Some tests failed. The fix may need additional work.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
