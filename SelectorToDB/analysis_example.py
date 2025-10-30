#!/usr/bin/env python3
"""
Example: How to use Data Analysis Functions
Demonstrates how to analyze scraped data using the data_analysis.py utilities.
"""

from SelectorToDB.generic_scraper import GenericPlatformScraper
from SelectorToDB.config_converter import get_flipkart_advanced_config
from summaryModulle.fetchHTML import fetch_html_sync
from SelectorToDB.data_analysis import (
    get_selector_performance, validate_price_selectors, validate_rating_selectors, 
    validate_review_selectors, validate_name_selectors, get_selector_validation_report,
    get_selector_improvement_suggestions, get_comprehensive_selector_analysis,
    export_selector_analysis_to_json, print_selector_validation_summary
)

def analyze_flipkart_data():
    """Example: Analyze Flipkart phone cases data"""
    print("🔍 Analyzing Flipkart Phone Cases Data")
    print("=" * 60)
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync("https://www.flipkart.com/search?q=phone+case")
    
    # Step 2: Create scraper and scrape data
    print("🛒 Scraping products...")
    scraper = GenericPlatformScraper(
        html_content=html_content,
        selector_config=get_flipkart_advanced_config(),
        site_name="flipkart",
        url="https://www.flipkart.com/search?q=phone+case"
    )
    
    products = scraper.scrape()
    
    if not products:
        print("❌ No products found to analyze")
        return
    
    print(f"✅ Found {len(products)} products to analyze")
    
    # Step 3: Perform selector validation analysis
    print("\n📊 PERFORMING SELECTOR VALIDATION ANALYSIS...")
    
    # Overall selector performance
    print("\n1️⃣ Selector Performance:")
    performance = get_selector_performance(scraper)
    print(f"   Total Products: {performance.get('total_products', 0)}")
    print(f"   Site: {performance.get('site', 'Unknown')}")
    print(f"   Overall Success Rate: {performance.get('overall_success_rate', 'N/A')}")
    
    # Price selector validation
    print("\n2️⃣ Price Selector Validation:")
    price_validation = validate_price_selectors(scraper)
    current_price = price_validation.get('current_price_selector', {})
    print(f"   Current Price Success: {current_price.get('success_rate', 'N/A')} ({current_price.get('status', 'N/A')})")
    print(f"   Recommendation: {current_price.get('recommendation', 'N/A')}")
    
    # Rating selector validation
    print("\n3️⃣ Rating Selector Validation:")
    rating_validation = validate_rating_selectors(scraper)
    rating = rating_validation.get('rating_selector', {})
    print(f"   Rating Success: {rating.get('success_rate', 'N/A')} ({rating.get('status', 'N/A')})")
    print(f"   Recommendation: {rating.get('recommendation', 'N/A')}")
    
    # Name selector validation
    print("\n4️⃣ Name Selector Validation:")
    name_validation = validate_name_selectors(scraper)
    name = name_validation.get('name_selector', {})
    print(f"   Name Success: {name.get('success_rate', 'N/A')} ({name.get('status', 'N/A')})")
    print(f"   Recommendation: {name.get('recommendation', 'N/A')}")
    
    # Review selector validation
    print("\n5️⃣ Review Selector Validation:")
    review_validation = validate_review_selectors(scraper)
    review = review_validation.get('review_selector', {})
    print(f"   Review Success: {review.get('success_rate', 'N/A')} ({review.get('status', 'N/A')})")
    print(f"   Recommendation: {review.get('recommendation', 'N/A')}")
    
    # Improvement suggestions
    print("\n6️⃣ Improvement Suggestions:")
    suggestions = get_selector_improvement_suggestions(scraper)
    if suggestions.get('high_priority'):
        print("   High Priority Issues:")
        for issue in suggestions['high_priority']:
            print(f"     🚨 {issue['field']}: {issue['suggestion']}")
    
    # Export comprehensive analysis
    print("\n7️⃣ Exporting Analysis:")
    json_file = export_selector_analysis_to_json(scraper, "flipkart_selector_analysis.json")
    print(f"   Analysis exported to: {json_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print_selector_validation_summary(scraper)

def analyze_amazon_data():
    """Example: Analyze Amazon fridges data"""
    print("\n🔍 Analyzing Amazon Fridges Data")
    print("=" * 60)
    
    # Amazon selectors
    amazon_selectors = {
        'product_container': {
            'type': 'css',
            'selectors': ['div[data-component-type="s-search-result"]']
        },
        'name': {
            'type': 'css',
            'selectors': ['h2.a-size-medium span', 'h2.a-size-medium', 'span.a-size-medium']
        },
        'current_price': {
            'type': 'css',
            'selectors': ['span.a-price-whole', '.a-price .a-price-whole', 'span.a-price[data-a-size="xl"]']
        },
        'original_price': {
            'type': 'css',
            'selectors': ['span.a-price.a-text-price', 'span.a-text-price']
        },
        'rating': {
            'type': 'css',
            'selectors': ['span.a-size-small.a-color-base', '.a-icon-alt']
        },
        'reviews': {
            'type': 'css',
            'selectors': ['span.a-size-mini', 'a[href*="customerReviews"] span']
        },
        'discount': {
            'type': 'css',
            'selectors': ['span:contains("% off")', 'span:contains("off")']
        },
        'offers': {
            'type': 'css',
            'selectors': ['span.s-coupon-unclipped', 'span.a-color-base:contains("coupon")', 'span:contains("back with")']
        }
    }
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync("https://www.amazon.in/s?k=fridge+double+door+fridge+5+star")
    
    # Step 2: Create scraper and scrape data
    print("🛒 Scraping products...")
    scraper = GenericPlatformScraper(
        html_content=html_content,
        selector_config=amazon_selectors,
        site_name="amazon",
        url="https://www.amazon.in/s?k=fridge+double+door+fridge+5+star"
    )
    
    products = scraper.scrape()
    
    if not products:
        print("❌ No products found to analyze")
        return
    
    print(f"✅ Found {len(products)} products to analyze")
    
    # Step 3: Get comprehensive selector analysis
    print("\n📊 Getting Comprehensive Selector Analysis...")
    comprehensive_analysis = get_comprehensive_selector_analysis(scraper)
    
    # Print key insights
    print(f"\n📈 SELECTOR VALIDATION INSIGHTS:")
    health = comprehensive_analysis['validation_report']['overall_selector_health']
    print(f"   Overall Health Score: {health['score']} ({health['status']})")
    print(f"   Total Products: {health['total_products']}")
    
    # Show field performance
    print(f"\n🎯 FIELD PERFORMANCE:")
    for field, data in comprehensive_analysis['selector_performance']['field_performance'].items():
        status_emoji = "✅" if data['status'] == "GOOD" else "⚠️" if data['status'] == "NEEDS_IMPROVEMENT" else "❌"
        print(f"   {status_emoji} {field.upper()}: {data['success_rate']}")
    
    # Show critical issues
    if comprehensive_analysis['validation_report']['critical_issues']:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in comprehensive_analysis['validation_report']['critical_issues']:
            print(f"   ❌ {issue}")
    
    # Export analysis
    json_file = export_selector_analysis_to_json(scraper, "amazon_selector_analysis.json")
    print(f"\n📄 Analysis exported to: {json_file}")

def main():
    """Run analysis examples"""
    print("🚀 Data Analysis Examples")
    print("=" * 80)
    
    try:
        # Analyze Flipkart data
        analyze_flipkart_data()
        
        # Analyze Amazon data
        analyze_amazon_data()
        
        print("\n✅ All analysis examples completed!")
        print("\n📁 Check the generated JSON files for detailed analysis results.")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")

if __name__ == "__main__":
    main()
