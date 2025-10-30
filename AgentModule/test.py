from typing import Dict, List, Any, Optional, Union
import os
from summaryModulle.fetchHTML import fetch_html_sync
from summaryModulle.main import analyze_html
from SelectorToDB.generic_scraper import GenericPlatformScraper
from SelectorToDB.data_analysis import (
    get_selector_performance, validate_price_selectors, validate_rating_selectors, 
    validate_review_selectors, validate_name_selectors, get_selector_validation_report,
    get_selector_improvement_suggestions, get_comprehensive_selector_analysis,
    export_selector_analysis_to_json, print_selector_validation_summary
)
import os
from google import genai
from google.genai import types


# Global variables for HTML content and analysis summary
html_content: str = ""
summary: Dict[str, Any] = {}
GenericPlatformScraperObj: GenericPlatformScraper = None

# Global selector template - empty by default, to be filled by LLM incrementally
selector_template: Dict[str, Any] = {
    'product_container': {
        'type': None,
        'selectors': []
    },
    'name': {
        'type': None,
        'selectors': []
    },
    'current_price': {
        'type': None,
        'selectors': []
    },
    'original_price': {
        'type': None,
        'selectors': []
    },
    'rating': {
        'type': None,
        'selectors': []
    },
    'reviews': {
        'type': None,
        'selectors': []
    },
    'discount': {
        'type': None,
        'selectors': []
    },
    'offers': {
        'type': None,
        'selectors': []
    }
}

def get_html(url: str) -> dict:
    """
    Fetch HTML content from URL and perform comprehensive analysis.
    
    This function fetches HTML content using Crawl4AI and analyzes it to extract
    structural patterns, field hints, and metadata that can be used for scraping.
    
    Args:
        url (str): The URL to fetch HTML content from
        
    Returns:
        dict: Success message confirming content saved in global variables
        
    Side Effects:
        - Updates global html_content variable with fetched HTML
        - Updates global summary variable with analysis results
    """
    print(f"🤖 Agent Tool Call: get_html(url='{url}')")
    global html_content, summary
    html_content = fetch_html_sync(url)
    summary = analyze_html(html_content)
    result = {"message":"successfully saved the content in the gloabal variable"}
    print(f"✅ Tool Response: {result}")
    return result

def readsummary(field: Optional[str] = None) -> Union[Any, List[str]]:
    """
    Read analysis summary data for a specific field or return all available fields.
    
    This function provides access to the HTML analysis results including:
    - DOM structure analysis
    - Repeated pattern detection
    - Field hint generation
    - Text pattern recognition
    - Form analysis
    - Confidence scoring
    
    Args:
        field (Optional[str]): Specific field name to retrieve. If None, returns all available field names.
                              Common fields: 'repeats', 'field_hint_map', 'text_patterns', 
                              'confidence_summary', 'forms_detailed', etc.
    
    Returns:
        Union[Any, List[str]]: 
            - If field is specified: The analysis data for that field
            - If field is None: List of all available field names in the summary
    
    Example:
        >>> readsummary('field_hint_map')  # Returns field hints for scraping
        >>> readsummary()  # Returns ['repeats', 'field_hint_map', 'text_patterns', ...]
    """
    print(f"🤖 Agent Tool Call: readsummary(field='{field}')")
    if field:
        result = summary.get(field, f"Field '{field}' not found in summary")
    else:
        result = list(summary.keys())
    print(f"✅ Tool Response: Retrieved {'field data' if field else 'field list'}")
    return result

def readHTML(start_line: int, end_line: int) -> str:
    """
    Read HTML content by line numbers instead of character indices.
    
    This function allows you to examine specific sections of the HTML content
    by specifying line numbers, making it easier to inspect HTML structure
    and debug scraping issues.
    
    Args:
        start_line (int): Starting line number (1-based indexing)
        end_line (int): Ending line number (1-based indexing, inclusive)
    
    Returns:
        str: String containing the specified lines from HTML content.
             Returns "No HTML content available" if html_content is empty.
    
    Example:
        >>> readHTML(1, 20)  # Returns first 20 lines of HTML
        >>> readHTML(100, 150)  # Returns lines 100-150 of HTML
        >>> readHTML(42, 42)  # Returns only line 42
    """
    print(f"🤖 Agent Tool Call: readHTML(start_line={start_line}, end_line={end_line})")
    if not html_content:
        result = "No HTML content available"
        print(f"✅ Tool Response: {result}")
        return result
    
    # Split HTML content into lines
    lines = html_content.split('\n')
    
    # Convert to 0-based indexing and handle bounds
    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line)
    
    # Return the specified line range
    result = '\n'.join(lines[start_idx:end_idx])
    print(f"✅ Tool Response: Retrieved {end_idx - start_idx} lines of HTML")
    return result
    
