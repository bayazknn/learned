#!/usr/bin/env python3
"""
Test Tavily tool in isolation to see if authentication issue occurs
"""

import sys
sys.path.insert(0, '/home/kenan/Desktop/ai-apps/learned/backend')

from tools.tavily_search_tool import tavily_search_tool

def test_tavily_tool_isolation():
    """Test the Tavily tool directly to see if authentication issue occurs"""
    print("Testing Tavily tool in isolation...")
    
    try:
        # Test the tool directly
        results = tavily_search_tool.func("test query", max_results=1)
        print(f"✅ Tavily tool working! Results: {len(results)}")
        return True
    except Exception as e:
        print(f"❌ Tavily tool failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Tavily Tool Isolation Test")
    print("=" * 50)
    
    success = test_tavily_tool_isolation()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Tavily tool works in isolation!")
    else:
        print("❌ Tavily tool fails in isolation!")
    print("=" * 50)
