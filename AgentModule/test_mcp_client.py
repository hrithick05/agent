"""
Test client for the Web Scraping Bot MCP Server
This script demonstrates how to connect to and use the MCP server
"""

import asyncio
from fastmcp import Client

async def test_mcp_server():
    """Test the MCP server functionality"""
    
    # Connect to the MCP server (assuming it's running on stdio transport)
    # For HTTP transport, use: Client("http://localhost:8000/mcp")
    client = Client("http://127.0.0.1:8000/mcp")
    
    try:
        async with client:
            print("🔗 Connected to MCP server successfully!")
            
            # Test 1: Get available fields
            print("\n📋 Test 1: Getting available fields...")
            result = await client.call_tool("get_available_fields", {})
            print(f"Result: {result}")
            
            # Test 2: Get current state
            print("\n📊 Test 2: Getting current state...")
            result = await client.call_tool("get_current_state", {})
            print(f"Result: {result}")
            
            print("\n📊 Test 3: Reading HTML 1-20...")
            result = await client.call_tool("readHTML", {"start_line": 1, "end_line": 20})
            print(f"Result: {result}")

            # Test 3: Set a selector
            print("\n🛠️ Test 4: Setting a selector...")
            result = await client.call_tool("set_selector", {
                "field": "name",
                "selector_type": "css",
                "selectors": ["h1.title", "a.product-link"]
            })
            print(f"Result: {result}")
            
            print("\n✅ All tests completed successfully!")
            
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")

if __name__ == "__main__":
    print("🧪 Testing Web Scraping Bot MCP Server...")
    asyncio.run(test_mcp_server())