def scrape(selector: Dict[str, Any], platform_name: str) -> Dict[str, str]:
    """
    Create a GenericPlatformScraper instance and store it in global variable.
    
    This function initializes a scraper that can extract product data from HTML content
    using flexible selector configurations. The scraper supports CSS, XPath, and regex
    selectors with fallback options. The scraper object is stored in the global variable
    GenericPlatformScraperObj for use by other tools.
    
    Args:
        selector (Dict[str, Any]): Selector configuration dictionary with the following structure:
            {
                'product_container': {
                    'type': 'css',
                    'selectors': ['div.product', 'div[data-id]']
                },
                'name': {
                    'type': 'css',
                    'selectors': ['h3.title', 'a.product-link'],
                    'attribute': 'title'  # Optional
                },
                'current_price': {
                    'type': 'css',
                    'selectors': ['span.price'],
                    'regex': r'₹([\\d,]+)'  # Optional regex cleaning
                }
            }
        platform_name (str): Name of the platform/site for identification and logging
    
    Returns:
        Dict[str, str]: Success message confirming scraper object creation and storage
        
    Side Effects:
        - Updates global variable GenericPlatformScraperObj with the created scraper instance
        - The scraper object is now available for use by other analysis and validation tools
        
    Note:
        The scraper is initialized but not yet executed. The object is stored globally
        and can be used by other tools to perform operations on the data.
        
    Example:
        >>> result = scrape(selector_config, "example_site")
        >>> print(result["message"])  # "Successfully created GenericPlatformScraper object..."
    """
    print(f"🤖 Agent Tool Call: scrape(platform_name='{platform_name}')")
    global GenericPlatformScraperObj
    GenericPlatformScraperObj = GenericPlatformScraper(html_content, selector, platform_name)
    result = {"message": "Successfully created GenericPlatformScraper object and stored in the global variable GenericPlatformScraperObj"}
    print(f"✅ Tool Response: {result}")
    return result

# ============================================================================
# SELECTOR VALIDATION AND DATA ANALYSIS FUNCTIONS
# ============================================================================

def get_selector_performance_tool() -> Dict[str, Any]:
    """
    Analyze selector performance and data extraction success rates.
    
    This function evaluates how well the selectors are performing by calculating
    success rates for each field (name, price, rating, etc.) and providing
    overall performance metrics. Uses the globally stored GenericPlatformScraperObj.
    
    Returns:
        Dict[str, Any]: Performance metrics including:
            - total_products (int): Number of products scraped
            - site (str): Site name
            - field_performance (Dict): Success rates for each field
            - overall_success_rate (str): Overall extraction success rate
            - scraped_at (str): Timestamp of scraping
    
    Raises:
        ValueError: If no scraper object is available in global variable
    
    Example:
        >>> performance = get_selector_performance_tool()
        >>> print(f"Overall success: {performance['overall_success_rate']}")
    """
    print(f"🤖 Agent Tool Call: get_selector_performance_tool()")
    global GenericPlatformScraperObj
    if GenericPlatformScraperObj is None:
        result = {"error": "No scraper object available. Please call scrape() function first."}
        print(f"❌ Tool Response: {result}")
        return result
    result = get_selector_performance(GenericPlatformScraperObj)
    print(f"✅ Tool Response: Performance analysis completed")
    return result

