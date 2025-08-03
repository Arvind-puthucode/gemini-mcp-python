#!/usr/bin/env python3
"""Direct test of Gemini API connection"""

import os
import asyncio
from src.gemini_mcp.gemini_client import GeminiClient
from src.gemini_mcp.orchestrator import TaskOrchestrator

async def test_direct():
    """Test Gemini connection directly"""
    try:
        print("🔧 Testing direct Gemini connection...")
        
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GEMINI_API_KEY")
        print(f"🔑 API Key loaded: {api_key[:10]}..." if api_key else "❌ No API key")
        
        # Create client
        client = GeminiClient()
        orchestrator = TaskOrchestrator(client)
        
        # Test simple ask
        result = await orchestrator.quick_ask("Hello! Respond with 'Direct test successful'")
        print(f"✅ Result: {result}")
        
        # Test file creation
        test_file = "/home/arvind/desi-feynman/gemini-mcp-python/test_output.py"
        with open(test_file, 'w') as f:
            f.write("# Test file created successfully\nprint('Hello World')\n")
        
        if os.path.exists(test_file):
            print(f"✅ File creation test passed: {test_file}")
        else:
            print(f"❌ File creation test failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct())