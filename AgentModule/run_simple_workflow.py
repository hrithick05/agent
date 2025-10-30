"""
Simple Scraping Workflow: Scrape -> Analyze -> Re-scrape if <80% OR Save to DB
This script demonstrates the complete workflow using available tools.
"""

import sys
import os

# Fix Windows console encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    # Set environment variable for subprocess encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
# Add current directory and parent directory to path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.extend([current_dir, parent_dir])

from app import (
    get_html,
    readsummary,
    readHTML,
    scrape,
    set_selector,
    get_available_fields,
    save_to_DB,
    get_selector_performance_tool,
    validate_price_selectors_tool,
    validate_rating_selectors_tool,
    validate_review_selectors_tool,
    validate_name_selectors_tool,
    get_selector_validation_report_tool,
    get_selector_improvement_suggestions_tool,
    get_comprehensive_selector_analysis_tool,
    export_selector_analysis_to_json_tool,
    print_selector_validation_summary_tool,
    html_content,  # Import the global HTML content
)
from bs4 import BeautifulSoup


def debug_html_structure(html_text):
    """Debug HTML to find actual selectors being used."""
    if not html_text:
        print("[DEBUG] No HTML content available")
        return
    
    soup = BeautifulSoup(html_text, 'html.parser')
    
    print("\n[DEBUG] Analyzing HTML Structure...")
    print("=" * 60)
    
    # Look for common product container patterns
    potential_containers = [
        ('div[data-id]', soup.select('div[data-id]')),
        ('div.cPHDOP', soup.select('div.cPHDOP')),
        ('div.slAVV4', soup.select('div.slAVV4')),
        ('div._75nlfW', soup.select('div._75nlfW')),
        ('div.tUxRFH', soup.select('div.tUxRFH')),
    ]
    
    print("\n[CONTAINERS] Product Container Candidates:")
    for selector, elements in potential_containers:
        if elements:
            print(f"  ✓ {selector}: Found {len(elements)} elements")
            # Show first element's structure
            if len(elements) > 0:
                first = elements[0]
                print(f"    Sample classes: {first.get('class', [])}")
                print(f"    Has data-id: {first.get('data-id', 'No')}")
        else:
            print(f"  ✗ {selector}: Not found")
    
    # If we found containers, analyze their children
    if potential_containers[0][1]:  # If div[data-id] exists
        first_container = potential_containers[0][1][0]
        print(f"\n[STRUCTURE] First Product Container Structure:")
        print(f"  Tags found: {[tag.name for tag in first_container.find_all()[:20]]}")
        
        # Look for price elements
        price_elements = first_container.select('div[class*="price"]') or first_container.select('span[class*="price"]')
        if price_elements:
            print(f"  Price elements: {len(price_elements)} found")
            for pe in price_elements[:3]:
                print(f"    Classes: {pe.get('class')}, Text: {pe.get_text(strip=True)[:30]}")
        
        # Look for name elements
        name_elements = first_container.select('a[title]') or first_container.select('div[class*="title"]')
        if name_elements:
            print(f"  Name elements: {len(name_elements)} found")
            for ne in name_elements[:2]:
                print(f"    Tag: {ne.name}, Classes: {ne.get('class')}, Title: {ne.get('title', '')[:50]}")
    
    print("=" * 60)


def extract_success_rate(performance_data):
    """Extract overall success rate from performance data."""
    if 'error' in performance_data:
        return 0.0
    
    overall_rate = performance_data.get('overall_success_rate', '0%')
    if isinstance(overall_rate, str):
        # Remove % sign and convert to float
        return float(overall_rate.replace('%', ''))
    return float(overall_rate)


def improve_selectors_based_on_suggestions(suggestions):
    """Improve selectors based on AI suggestions."""
    print("\n[IMPROVE] Applying selector improvements...")
    
    if 'error' in suggestions:
        print(f"[WARNING] No suggestions available: {suggestions.get('error')}")
        return False
    
    improvements = suggestions.get('improvements', [])
    if not improvements:
        print("[INFO] No specific improvements suggested")
        return False
    
    improved = False
    for improvement in improvements:
        field = improvement.get('field')
        new_selectors = improvement.get('suggested_selectors', [])
        selector_type = improvement.get('type', 'css')
        
        if field and new_selectors:
            print(f"[UPDATE] Improving {field} selectors: {new_selectors}")
            result = set_selector(field, selector_type, new_selectors)
            if 'error' not in result:
                improved = True
                print(f"[SUCCESS] Updated {field} selectors")
            else:
                print(f"[ERROR] Failed to update {field}: {result.get('error')}")
    
    return improved