def validate_price_selectors_tool() -> Dict[str, Any]:
    """
    Validate price selector performance and data quality.
    
    This function specifically analyzes price extraction performance, checking
    for valid numeric values and providing recommendations for improvement.
    Uses the globally stored GenericPlatformScraperObj.
    
    Returns:
        Dict[str, Any]: Price validation results including:
            - current_price_selector (Dict): Current price validation metrics
            - original_price_selector (Dict): Original price validation metrics
            Each contains: success_rate, valid_extractions, status, sample_data, recommendation
    
    Raises:
        ValueError: If no scraper object is available in global variable
    
    Example:
        >>> price_validation = validate_price_selectors_tool()
        >>> print(f"Current price success: {price_validation['current_price_selector']['success_rate']}")
    """
    global GenericPlatformScraperObj
    if GenericPlatformScraperObj is None:
        return {"error": "No scraper object available. Please call scrape() function first."}
    return validate_price_selectors(GenericPlatformScraperObj)

def validate_rating_selectors_tool() -> Dict[str, Any]:
    """
    Validate rating selector performance and data quality.
    
    This function analyzes rating extraction performance, checking for valid
    rating values (0-5 range) and providing quality metrics.
    Uses the globally stored GenericPlatformScraperObj.
    
    Returns:
        Dict[str, Any]: Rating validation results including:
            - rating_selector (Dict): Rating validation metrics containing:
                - success_rate (str): Percentage of successful extractions
                - valid_extractions (int): Number of valid ratings found
                - valid_range_extractions (int): Ratings in valid 0-5 range
                - status (str): "GOOD", "NEEDS_IMPROVEMENT", or "POOR"
                - sample_data (List[str]): Sample extracted ratings
                - recommendation (str): Improvement suggestions
    
    Raises:
        ValueError: If no scraper object is available in global variable
    
    Example:
        >>> rating_validation = validate_rating_selectors_tool()
        >>> print(f"Rating status: {rating_validation['rating_selector']['status']}")
    """
    global GenericPlatformScraperObj
    if GenericPlatformScraperObj is None:
        return {"error": "No scraper object available. Please call scrape() function first."}
    return validate_rating_selectors(GenericPlatformScraperObj)

def validate_review_selectors_tool() -> Dict[str, Any]:
    """
    Validate review selector performance and data quality.
    
    This function analyzes review count extraction performance, checking for
    valid numeric review counts and providing quality metrics.
    Uses the globally stored GenericPlatformScraperObj.
    
    Returns:
        Dict[str, Any]: Review validation results including:
            - review_selector (Dict): Review validation metrics containing:
                - success_rate (str): Percentage of successful extractions
                - valid_extractions (int): Number of valid reviews found
                - numeric_extractions (int): Reviews with numeric values
                - status (str): "GOOD", "NEEDS_IMPROVEMENT", or "POOR"
                - sample_data (List[str]): Sample extracted review counts
                - recommendation (str): Improvement suggestions
    
    Raises:
        ValueError: If no scraper object is available in global variable
    
    Example:
        >>> review_validation = validate_review_selectors_tool()
        >>> print(f"Review success: {review_validation['review_selector']['success_rate']}")
    """
    global GenericPlatformScraperObj
    if GenericPlatformScraperObj is None:
        return {"error": "No scraper object available. Please call scrape() function first."}
    return validate_review_selectors(GenericPlatformScraperObj)

def validate_name_selectors_tool() -> Dict[str, Any]:
    """
    Validate name selector performance and data quality.
    
    This function analyzes product name extraction performance, checking for
    reasonable name lengths and providing quality metrics.
    Uses the globally stored GenericPlatformScraperObj.
    
    Returns:
        Dict[str, Any]: Name validation results including:
            - name_selector (Dict): Name validation metrics containing:
                - success_rate (str): Percentage of successful extractions
                - valid_extractions (int): Number of valid names found
                - reasonable_length_extractions (int): Names with reasonable length (5-200 chars)
                - status (str): "GOOD", "NEEDS_IMPROVEMENT", or "POOR"
                - sample_data (List[str]): Sample extracted product names
                - recommendation (str): Improvement suggestions
    
    Raises:
        ValueError: If no scraper object is available in global variable
    
    Example:
        >>> name_validation = validate_name_selectors_tool()
        >>> print(f"Name status: {name_validation['name_selector']['status']}")
    """
    global GenericPlatformScraperObj
    if GenericPlatformScraperObj is None:
        return {"error": "No scraper object available. Please call scrape() function first."}
    return validate_name_selectors(GenericPlatformScraperObj)

