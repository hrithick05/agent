#!/usr/bin/env python3
"""
Amazon AirPods Pro 2 Scraper using MCP Tools
This script uses the MCP server to scrape AirPods Pro 2 products from Amazon India
"""

import asyncio
import json
import os
from fastmcp import Client

async def scrape_amazon_airpods():
    """Main scraping function using MCP tools"""
    
    # Connect to MCP server
    client = Client("stdio")
    
    try:
        async with client:
            print("🚀 Starting Amazon AirPods Pro 2 scraping...")
            
            # Step 1: Fetch HTML content
            print("\n📥 Fetching HTML content...")
            result = await client.call_tool("get_html", {"url": "https://www.amazon.in/s?k=airpods+pro2"})
            print(f"✅ {result['message']}")
            
            # Step 2: Get available fields for selectors
            print("\n🔍 Getting available selector fields...")
            fields = await client.call_tool("get_available_fields", {})
            print(f"Available fields: {fields['available_fields']}")
            
            # Step 3: Read analysis summary to understand HTML structure
            print("\n📊 Analyzing HTML structure...")
            summary_fields = await client.call_tool("readsummary", {"field": None})
            print(f"Available summary fields: {summary_fields['data']}")
            
            # Get field hints for selectors
            field_hints = await client.call_tool("readsummary", {"field": "field_hint_map"})
            print(f"Field hints: {field_hints['data']}")
            
            # Get repeated patterns to identify product containers
            repeats = await client.call_tool("readsummary", {"field": "repeats"})
            print(f"Top repeated patterns: {repeats['data']['top_repeated'][:5]}")
            
            # Step 4: Configure selectors based on analysis
            print("\n⚙️ Configuring selectors...")
            
            # Product container selector (based on repeated patterns)
            await client.call_tool("set_selector", {
                "field": "product_container",
                "selector_type": "css",
                "selectors": ["div[data-component-type='s-search-result']", "div.s-result-item"]
            })
            
            # Product name selectors
            await client.call_tool("set_selector", {
                "field": "name",
                "selector_type": "css", 
                "selectors": ["h2 a span", "h2 span", ".s-size-mini span", "a span[aria-label]"]
            })
            
            # Current price selectors
            await client.call_tool("set_selector", {
                "field": "current_price",
                "selector_type": "css",
                "selectors": [".a-price-whole", ".a-offscreen", ".a-price .a-offscreen", ".a-price-range"]
            })
            
            # Original price selectors
            await client.call_tool("set_selector", {
                "field": "original_price", 
                "selector_type": "css",
                "selectors": [".a-price.a-text-price .a-offscreen", ".a-text-strike"]
            })
            
            # Rating selectors
            await client.call_tool("set_selector", {
                "field": "rating",
                "selector_type": "css",
                "selectors": [".a-icon-alt", ".a-icon-star", "[aria-label*='stars']"]
            })
            
            # Reviews selectors
            await client.call_tool("set_selector", {
                "field": "reviews",
                "selector_type": "css", 
                "selectors": [".a-size-base", "a[href*='reviews'] span", ".a-link-normal span"]
            })
            
            # Discount selectors
            await client.call_tool("set_selector", {
                "field": "discount",
                "selector_type": "css",
                "selectors": [".a-badge-text", ".a-color-base", ".a-color-price"]
            })
            
            # Offers selectors
            await client.call_tool("set_selector", {
                "field": "offers",
                "selector_type": "css",
                "selectors": [".a-color-base", ".a-text-bold", ".a-badge-text"]
            })
            
            print("✅ Selectors configured successfully")
            
            # Step 5: Create scraper instance
            print("\n🔧 Creating scraper instance...")
            scraper_result = await client.call_tool("create_scraper", {"platform_name": "Amazon India"})
            print(f"✅ {scraper_result['message']}")
            
            # Step 6: Extract products
            print("\n📦 Extracting products...")
            products_result = await client.call_tool("extract_products", {})
            print(f"✅ Extracted {products_result['product_count']} products")
            
            # Step 7: Analyze selector performance
            print("\n📈 Analyzing selector performance...")
            performance = await client.call_tool("get_selector_performance", {})
            print(f"Performance data: {performance['data']}")
            
            # Step 8: Validate specific selectors
            print("\n🔍 Validating selectors...")
            
            # Validate name selectors
            name_validation = await client.call_tool("validate_name_selectors", {})
            print(f"Name validation: {name_validation['data']}")
            
            # Validate price selectors
            price_validation = await client.call_tool("validate_price_selectors", {})
            print(f"Price validation: {price_validation['data']}")
            
            # Validate rating selectors
            rating_validation = await client.call_tool("validate_rating_selectors", {})
            print(f"Rating validation: {rating_validation['data']}")
            
            # Validate review selectors
            review_validation = await client.call_tool("validate_review_selectors", {})
            print(f"Review validation: {review_validation['data']}")
            
            # Step 9: Get comprehensive analysis
            print("\n📊 Getting comprehensive analysis...")
            comprehensive_analysis = await client.call_tool("get_comprehensive_selector_analysis", {})
            print(f"Comprehensive analysis: {comprehensive_analysis['data']}")
            
            # Step 10: Export analysis to JSON
            print("\n💾 Exporting analysis...")
            export_result = await client.call_tool("export_selector_analysis_to_json", {"filename": "amazon_airpods_analysis.json"})
            print(f"Analysis exported to: {export_result['file_path']}")
            
            # Step 11: Save to database (if Supabase credentials are available)
            print("\n💾 Saving to database...")
            db_result = await client.call_tool("save_to_database", {})
            print(f"Database save result: {db_result}")
            
            # Step 12: Get current state
            print("\n📋 Getting current state...")
            state = await client.call_tool("get_current_state", {})
            print(f"Current state: {state}")
            
            print("\n🎉 Scraping completed successfully!")
            
            return products_result
            
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        return None

if __name__ == "__main__":
    # Run the scraping process
    result = asyncio.run(scrape_amazon_airpods())
    
    if result:
        print(f"\n📊 Final Results:")
        print(f"- Products extracted: {result['product_count']}")
        print(f"- Status: {result['status']}")
        
        # Save products to local JSON file as backup
        with open("amazon_airpods_products.json", "w", encoding="utf-8") as f:
            json.dump(result['products'], f, indent=2, ensure_ascii=False)
        print(f"- Products saved to: amazon_airpods_products.json")
    else:
        print("❌ Scraping failed")
