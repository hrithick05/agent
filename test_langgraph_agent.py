"""Test script to run the LangGraph agent"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from AgentModule.langgraph_agent import run_scraping_agent

def main():
    print("=" * 80)
    print("Starting LangGraph Scraping Agent Test")
    print("=" * 80)
    
    try:
        print("\n[TEST] Calling run_scraping_agent...")
        result = run_scraping_agent(
            url="https://www.flipkart.com/search?q=phone+case",
            platform_name="flipkart",
            task_description="Extract product information including name, price, rating, and reviews.",
            max_iterations=2  # Very small number for quick testing
        )
        print("\n[TEST] Agent returned!")
        
        print("\n" + "=" * 80)
        print("✅ Agent Execution Complete!")
        print("=" * 80)
        print(f"Success: {result.get('success', False)}")
        print(f"Iterations: {result.get('iterations', 0)}")
        print(f"Tool Calls Made: {result.get('tool_calls_made', 0)}")
        print(f"Completed Steps: {result.get('completed_steps', [])}")
        
        if result.get('errors'):
            print(f"\n⚠️ Errors ({len(result['errors'])}):")
            for error in result['errors'][:3]:
                print(f"  - {error}")
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