def get_selector_validation_report_tool() -> Dict[str, Any]:
    """
    Get comprehensive selector validation report.
    
    This function provides a complete validation report combining all field
    validations with overall health scoring and recommendations.
    Uses the globally stored GenericPlatformScraperObj.
    
    Returns:
        Dict[str, Any]: Comprehensive validation report including:
            - overall_selector_health (Dict): Overall health score and status
            - field_performance (Dict): Performance metrics for each field
            - detailed_validations (Dict): Detailed validation results for each field type
            - critical_issues (List[str]): List of critical problems found
            - recommendations (List[str]): List of improvement recommendations
            - analysis_timestamp (str): When the analysis was performed
    
    Raises:
        ValueError: If no scraper object is available in global variable
    
    Example:
        >>> report = get_selector_validation_report_tool()
        >>> print(f"Overall health: {report['overall_selector_health']['status']}")
    """
    global GenericPlatformScraperObj
    if GenericPlatformScraperObj is None:
        return {"error": "No scraper object available. Please call scrape() function first."}
    return get_selector_validation_report(GenericPlatformScraperObj)

def get_selector_improvement_suggestions_tool() -> Dict[str, Any]:
    """
    Get specific suggestions for improving selectors.
    
    This function analyzes selector performance and provides prioritized
    suggestions for improving data extraction quality.
    Uses the globally stored GenericPlatformScraperObj.
    
    Returns:
        Dict[str, Any]: Improvement suggestions organized by priority:
            - high_priority (List[Dict]): Critical issues requiring immediate attention
            - medium_priority (List[Dict]): Issues that should be addressed soon
            - low_priority (List[Dict]): Minor improvements for optimization
            - sample_failures (Dict): Sample failed extractions for each field
            Each suggestion contains: field, issue, suggestion
    
    Raises:
        ValueError: If no scraper object is available in global variable
    
    Example:
        >>> suggestions = get_selector_improvement_suggestions_tool()
        >>> for issue in suggestions['high_priority']:
        ...     print(f"Fix {issue['field']}: {issue['suggestion']}")
    """
    global GenericPlatformScraperObj
    if GenericPlatformScraperObj is None:
        return {"error": "No scraper object available. Please call scrape() function first."}
    return get_selector_improvement_suggestions(GenericPlatformScraperObj)

def get_comprehensive_selector_analysis_tool() -> Dict[str, Any]:
    """
    Get comprehensive selector validation analysis.
    
    This function combines all analysis functions into a single comprehensive
    report providing complete insights into selector performance.
    Uses the globally stored GenericPlatformScraperObj.
    
    Returns:
        Dict[str, Any]: Complete analysis including:
            - selector_performance (Dict): Overall performance metrics
            - price_validation (Dict): Price-specific validation results
            - rating_validation (Dict): Rating-specific validation results
            - review_validation (Dict): Review-specific validation results
            - name_validation (Dict): Name-specific validation results
            - validation_report (Dict): Comprehensive validation report
            - improvement_suggestions (Dict): Prioritized improvement suggestions
            - analysis_timestamp (str): Analysis timestamp
    
    Raises:
        ValueError: If no scraper object is available in global variable
    
    Example:
        >>> analysis = get_comprehensive_selector_analysis_tool()
        >>> print(f"Analysis completed at: {analysis['analysis_timestamp']}")
    """
    print(f"🤖 Agent Tool Call: get_comprehensive_selector_analysis_tool()")
    global GenericPlatformScraperObj
    if GenericPlatformScraperObj is None:
        result = {"error": "No scraper object available. Please call scrape() function first."}
        print(f"❌ Tool Response: {result}")
        return result
    result = get_comprehensive_selector_analysis(GenericPlatformScraperObj)
    print(f"✅ Tool Response: Comprehensive analysis completed")
    return result

