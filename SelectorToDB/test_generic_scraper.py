#!/usr/bin/env python3
"""
Test Script for Generic Platform Scraper
Tests the scraper with different platforms and configurations.
"""

import json
from generic_scraper import GenericPlatformScraper, scrape_platform
from config_converter import convert_all_configs, get_flipkart_advanced_config
from summaryModulle.fetchHTML import fetch_html_sync

def test_flipkart_advanced():
    """Test Flipkart with advanced configuration from out.json analysis"""
    print("🧪 Test 1: Flipkart with Advanced Configuration")
    print("=" * 60)
    
    # Use the advanced Flipkart configuration
    selector_config = get_flipkart_advanced_config()
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync("https://www.flipkart.com/search?q=phone+case")
    
    # Step 2: Create scraper with HTML content
    scraper = GenericPlatformScraper(
        html_content=html_content,
        selector_config=selector_config,
        site_name="flipkart_advanced",
        url="https://www.flipkart.com/search?q=phone+case"
    )
    
    try:
        products = scraper.scrape()
        
        if products:
            csv_file = scraper.save_to_csv("test_flipkart_advanced.csv")
            json_file = scraper.save_to_json("test_flipkart_advanced.json")
            
            print(f"✅ Successfully scraped {len(products)} products")
            print(f"📄 CSV: {csv_file}")
            print(f"📄 JSON: {json_file}")
            
            # Show sample product
            if products:
                sample = products[0]
                print(f"\n📦 Sample Product:")
                print(f"   Name: {sample.get('name', 'N/A')}")
                print(f"   Price: {sample.get('current_price', 'N/A')}")
                print(f"   Rating: {sample.get('rating', 'N/A')}")
        else:
            print("❌ No products found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def test_amazon_converted():
    """Test Amazon using converted main.py configuration"""
    print("🧪 Test 2: Amazon with Converted Configuration")
    print("=" * 60)
    
    # Convert main.py configs
    configs = convert_all_configs()
    amazon_config = configs.get('amazon')
    
    if not amazon_config:
        print("❌ Amazon configuration not found")
        return
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync("https://www.amazon.in/s?k=fridge+double+door+fridge+5+star")
    
    # Step 2: Create scraper with HTML content
    scraper = GenericPlatformScraper(
        html_content=html_content,
        selector_config=amazon_config,
        site_name="amazon_converted",
        url="https://www.amazon.in/s?k=fridge+double+door+fridge+5+star"
    )
    
    try:
        products = scraper.scrape()
        
        if products:
            csv_file = scraper.save_to_csv("test_amazon_converted.csv")
            print(f"✅ Successfully scraped {len(products)} products")
            print(f"📄 CSV: {csv_file}")
            
            # Show sample product
            if products:
                sample = products[0]
                print(f"\n📦 Sample Product:")
                print(f"   Name: {sample.get('name', 'N/A')}")
                print(f"   Price: {sample.get('current_price', 'N/A')}")
                print(f"   Rating: {sample.get('rating', 'N/A')}")
        else:
            print("❌ No products found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def test_convenience_function():
    """Test the convenience function"""
    print("🧪 Test 3: Convenience Function")
    print("=" * 60)
    
    # Simple configuration
    simple_config = {
        'product_container': {
            'type': 'css',
            'selectors': ['div[class*="_4WELSP"]', 'div[data-id]']
        },
        'name': {
            'type': 'css',
            'selectors': ['a[class*="wjcEIp"]', 'img[alt]']
        },
        'current_price': {
            'type': 'css',
            'selectors': ['div[class*="Nx9bqj"]']
        }
    }
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync("https://www.flipkart.com/search?q=airpods")
    
    # Step 2: Use convenience function
    try:
        csv_file = scrape_platform(
            html_content=html_content,
            selector_config=simple_config,
            site_name="flipkart_simple"
        )
        print(f"✅ Convenience function completed")
        print(f"📄 CSV: {csv_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def test_configuration_validation():
    """Test configuration validation and conversion"""
    print("🧪 Test 4: Configuration Validation")
    print("=" * 60)
    
    # Test configuration conversion
    configs = convert_all_configs()
    
    print("📋 Available converted configurations:")
    for site_name, config in configs.items():
        print(f"  ✅ {site_name}: {len(config)} fields")
        
        # Show some selectors
        if 'name' in config:
            name_selectors = config['name'].get('selectors', [])
            print(f"     Name selectors: {name_selectors[:2]}...")
    
    print(f"\n📊 Total configurations: {len(configs)}")
    
    # Test advanced Flipkart config
    advanced_config = get_flipkart_advanced_config()
    print(f"\n🔧 Advanced Flipkart config fields: {len(advanced_config)}")
    
    print()

def test_error_handling():
    """Test error handling with invalid configurations"""
    print("🧪 Test 5: Error Handling")
    print("=" * 60)
    
    # Test with minimal configuration
    minimal_config = {
        'product_container': {
            'type': 'css',
            'selectors': ['div.nonexistent']
        }
    }
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync("https://www.flipkart.com/search?q=phone+case")
    
    # Step 2: Create scraper with HTML content
    scraper = GenericPlatformScraper(
        html_content=html_content,
        selector_config=minimal_config,
        site_name="test_error",
        url="https://www.flipkart.com/search?q=phone+case"
    )
    
    try:
        products = scraper.scrape()
        print(f"📊 Products found with minimal config: {len(products)}")
        
        if products:
            print("✅ Some products found despite minimal config")
        else:
            print("⚠️ No products found (expected with minimal config)")
            
    except Exception as e:
        print(f"❌ Expected error: {e}")
    
    print()

def main():
    """Run all tests"""
    print("🚀 Generic Platform Scraper Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all tests
        test_flipkart_advanced()
        test_amazon_converted()
        test_convenience_function()
        test_configuration_validation()
        test_error_handling()
        
        print("✅ All tests completed!")
        print("\n📁 Check the generated CSV and JSON files for results.")
        
    except Exception as e:
        print(f"❌ Test suite error: {e}")

if __name__ == "__main__":
    main()
