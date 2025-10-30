"""
Complete workflow runner for LangGraph scraping agent
Follows the standard workflow: Fetch -> Analyze -> Configure -> Extract -> Validate -> Save
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from AgentModule.langgraph_agent import run_scraping_agent

def main():
    print("=" * 80)
    print("LANGGRAPH SCRAPING AGENT - COMPLETE WORKFLOW")
    print("=" * 80)
    print("\nWorkflow Steps:")
    print("1. Fetch HTML (get_html)")
    print("2. Analyze Structure (readsummary, readHTML)")
    print("3. Configure Selectors (get_available_fields, set_selector)")
    print("4. Create Scraper (create_scraper)")
    print("5. Extract Products (extract_products)")
    print("6. Inspect Data (inspect_extracted_data)")
    print("7. Validate Selectors (validate_*_selectors)")
    print("8. Save to Database (save_to_database)")
    print("=" * 80)
    
    # Configuration
    url = "https://www.flipkart.com/search?q=phone+case"
    platform = "flipkart"
    
    print(f"\nConfiguration:")
    print(f"  URL: {url}")
    print(f"  Platform: {platform}")
    print(f"  Max Iterations: 15")
    print("\nStarting agent...\n")
    
    try:
        result = run_scraping_agent(
            url=url,
            platform_name=platform,
            task_description="""Complete the full scraping workflow:
1. Fetch and analyze HTML structure
2. Understand the page layout using readsummary and readHTML
3. Design and configure selectors for all product fields (name, price, rating, reviews, etc.)
4. Create the scraper with configured selectors
5. Extract product data
6. Inspect extracted data quality
7. Validate selector performance
8. If quality is good, save to database
9. Provide final summary""",
            max_iterations=15
        )
        
        # Display results
        print("\n" + "=" * 80)
        print("WORKFLOW EXECUTION RESULTS")
        print("=" * 80)
        print(f"Success: {result.get('success', False)}")
        print(f"Total Iterations: {result.get('iterations', 0)}")
        print(f"Tool Calls Made: {result.get('tool_calls_made', 0)}")
        print(f"\nCompleted Steps ({len(result.get('completed_steps', []))}):")
        
        steps = result.get('completed_steps', [])
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
        
        if result.get('final_results'):
            print("\nFinal Results:")
            final = result['final_results']
            for key, value in final.items():
                print(f"  {key}: {value}")
        
        if result.get('errors'):
            print(f"\nErrors ({len(result['errors'])}):")
            for error in result['errors'][:5]:
                print(f"  - {error}")
        
        # Check workflow completion
        required_steps = [
            'get_html',
            'set_selector',
            'create_scraper',
            'extract_products'
        ]
        
        completed_required = [step for step in required_steps if any(step in s for s in steps)]
        print(f"\nRequired Steps Completed: {len(completed_required)}/{len(required_steps)}")
        if len(completed_required) == len(required_steps):
            print("✓ Workflow completed successfully!")
        else:
            missing = [s for s in required_steps if s not in completed_required]
            print(f"Missing steps: {missing}")
        
        print("\n" + "=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Agent execution was interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Failed to run agent: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