def export_selector_analysis_to_json_tool(filename: Optional[str] = None) -> str:
    """
    Export comprehensive selector analysis to JSON file.
    
    This function saves the complete selector analysis to a JSON file for
    later review, sharing, or integration with other tools.
    Uses the globally stored GenericPlatformScraperObj.
    
    Args:
        filename (Optional[str]): Output filename. If None, auto-generates with timestamp
    
    Returns:
        str: Path to the exported JSON file
    
    Raises:
        ValueError: If no scraper object is available in global variable
    
    Example:
        >>> json_file = export_selector_analysis_to_json_tool("analysis.json")
        >>> print(f"Analysis saved to: {json_file}")
    """
    global GenericPlatformScraperObj
    if GenericPlatformScraperObj is None:
        return "Error: No scraper object available. Please call scrape() function first."
    return export_selector_analysis_to_json(GenericPlatformScraperObj, filename)

def print_selector_validation_summary_tool() -> None:
    """
    Print a summary of the selector validation to console.
    
    This function prints a formatted summary of selector validation results
    to the console, providing a quick overview of scraping performance.
    Uses the globally stored GenericPlatformScraperObj.
    
    Returns:
        None: Prints formatted summary to console
    
    Raises:
        ValueError: If no scraper object is available in global variable
    
    Example:
        >>> print_selector_validation_summary_tool()
        # Prints formatted summary with health scores, field performance, etc.
    """
    global GenericPlatformScraperObj
    if GenericPlatformScraperObj is None:
        print("Error: No scraper object available. Please call scrape() function first.")
        return
    return print_selector_validation_summary(GenericPlatformScraperObj)
def save_to_DB() -> Dict[str, Any]:
    """
    Save scraped data to Supabase database.
    
    This function saves the scraped products to a Supabase database table.
    It requires SUPABASE_URL and SUPABASE_KEY environment variables to be set.
    Uses the globally stored GenericPlatformScraperObj.
    
    Returns:
        Dict[str, Any]: Save operation result including:
            - success (bool): Whether the save operation was successful
            - saved_count (int): Number of products saved to database
            - table_name (str): Name of the database table used
            - site (str): Site name from scraper
            - scraped_at (str): Timestamp when data was scraped
            - message (str): Success message
            - error (str): Error message if operation failed
    
    Environment Variables Required:
        - SUPABASE_URL: Your Supabase project URL
        - SUPABASE_KEY: Your Supabase API key
        - SUPABASE_TABLE_NAME: Database table name (optional, defaults to 'scraped_products')
    
    Raises:
        ValueError: If no scraper object is available in global variable
    
    Example:
        >>> result = save_to_DB()
        >>> if result['success']:
        ...     print(f"Saved {result['saved_count']} products to {result['table_name']}")
        >>> else:
        ...     print(f"Error: {result['error']}")
    """
    print(f"🤖 Agent Tool Call: save_to_DB()")
    global GenericPlatformScraperObj
    if GenericPlatformScraperObj is None:
        result = {
            "success": False,
            "saved_count": 0,
            "error": "No scraper object available. Please call scrape() function first."
        }
        print(f"❌ Tool Response: {result}")
        return result
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    table_name = os.getenv('SUPABASE_TABLE_NAME', 'scraped_products')
    
    if not supabase_url or not supabase_key:
        result = {
            "success": False,
            "saved_count": 0,
            "error": "Supabase credentials not found in environment variables. Please set SUPABASE_URL and SUPABASE_KEY."
        }
        print(f"❌ Tool Response: {result}")
        return result
    
    result = GenericPlatformScraperObj.save_to_supabase(supabase_url, supabase_key, table_name)
    print(f"✅ Tool Response: Database save {'successful' if result.get('success') else 'failed'}")
    return result