def run_scraping_workflow(url, platform_name, max_iterations=3):
    """
    Main workflow: Scrape -> Analyze -> Re-scrape if <80% OR Save to DB
    
    Args:
        url: Target URL to scrape
        platform_name: Name of the platform
        max_iterations: Maximum number of re-scraping attempts
    """
    print("[ROCKET] Starting Simple Scraping Workflow")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Platform: {platform_name}")
    print(f"Quality Threshold: 80%")
    print("=" * 80)
    
    iteration = 0
    success_rate = 0.0
    
    # Updated selectors for Flipkart based on latest HTML structure
    # These are more generic and should work better
    initial_selectors = {
        'product_container': {
            'type': 'css',
            'selectors': [
                'div[data-id]',  # Primary: Product containers with data-id
                'div.cPHDOP',    # Alternative container class
                'div.slAVV4',    # Older class
                'div._75nlfW',   # Fallback
                'div[class*="product"]'  # Generic product container
            ]
        },
        'name': {
            'type': 'css',
            'selectors': [
                'div.KzDlHZ',    # Product title div
                'a.wjcEIp',      # Product link
                'a.WKTcLC',      # Alternative link class
                'div[class*="title"]',  # Generic title
                'a[title]'       # Any link with title attribute
            ]
        },
        'current_price': {
            'type': 'css',
            'selectors': [
                'div.Nx9bqj',    # Current price div
                'div._4b5DiR',   # Alternative price class
                'div._1vC4OE',   # Another alternative
                'div[class*="price"]',  # Generic price
                'span[class*="price"]'  # Price in span
            ]
        },
        'original_price': {
            'type': 'css',
            'selectors': [
                'div.yRaY8j',    # Original price
                'div._3auQ3N',   # MRP class
                'div._25b18c',   # Strike-through price
                'span[class*="strike"]'  # Generic strikethrough
            ]
        },
        'rating': {
            'type': 'css',
            'selectors': [
                'div.XQDdHH',    # Rating div
                'div._2_KrJI',   # Alternative rating
                'span[class*="rating"]',  # Generic rating
                'div[class*="stars"]'  # Star rating
            ]
        },
        'reviews': {
            'type': 'css',
            'selectors': [
                'span.Wphh3N',   # Review count
                'span._2_R_DZ',  # Alternative review count
                'span[class*="review"]',  # Generic reviews
                'span[class*="rating"]'   # Rating text with count
            ]
        },
        'discount': {
            'type': 'css',
            'selectors': [
                'div.UkUFwK',    # Discount badge
                'div._3Ay6Sb',   # Alternative discount
                'span[class*="discount"]',  # Generic discount
                'span[class*="off"]'  # "X% off" text
            ]
        },
        'offers': {
            'type': 'css',
            'selectors': [
                'div[class*="offer"]',
                'span[class*="coupon"]',
                'div[class*="bank"]',  # Bank offers
                'span[class*="save"]'  # Save offers
            ]
        }
    }
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'='*80}")
        print(f"[ITERATION {iteration}/{max_iterations}]")
        print(f"{'='*80}")
        
        try:
            # STEP 1: Fetch HTML
            print("\n[STEP 1] Fetching and analyzing HTML...")
            html_result = get_html(url)
            if 'error' in html_result:
                print(f"[ERROR] Failed to fetch HTML: {html_result['error']}")
                break
            print("[SUCCESS] HTML fetched successfully")
            
            # Debug HTML structure on first iteration
            if iteration == 1:
                from app import html_content as fetched_html
                debug_html_structure(fetched_html)
            
            # STEP 2: Read summary to understand structure
            print("\n[STEP 2] Reading HTML summary...")
            summary_result = readsummary()
            if isinstance(summary_result, dict) and 'available_fields' in summary_result:
                print(f"[INFO] Available fields: {summary_result['available_fields']}")
            
            # STEP 3: Configure selectors
            print("\n[STEP 3] Configuring selectors...")
            for field, config in initial_selectors.items():
                set_result = set_selector(
                    field, 
                    config['type'], 
                    config['selectors']
                )
                if 'error' not in set_result:
                    print(f"[SUCCESS] Configured {field}")
                else:
                    print(f"[WARNING] Could not configure {field}: {set_result.get('error')}")
            
            # STEP 4: Create scraper and extract data
            print("\n[STEP 4] Creating scraper and extracting data...")
            scrape_result = scrape(initial_selectors, platform_name)
            if 'error' in scrape_result:
                print(f"[ERROR] Scraping failed: {scrape_result['error']}")
                break
            
            products_count = scrape_result.get('products_count', 0)
            print(f"[SUCCESS] {scrape_result['message']}")
            
            if products_count == 0:
                print("[WARNING] No products extracted! Selectors may not match the HTML structure.")
                print("[INFO] This will result in 0% success rate.")
            
            # STEP 5: Analyze performance
            print("\n[STEP 5] Analyzing data quality...")
            performance = get_selector_performance_tool()
            success_rate = extract_success_rate(performance)
            
            print(f"\n[METRICS] Data Quality Report:")
            print(f"  Overall Success Rate: {success_rate}%")
            print(f"  Quality Threshold: 80%")
            print(f"  Status: {'PASS' if success_rate >= 80 else 'FAIL'}")
            
            # Display field-wise performance
            if 'field_performance' in performance:
                print(f"\n[DETAILS] Field-wise Performance:")
                for field, stats in performance['field_performance'].items():
                    rate = stats.get('success_rate', 'N/A')
                    print(f"  - {field}: {rate}")
            
            # STEP 6: Validate specific fields
            print("\n[STEP 6] Running field validations...")
            validations = {
                'price': validate_price_selectors_tool(),
                'rating': validate_rating_selectors_tool(),
                'review': validate_review_selectors_tool(),
                'name': validate_name_selectors_tool()
            }
            
            for field_type, result in validations.items():
                if 'error' not in result:
                    print(f"[SUCCESS] {field_type.capitalize()} validation passed")
                else:
                    print(f"[WARNING] {field_type.capitalize()} validation: {result.get('error')}")
            
            # DECISION POINT: Check if quality is >= 80%
            if success_rate >= 80.0:
                print(f"\n{'='*80}")
                print(f"[DECISION] Quality >= 80% - PROCEEDING TO SAVE")
                print(f"{'='*80}")
                
                # STEP 7: Save to database
                print("\n[STEP 7] Saving data to database...")
                db_result = save_to_DB()
                if 'error' not in db_result:
                    print(f"[SUCCESS] {db_result.get('message', 'Data saved successfully')}")
                else:
                    print(f"[ERROR] Database save failed: {db_result.get('error')}")
                
                # STEP 8: Generate comprehensive report
                print("\n[STEP 8] Generating final report...")
                comprehensive = get_comprehensive_selector_analysis_tool()
                export_result = export_selector_analysis_to_json_tool(f"{platform_name}_analysis.json")
                print_selector_validation_summary_tool()
                
                print(f"\n{'='*80}")
                print("[COMPLETE] Workflow finished successfully!")
                print(f"  Final Quality: {success_rate}%")
                print(f"  Iterations Used: {iteration}/{max_iterations}")
                print(f"  Report Saved: {export_result.get('file', 'N/A')}")
                print(f"{'='*80}")
                
                return True
            
            else:
                print(f"\n{'='*80}")
                print(f"[DECISION] Quality < 80% - ATTEMPTING TO IMPROVE")
                print(f"{'='*80}")
                
                if iteration < max_iterations:
                    # STEP 7: Get improvement suggestions
                    print("\n[STEP 7] Getting selector improvement suggestions...")
                    suggestions = get_selector_improvement_suggestions_tool()
                    
                    # STEP 8: Apply improvements
                    improved = improve_selectors_based_on_suggestions(suggestions)
                    
                    if improved:
                        print(f"[INFO] Selectors improved, retrying scrape (Iteration {iteration+1})...")
                        # Update initial_selectors with improved ones (they're already set in global state)
                        continue
                    else:
                        print("[WARNING] No improvements applied, using same selectors...")
                        # Try anyway with slight modifications
                        continue
                else:
                    print(f"\n[WARNING] Maximum iterations ({max_iterations}) reached")
                    print(f"[INFO] Final quality: {success_rate}%")
                    
                    # Save anyway with warning
                    print("\n[STEP 7] Saving data despite low quality...")
                    db_result = save_to_DB()
                    if 'error' not in db_result:
                        print(f"[SUCCESS] {db_result.get('message', 'Data saved with warnings')}")
                    
                    print(f"\n{'='*80}")
                    print("[COMPLETE] Workflow finished (quality below threshold)")
                    print(f"  Final Quality: {success_rate}%")
                    print(f"  Threshold: 80%")
                    print(f"{'='*80}")
                    
                    return False
        
        except Exception as e:
            print(f"\n[ERROR] Workflow error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return False


if __name__ == "__main__":
    # Example usage
    target_url = "https://www.flipkart.com/search?q=phone+case"
    platform = "flipkart_phone_cases"
    
    success = run_scraping_workflow(target_url, platform, max_iterations=3)
    
    if success:
        print("\n[FINAL] Scraping workflow completed successfully!")
    else:
        print("\n[FINAL] Scraping workflow completed with issues")

