"""Test script to run the Gemini-powered interactive scraping agent."""
import sys
import os

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from AgentModule.langgraph_agent import run_scraping_agent

def main():
    """Run the agent with a test URL."""
    print("Testing Gemini-Powered Interactive Scraping Agent")
    print("=" * 80)
    
    # Test with Flipkart
    test_url = "https://www.flipkart.com/search?q=phone+case"
    platform = "flipkart"
    
    print(f"Test Configuration:")
    print(f"   URL: {test_url}")
    print(f"   Platform: {platform}")
    print(f"   Mode: Interactive Tool Calling (MCP-like)")
    print("=" * 80)
    
    try:
        result = run_scraping_agent(
            url=test_url,
            platform_name=platform,
            task_description="Extract product information including name, price, rating, and reviews. Validate selectors before saving to database."
        )
        
        print("\n" + "=" * 80)
        print("📊 Final Results Summary:")
        print("=" * 80)
        print(f"   Success: {result.get('success', False)}")
        print(f"   Tool Calls Made: {result.get('final_results', {}).get('tool_calls_made', 0) if result.get('final_results') else 0}")
        print(f"   Iterations: {result.get('final_results', {}).get('iterations', 0) if result.get('final_results') else 0}")
        print(f"   Completed Steps: {len(result.get('completed_steps', []))}")
        print(f"   Completed Steps: {result.get('completed_steps', [])}")
        
        if result.get('errors'):
            print(f"\n⚠️ Errors Encountered ({len(result.get('errors', []))}):")
            for error in result['errors'][:5]:  # Show first 5 errors
                print(f"   - {error}")
        
        if result.get('final_results'):
            print(f"\n📦 Additional Results:")
            final = result['final_results']
            print(f"   URL: {final.get('url', 'N/A')}")
            print(f"   Platform: {final.get('platform', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ Error running agent: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