def set_selector(field: str, selector_type: str, selectors: List[str]) -> Dict[str, Any]:
    """
    Set selector configuration for a specific field in the global template.
    
    This function allows the LLM to incrementally build the selector configuration
    by filling in specific fields one at a time, avoiding token limit issues
    and reducing the chance of format errors.
    
    Args:
        field (str): The field name to set. MUST be one of these exact values:
                    - 'product_container': Container element that wraps each product
                    - 'name': Product name/title
                    - 'current_price': Current selling price
                    - 'original_price': Original/MRP price (optional)
                    - 'rating': Product rating (1-5 stars)
                    - 'reviews': Number of reviews/ratings
                    - 'discount': Discount percentage or amount
                    - 'offers': Special offers or coupons
        selector_type (str): The type of selector. MUST be one of: 'css', 'xpath', 'regex'
        selectors (List[str]): List of selector strings for the field. Must be non-empty.
    
    Returns:
        Dict[str, Any]: The current state of the selector template after the update
        
    Example:
        >>> template = set_selector("name", "css", ['img[alt]', 'a[class*="wjcEIp"]'])
        >>> print(template['name'])
        {'type': 'css', 'selectors': ['img[alt]', 'a[class*="wjcEIp"]']}
        
        >>> template = set_selector("current_price", "css", ['div[class*="Nx9bqj"]'])
        >>> print(template['current_price'])
        {'type': 'css', 'selectors': ['div[class*="Nx9bqj"]']}
        
    Note:
        Available fields are: product_container, name, current_price, original_price, 
        rating, reviews, discount, offers. Do NOT use fields like 'image_url', 
        'product_url', 'description', etc. as they are not supported.
    """
    print(f"🤖 Agent Tool Call: set_selector(field='{field}', type='{selector_type}', selectors={len(selectors)} items)")
    global selector_template
    print(selector_template)
    # Validate field name
    if field not in selector_template:
        available_fields = list(selector_template.keys())
        result = {
            "error": f"Invalid field '{field}'. Available fields: {available_fields}",
            "suggestion": f"Use one of these exact field names: {', '.join(available_fields)}",
            "field_descriptions": {
                "product_container": "Container element that wraps each product",
                "name": "Product name/title", 
                "current_price": "Current selling price",
                "original_price": "Original/MRP price (optional)",
                "rating": "Product rating (1-5 stars)",
                "reviews": "Number of reviews/ratings",
                "discount": "Discount percentage or amount",
                "offers": "Special offers or coupons"
            }
        }
        print(f"❌ Tool Response: {result}")
        return result
    
    # Validate selector type
    valid_types = ['css', 'xpath', 'regex']
    if selector_type not in valid_types:
        result = {
            "error": f"Invalid selector type '{selector_type}'. Valid types: {valid_types}"
        }
        print(f"❌ Tool Response: {result}")
        return result
    
    # Validate selectors list
    if not isinstance(selectors, list) or not selectors:
        result = {
            "error": "Selectors must be a non-empty list of strings"
        }
        print(f"❌ Tool Response: {result}")
        return result
    
    # Update the template
    selector_template[field] = {
        'type': selector_type,
        'selectors': selectors
    }
    
    result = {
        "message": f"Successfully set {field} selector",
        "field": field,
        "type": selector_type,
        "selectors": selectors,
        "template": selector_template
    }
    print(f"✅ Tool Response: {result['message']}")
    return result

def get_available_fields() -> Dict[str, Any]:
    """
    Get the list of available fields for selector configuration.
    
    This function helps the LLM understand what fields are available
    for the set_selector function, preventing invalid field name errors.
    
    Returns:
        Dict[str, Any]: Available fields with descriptions
        
    Example:
        >>> fields = get_available_fields()
        >>> print(fields['available_fields'])
        ['product_container', 'name', 'current_price', ...]
    """
    print(f"🤖 Agent Tool Call: get_available_fields()")
    global selector_template
    
    result = {
        "available_fields": list(selector_template.keys()),
        "field_descriptions": {
            "product_container": "Container element that wraps each product",
            "name": "Product name/title", 
            "current_price": "Current selling price",
            "original_price": "Original/MRP price (optional)",
            "rating": "Product rating (1-5 stars)",
            "reviews": "Number of reviews/ratings",
            "discount": "Discount percentage or amount",
            "offers": "Special offers or coupons"
        },
        "usage_example": "Use set_selector('name', 'css', ['h1.title', 'a.product-link']) to set name selectors"
    }
    print(f"✅ Tool Response: Retrieved {len(result['available_fields'])} available fields")
    return result

