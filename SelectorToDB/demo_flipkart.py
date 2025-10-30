#!/usr/bin/env python3
"""
Demo: Flipkart Scraping with Generic Scraper
Demonstrates how to use the generic scraper with Flipkart phone cases.
"""

from generic_scraper import GenericPlatformScraper, scrape_platform
from config_converter import get_flipkart_advanced_config
from summaryModulle.fetchHTML import fetch_html_sync

def demo_flipkart_phone_cases():
    """Demo: Scrape Flipkart phone cases using advanced configuration"""
    print("🛒 Flipkart Phone Cases Demo")
    print("=" * 50)
    
    # Use the advanced Flipkart configuration based on out.json analysis
    selector_config = get_flipkart_advanced_config()
    
    print("📋 Configuration:")
    print(f"  Product containers: {selector_config['product_container']['selectors']}")
    print(f"  Name selectors: {selector_config['name']['selectors']}")
    print(f"  Price selectors: {selector_config['current_price']['selectors']}")
    print()
    
    # Method 1: Using the class directly
    print("🔧 Method 1: Direct Class Usage")
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync("https://www.flipkart.com/search?q=phone+case")
    
    # Step 2: Create scraper with HTML content
    scraper = GenericPlatformScraper(
        html_content=html_content,
        selector_config=selector_config,
        site_name="flipkart_demo",
        url="https://www.flipkart.com/search?q=phone+case"
    )
    
    try:
        products = scraper.scrape()
        
        if products:
            csv_file = scraper.save_to_csv("demo_flipkart_phone_cases.csv")
            json_file = scraper.save_to_json("demo_flipkart_phone_cases.json")
            
            print(f"✅ Successfully scraped {len(products)} products")
            print(f"📄 CSV saved: {csv_file}")
            print(f"📄 JSON saved: {json_file}")
            
            # Show first few products
            print(f"\n📦 First 3 Products:")
            for i, product in enumerate(products[:3]):
                print(f"  {i+1}. {product.get('name', 'N/A')[:50]}...")
                print(f"     Price: {product.get('current_price', 'N/A')}")
                print(f"     Rating: {product.get('rating', 'N/A')}")
                print()
            
            print(scraper.get_summary())
        else:
            print("❌ No products found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def demo_flipkart_airpods():
    """Demo: Scrape Flipkart airpods using convenience function"""
    print("🎧 Flipkart AirPods Demo")
    print("=" * 50)
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync("https://www.flipkart.com/search?q=airpods")
    
    # Step 2: Use convenience function
    try:
        csv_file = scrape_platform(
            html_content=html_content,
            selector_config=get_flipkart_advanced_config(),
            site_name="flipkart_airpods"
        )
        print(f"✅ Convenience function completed")
        print(f"📄 CSV saved: {csv_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def demo_custom_configuration():
    """Demo: Custom configuration for a different search"""
    print("🔧 Custom Configuration Demo")
    print("=" * 50)
    
    # Custom configuration for phone cases with different search
    custom_config = {
        'product_container': {
            'type': 'css',
            'selectors': ['div[class*="_4WELSP"]', 'div[data-id]']
        },
        'name': {
            'type': 'css',
            'selectors': ['a[class*="wjcEIp"]', 'img[alt]'],
            'attribute': 'title'
        },
        'current_price': {
            'type': 'css',
            'selectors': ['div[class*="Nx9bqj"]'],
            'regex': r'₹([\d,]+)'
        },
        'rating': {
            'type': 'css',
            'selectors': ['div[class*="XQDdHH"]'],
            'regex': r'(\d+\.?\d*)'
        }
    }
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync("https://www.flipkart.com/search?q=mobile+case")
    
    # Step 2: Create scraper with HTML content
    scraper = GenericPlatformScraper(
        html_content=html_content,
        selector_config=custom_config,
        site_name="flipkart_mobile_cases",
        url="https://www.flipkart.com/search?q=mobile+case"
    )
    
    try:
        products = scraper.scrape()
        
        if products:
            csv_file = scraper.save_to_csv("demo_mobile_cases.csv")
            print(f"✅ Custom config scraped {len(products)} products")
            print(f"📄 CSV saved: {csv_file}")
        else:
            print("❌ No products found with custom config")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def main():
    """Run all demos"""
    print("🚀 Generic Scraper Demo - Flipkart Examples")
    print("=" * 80)
    print()
    
    try:
        # Run demos
        demo_flipkart_phone_cases()
        demo_flipkart_airpods()
        demo_custom_configuration()
        
        print("✅ All demos completed!")
        print("\n📁 Check the generated CSV files for results.")
        print("📖 See README_generic_scraper.md for full documentation.")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")

if __name__ == "__main__":
    main()
