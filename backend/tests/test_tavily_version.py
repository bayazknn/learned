#!/usr/bin/env python3
"""
Test to check Tavily client version and authentication methods
"""

import sys
sys.path.insert(0, '/home/kenan/Desktop/ai-apps/learned/backend')

import tavily
from tavily import TavilyClient
from config import settings

def test_tavily_version_and_auth():
    """Test different Tavily authentication methods"""
    print(f"API key: {settings.TAVILY_API_KEY}")
    
    # Test different initialization methods
    methods = [
        ("Direct API key", lambda: TavilyClient(api_key=settings.TAVILY_API_KEY)),
        ("Environment variable", lambda: TavilyClient()),
    ]
    
    for method_name, client_factory in methods:
        print(f"\nTesting {method_name}...")
        try:
            client = client_factory()
            response = client.search(query="test", max_results=1)
            print(f"✅ {method_name} successful! Results: {len(response.get('results', []))}")
        except Exception as e:
            print(f"❌ {method_name} failed: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("Tavily Version and Authentication Methods Test")
    print("=" * 60)
    
    test_tavily_version_and_auth()
    
    print("\n" + "=" * 60)
    print("Check if the Tavily client version matches expected authentication")
    print("=" * 60)
