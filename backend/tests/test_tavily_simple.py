#!/usr/bin/env python3
"""
Simple test to verify Tavily API key works with the exact same setup as the tool
"""

import os
import sys
sys.path.insert(0, '/home/kenan/Desktop/ai-apps/learned/backend')

from tavily import TavilyClient
from config import settings

def test_exact_tavily_setup():
    """Test the exact same Tavily setup as used in the tool"""
    print(f"Testing Tavily API key: {settings.TAVILY_API_KEY}")
    
    try:
        # This is the exact same setup as in tavily_search_tool.py
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        
        # Test the exact same search call
        print("Testing Tavily search with exact same parameters...")
        response = client.search(query="test", max_results=3)
        
        print(f"Response keys: {list(response.keys())}")
        print(f"Results count: {len(response.get('results', []))}")
        
        if response and 'results' in response:
            print("✅ Tavily setup works correctly!")
            return True
        else:
            print("❌ Tavily search returned unexpected response")
            return False
            
    except Exception as e:
        print(f"❌ Tavily setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Tavily Exact Setup Test")
    print("=" * 50)
    
    success = test_exact_tavily_setup()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Tavily setup is working correctly!")
        print("The issue might be in how the tool is being called within LangGraph")
    else:
        print("❌ Tavily setup failed!")
    print("=" * 50)
