import sys
import os
# Add current directory and parent directory to path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.extend([current_dir, parent_dir])
from langgraph_agent import run_scraping_agent, run_agent


def demo_comprehensive_agent():
    """Demo the complete LangGraph scraping agent workflow."""
    print("[ROCKET] Running Comprehensive LangGraph Scraping Agent Demo")
    print("=" * 80)

    # Example URLs for different platforms
    test_urls = [
        {
            "url": "https://www.flipkart.com/search?q=phone+case",
            "platform": "flipkart_phone_cases"
        },
        {
            "url": "https://www.amazon.in/s?k=laptop",
            "platform": "amazon_laptops"
        }
    ]

    for i, test_case in enumerate(test_urls, 1):
        print(f"\n[SEARCH] Test Case {i}: {test_case['platform']}")
        print(f"URL: {test_case['url']}")
        print("-" * 60)

        try:
            # Run the complete scraping agent workflow
            result = run_scraping_agent(
                url=test_case['url'],
                platform_name=test_case['platform']
            )

            # Display results
            print(f"\n[CHART] Results for {test_case['platform']}:")
            print(f"[SUCCESS] Success: {result.get('success', False)}")
            print(f"[LIST] Completed Steps: {len(result.get('completed_steps', []))}")
            print(f"[ERROR] Errors: {len(result.get('errors', []))}")

            if result.get('final_results'):
                final = result['final_results']
                print(f"[GLOBE] URL: {final.get('url', 'N/A')}")
                print(f"[STORE] Platform: {final.get('platform', 'N/A')}")
                print(f"[PACKAGE] Products Found: {final.get('products_found', 0)}")
                print(f"[FILE] Export File: {final.get('export_file', 'N/A')}")

            if result.get('errors'):
                print(f"\n[WARNING] Errors encountered:")
                for error in result['errors']:
                    print(f"   - {error}")

        except Exception as e:
            print(f"[FAIL] Test case {i} failed: {str(e)}")

        print("\n" + "=" * 80)


def demo_single_tools():
    """Demo individual tool usage."""
    print("\n[TOOL] Single Tool Demo")
    print("=" * 40)

    # Test individual tools
    tools_to_test = [
        ("get_available_fields", {}),
        ("get_html", {"url": "https://www.example.com"}),
    ]

    for tool_name, args in tools_to_test:
        print(f"\n[WRENCH] Testing: {tool_name}")
        try:
            result = run_agent(tool_name, args)
            print(f"[SUCCESS] Result: {result}")
        except Exception as e:
            print(f"[FAIL] Error: {str(e)}")


def main():
    """Main demo function."""
    print("[TARGET] LangGraph Web Scraping Agent Demo")
    print("=" * 80)
    print("This demo shows two approaches:")
    print("1. Comprehensive multi-step agent workflow")
    print("2. Individual tool usage")
    print("=" * 80)

    # Run comprehensive agent demo
    demo_comprehensive_agent()

    # Run single tools demo
    demo_single_tools()

    print("\n[PARTY] Demo Complete!")
    print("=" * 80)
    print("The LangGraph agent provides:")
    print("[SUCCESS] Multi-step workflow with state management")
    print("[SUCCESS] Error handling and recovery")
    print("[SUCCESS] Comprehensive analysis and reporting")
    print("[SUCCESS] Flexible tool integration")
    print("[SUCCESS] Easy to extend and customize")


if __name__ == "__main__":
    main()