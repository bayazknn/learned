#!/usr/bin/env python3
"""
Test script to verify Tavily API authentication
"""

import os
import sys
sys.path.insert(0, '/home/kenan/Desktop/ai-apps/learned/backend')

from tavily import TavilyClient
from config import settings

def test_tavily_auth():
    """Test Tavily API authentication"""
    print(f"Testing Tavily API key: {settings.TAVILY_API_KEY}")
    
    try:
        # Test the Tavily client directly
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        
        # Try a simple search to verify authentication
        print("Testing Tavily search...")
        response = client.search(query="test", max_results=1)
        
        if response and 'results' in response:
            print("✅ Tavily authentication successful!")
            print(f"Found {len(response['results'])} results")
            return True
        else:
            print("❌ Tavily search returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Tavily authentication failed: {str(e)}")
        return False

def test_tavily_tool():
    """Test the Tavily search tool"""
    print("\nTesting Tavily search tool...")
    
    try:
        # Import the TavilySearchTool class directly
        from tools.tavily_search_tool import TavilySearchTool
        
        # Create an instance and test it
        tavily_tool = TavilySearchTool()
        results = tavily_tool.search("test", max_results=1)
        
        if results is not None:
            print("✅ Tavily search tool working!")
            print(f"Results: {len(results)}")
            return True
        else:
            print("❌ Tavily search tool returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Tavily search tool failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Tavily Authentication Test")
    print("=" * 50)
    
    auth_success = test_tavily_auth()
    tool_success = test_tavily_tool()
    
    print("\n" + "=" * 50)
    if auth_success and tool_success:
        print("✅ All Tavily tests passed!")
    else:
        print("❌ Some Tavily tests failed!")
        print("\nTroubleshooting steps:")
        print("1. Check if the Tavily API key is valid")
        print("2. Verify the key format (should start with 'tvly-')")
        print("3. Check if the API key has sufficient credits")
        print("4. Ensure the .env file doesn't override with an invalid key")
    print("=" * 50)