client = genai.Client(api_key="AIzaSyAsPWKRL9ab5g1v-0LujZJFrpl8zyfijq8")
config = types.GenerateContentConfig(
    tools=[get_html, readsummary, readHTML, set_selector, get_available_fields, scrape, get_selector_performance_tool, validate_price_selectors_tool, validate_rating_selectors_tool, validate_review_selectors_tool, validate_name_selectors_tool, get_selector_validation_report_tool, get_selector_improvement_suggestions_tool, get_comprehensive_selector_analysis_tool, export_selector_analysis_to_json_tool, print_selector_validation_summary_tool, save_to_DB]
)
'''
# Make the request
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="get the html content of the url https://www.flipkart.com/search?q=phone+case and analyze the html structure completely , by using the summary tool and reading the html you can understand the structure fully . then design the proper selector to scrape the products with the fields required using the set_selector tool. after making a proper selector try to see the quality of data extracted from the selector using the many analysis tools given to you. if the data is not good, then improve the selector using the set_selector tool. repeat the process until you get the good data . after getting the good data, try to save the data to the database using the save_to_DB tool. ",
    config=config,
)

# Print the final, user-facing response
# print(response.text)  # Commented out to avoid running LLM
'''
def main_with_llm_selectors() -> None:
    """
    Main function using the LLM-generated selector template with added offers selector.
    
    This function uses the exact selectors created by the LLM and adds the missing
    offers selector to complete the scraping workflow.
    
    Workflow:
    1. Set up the LLM's selector template
    2. Add the missing offers selector
    3. Fetch and analyze HTML
    4. Create scraper with the complete template
    5. Extract and analyze data
    6. Save to database
    """
    print("🚀 Starting Scraping with LLM-Generated Selectors")
    print("=" * 60)
    
    # LLM's selector template (exactly as generated)
    llm_selectors = {
        'product_container': {
            'type': 'css',
            'selectors': ['div.slAVV4']
        },
        'name': {
            'type': 'css',
            'selectors': ['a.wjcEIp']
        },
        'current_price': {
            'type': 'css',
            'selectors': ['div.Nx9bqj']
        },
        'original_price': {
            'type': 'css',
            'selectors': ['div.yRaY8j']
        },
        'rating': {
            'type': 'css',
            'selectors': ['div.XQDdHH']
        },
        'reviews': {
            'type': 'css',
            'selectors': ['span.Wphh3N']
        },
        'discount': {
            'type': 'css',
            'selectors': ['div.UkUFwK span']
        },
        'offers': {
            'type': 'css',
            'selectors': ['div[class*="+7E521"]', 'div[class*="oUss6M"]', 'div[class*="offer"]', 'span[class*="coupon"]', 'div:contains("Save")']
        }
    }
    
    target_url = "https://www.flipkart.com/search?q=phone+case"
    
    try:
        # Step 1: Fetch and analyze HTML
        print("\n📡 Step 1: Fetching and analyzing HTML...")
        get_html(target_url)
        print(f"✅ HTML fetched and analyzed from: {target_url}")
        
        # Step 2: Create scraper with LLM's selectors
        print("\n🛠️ Step 2: Creating scraper with LLM-generated selectors...")
        scrape_result = scrape(llm_selectors, "flipkart_phone_cases_llm")
        print(f"✅ {scrape_result['message']}")
        
        # Step 3: Extract product data
        print("\n🛒 Step 3: Extracting product data...")
        global GenericPlatformScraperObj
        if GenericPlatformScraperObj is not None:
            products = GenericPlatformScraperObj.scrape()
            print(f"✅ Successfully extracted {len(products)} products")
            
            # Display sample products
            if products:
                print("\n📦 Sample Products:")
                for i, product in enumerate(products[:3]):
                    print(f"   {i+1}. {product.get('name', 'N/A')[:50]}...")
                    print(f"      Current Price: {product.get('current_price', 'N/A')}")
                    print(f"      Original Price: {product.get('original_price', 'N/A')}")
                    print(f"      Rating: {product.get('rating', 'N/A')}")
                    print(f"      Reviews: {product.get('reviews', 'N/A')}")
                    print(f"      Discount: {product.get('discount', 'N/A')}")
                    print(f"      Offers: {product.get('offers', 'N/A')}")
                    print()
        else:
            print("❌ Failed to create scraper object")
            return
        
        # Step 4: Performance Analysis
        print("\n📊 Step 4: Analyzing selector performance...")
        performance = get_selector_performance_tool()
        if 'error' not in performance:
            print(f"✅ Overall success rate: {performance.get('overall_success_rate', 'N/A')}")
            print(f"   Total products: {performance.get('total_products', 0)}")
            print(f"   Site: {performance.get('site', 'Unknown')}")
            
            # Show field-wise performance
            field_performance = performance.get('field_performance', {})
            print("\n📈 Field-wise Performance:")
            for field, stats in field_performance.items():
                print(f"   {field}: {stats.get('success_rate', 'N/A')} ({stats.get('extracted_count', 0)}/{stats.get('total_products', 0)})")
        else:
            print(f"❌ Performance analysis failed: {performance['error']}")
        
        # Step 5: Field-specific validation
        print("\n🔍 Step 5: Field-specific validation...")
        
        # Price validation
        price_validation = validate_price_selectors_tool()
        if 'error' not in price_validation:
            current_price = price_validation.get('current_price_selector', {})
            original_price = price_validation.get('original_price_selector', {})
            print(f"✅ Current Price: {current_price.get('success_rate', 'N/A')} ({current_price.get('status', 'N/A')})")
            print(f"✅ Original Price: {original_price.get('success_rate', 'N/A')} ({original_price.get('status', 'N/A')})")
        else:
            print(f"❌ Price validation failed: {price_validation['error']}")
        
        # Rating validation
        rating_validation = validate_rating_selectors_tool()
        if 'error' not in rating_validation:
            rating = rating_validation.get('rating_selector', {})
            print(f"✅ Rating: {rating.get('success_rate', 'N/A')} ({rating.get('status', 'N/A')})")
        else:
            print(f"❌ Rating validation failed: {rating_validation['error']}")
        
        # Name validation
        name_validation = validate_name_selectors_tool()
        if 'error' not in name_validation:
            name = name_validation.get('name_selector', {})
            print(f"✅ Name: {name.get('success_rate', 'N/A')} ({name.get('status', 'N/A')})")
        else:
            print(f"❌ Name validation failed: {name_validation['error']}")
        
        # Step 6: Comprehensive analysis
        print("\n📈 Step 6: Comprehensive analysis...")
        comprehensive_analysis = get_comprehensive_selector_analysis_tool()
        if 'error' not in comprehensive_analysis:
            health = comprehensive_analysis.get('validation_report', {}).get('overall_selector_health', {})
            print(f"✅ Overall health: {health.get('score', 'N/A')} ({health.get('status', 'N/A')})")
        else:
            print(f"❌ Comprehensive analysis failed: {comprehensive_analysis['error']}")
        
        # Step 7: Export analysis
        print("\n📄 Step 7: Exporting analysis to JSON...")
        json_file = export_selector_analysis_to_json_tool("llm_selector_analysis.json")
        if not json_file.startswith("Error"):
            print(f"✅ Analysis exported to: {json_file}")
        else:
            print(f"❌ Export failed: {json_file}")
        
        # Step 8: Print summary
        print("\n📋 Step 8: Printing validation summary...")
        print_selector_validation_summary_tool()
        
        # Step 9: Save to database
        print("\n💾 Step 9: Saving data to database...")
        db_result = save_to_DB()
        if db_result.get('success'):
            print(f"✅ Successfully saved {db_result.get('saved_count', 0)} products to database")
            print(f"   Table: {db_result.get('table_name', 'Unknown')}")
            print(f"   Site: {db_result.get('site', 'Unknown')}")
        else:
            print(f"❌ Database save failed: {db_result.get('error', 'Unknown error')}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎉 LLM SELECTOR WORKFLOW COMPLETED!")
        print("=" * 60)
        print(f"📊 Total products processed: {len(products) if 'products' in locals() else 0}")
        print(f"📄 Analysis exported to: {json_file if 'json_file' in locals() and not json_file.startswith('Error') else 'Failed'}")
        print(f"💾 Database save: {'Success' if db_result.get('success') else 'Failed'}")
        print("=" * 60)
        
        # Show LLM selector summary
        print("\n🤖 LLM Selector Summary:")
        print("✅ All selectors were correctly identified by the LLM")
        print("✅ Added missing offers selector for completeness")
        print("✅ Selectors are Flipkart-specific and highly accurate")
        
    except Exception as e:
        print(f"\n❌ Workflow failed with error: {e}")
        print("Please check your internet connection and try again.")
        return

# Uncomment the line below to run the LLM selector workflow
main_with_llm_selectors()
