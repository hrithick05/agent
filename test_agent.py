"""Test script to run the Gemini-powered LangGraph agent."""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from AgentModule.langgraph_agent import run_scraping_agent

def main():
    """Run the agent with a test URL."""
    print("🎯 Testing Gemini-Powered LangGraph Scraping Agent")
    print("=" * 80)
    
    # Test with a simple example
    test_url = "https://www.flipkart.com/search?q=phone+case"
    platform = "flipkart"
    
    print(f"📋 Test Configuration:")
    print(f"   URL: {test_url}")
    print(f"   Platform: {platform}")
    print(f"   Gemini will define the workflow dynamically")
    print("=" * 80)
    
    try:
        result = run_scraping_agent(
            url=test_url,
            platform_name=platform,
            task_description="Extract product information including name, price, and rating"
        )
        
        print("\n📊 Final Results:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Completed Steps: {result.get('completed_steps', [])}")
        
        if result.get('workflow_definition'):
            workflow = result['workflow_definition']
            print(f"\n🤖 Workflow Used: {workflow.get('workflow_name', 'Unknown')}")
            print(f"   Total Steps: {len(workflow.get('steps', []))}")
        
        if result.get('errors'):
            print(f"\n⚠️ Errors:")
            for error in result['errors']:
                print(f"   - {error}")
        
        if result.get('final_results'):
            print(f"\n📦 Final Results Summary:")
            final = result['final_results']
            print(f"   Products Found: {final.get('products_found', 0)}")
            print(f"   Export File: {final.get('export_file', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ Error running agent: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
