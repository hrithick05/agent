"""
Test script for the Autonomous Scraping Agent (Gemini 2.5 + LangGraph).
This demonstrates the complete end-to-end workflow automation.
"""
import sys
import os

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from AgentModule.langgraph_agent import run_autonomous_scraping_agent

def main():
    """Run the autonomous scraping agent with a test URL."""
    print("\n" + "="*80)
    print("🤖 AUTONOMOUS SCRAPING AGENT - DEMONSTRATION")
    print("="*80)
    
    # Test configuration
    test_url = "https://www.flipkart.com/search?q=phone+case"
    
    print(f"\n📎 Target URL: {test_url}")
    print(f"🎯 Mode: Autonomous End-to-End Workflow")
    print(f"🤖 AI: Gemini 2.5 + LangGraph")
    print("\n" + "="*80)
    print("The agent will autonomously:")
    print("  1. Fetch & analyze HTML")
    print("  2. Understand DOM structure")
    print("  3. Design platform selectors")
    print("  4. Extract product data")
    print("  5. Validate data quality")
    print("  6. Save to database (if quality passes)")
    print("="*80 + "\n")
    
    try:
        # Run the autonomous agent
        result = run_autonomous_scraping_agent(
            url=test_url,
            platform_name="flipkart",
            max_iterations=15,
            quality_threshold=0.7  # 70% quality threshold
        )
        
        # Display final results
        print("\n" + "="*80)
        print("📊 WORKFLOW EXECUTION SUMMARY")
        print("="*80)
        
        final_summary = result.get("final_summary", {})
        print(f"\n✅ HTML Fetched: {final_summary.get('html_fetched', False)}")
        print(f"✅ Selectors Configured: {final_summary.get('selectors_configured', False)}")
        print(f"✅ Data Extracted: {final_summary.get('data_extracted', False)}")
        print(f"✅ Validation Passed: {final_summary.get('validation_passed', False)}")
        print(f"✅ Data Saved: {final_summary.get('data_saved', False)}")
        print(f"\n📈 Products Extracted: {final_summary.get('products_extracted', 0)}")
        print(f"🔄 Total Iterations: {final_summary.get('total_iterations', 0)}")
        print(f"🔧 Tool Calls Made: {final_summary.get('tool_calls_made', 0)}")
        
        if final_summary.get('validation_scores'):
            print(f"\n📊 Validation Scores:")
            for metric, score in final_summary['validation_scores'].items():
                print(f"   {metric}: {score*100:.1f}%")
        
        if final_summary.get('tools_used'):
            print(f"\n🛠️  Tools Used:")
            for tool in final_summary['tools_used']:
                print(f"   - {tool}")
        
        if result.get('errors'):
            print(f"\n⚠️  Errors Encountered: {len(result['errors'])}")
            for error in result['errors'][:3]:
                print(f"   - {error}")
        
        print("\n" + "="*80)
        
        if final_summary.get('workflow_completed'):
            print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        else:
            print("⚠️  Workflow completed with warnings or incomplete steps")
        
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running autonomous agent: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

