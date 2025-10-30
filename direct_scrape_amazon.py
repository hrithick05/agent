#!/usr/bin/env python3
"""
Direct Amazon AirPods Pro 2 Scraper
This script directly uses the existing modules to scrape AirPods Pro 2 products from Amazon India
"""

import asyncio
import json
import os
from datetime import datetime

# Import our existing modules
from summaryModulle.fetchHTML import fetch_html
from summaryModulle.main import analyze_html
from SelectorToDB.generic_scraper import GenericPlatformScraper

async def scrape_amazon_airpods_direct():
    """Direct scraping function using existing modules"""
    
    try:
        print("🚀 Starting Amazon AirPods Pro 2 scraping...")
        
        # Step 1: Fetch HTML content
        print("\n📥 Fetching HTML content...")
        url = "https://www.amazon.in/s?k=airpods+pro2"
        html_content = await fetch_html(url)
        print(f"✅ HTML content fetched ({len(html_content)} characters)")
        
        # Step 2: Analyze HTML structure
        print("\n📊 Analyzing HTML structure...")
        summary = analyze_html(html_content)
        print(f"✅ HTML analysis completed")
        
        # Print some key insights
        print(f"- Total nodes: {summary.get('total_nodes', 0)}")
        print(f"- Top tags: {summary.get('top_tags', [])[:5]}")
        print(f"- Repeated patterns: {len(summary.get('repeats', {}).get('top_repeated', []))}")
        
        # Step 3: Configure selectors based on analysis
        print("\n⚙️ Configuring selectors...")
        
        # Get field hints from analysis
        field_hints = summary.get('field_hint_map', {})
        print(f"Field hints available: {list(field_hints.keys())}")
        
        # Create selector configuration
        selector_config = {
            'product_container': {
                'type': 'css',
                'selectors': [
                    'div[data-component-type="s-search-result"]',
                    'div.s-result-item',
                    'div[data-asin]',
                    '.s-result-item'
                ]
            },
            'name': {
                'type': 'css',
                'selectors': [
                    'h2 a span',
                    'h2 span',
                    '.s-size-mini span',
                    'a span[aria-label]',
                    'h2 a span[aria-label]'
                ]
            },
            'current_price': {
                'type': 'css',
                'selectors': [
                    '.a-price-whole',
                    '.a-offscreen',
                    '.a-price .a-offscreen',
                    '.a-price-range',
                    '.a-price .a-price-whole'
                ]
            },
            'original_price': {
                'type': 'css',
                'selectors': [
                    '.a-price.a-text-price .a-offscreen',
                    '.a-text-strike',
                    '.a-price.a-text-price'
                ]
            },
            'rating': {
                'type': 'css',
                'selectors': [
                    '.a-icon-alt',
                    '.a-icon-star',
                    '[aria-label*="stars"]',
                    '.a-icon-star-small'
                ]
            },
            'reviews': {
                'type': 'css',
                'selectors': [
                    '.a-size-base',
                    'a[href*="reviews"] span',
                    '.a-link-normal span',
                    '.a-size-small'
                ]
            },
            'discount': {
                'type': 'css',
                'selectors': [
                    '.a-badge-text',
                    '.a-color-base',
                    '.a-color-price',
                    '.a-text-bold'
                ]
            },
            'offers': {
                'type': 'css',
                'selectors': [
                    '.a-color-base',
                    '.a-text-bold',
                    '.a-badge-text',
                    '.a-color-secondary'
                ]
            }
        }
        
        print("✅ Selectors configured")
        
        # Step 4: Create scraper instance
        print("\n🔧 Creating scraper instance...")
        scraper = GenericPlatformScraper(html_content, selector_config, "Amazon India", url)
        print("✅ Scraper created")
        
        # Step 5: Extract products
        print("\n📦 Extracting products...")
        products = scraper.scrape()
        print(f"✅ Extracted {len(products)} products")
        
        # Step 6: Display sample products
        print("\n📋 Sample products:")
        for i, product in enumerate(products[:5]):
            print(f"\nProduct {i+1}:")
            print(f"  Name: {product.get('name', 'N/A')}")
            print(f"  Price: {product.get('current_price', 'N/A')}")
            print(f"  Rating: {product.get('rating', 'N/A')}")
            print(f"  Reviews: {product.get('reviews', 'N/A')}")
        
        # Step 7: Save to CSV
        print("\n💾 Saving to CSV...")
        csv_file = scraper.save_to_csv("amazon_airpods_products.csv")
        print(f"✅ Products saved to: {csv_file}")
        
        # Step 8: Save to JSON
        print("\n💾 Saving to JSON...")
        json_file = scraper.save_to_json("amazon_airpods_products.json")
        print(f"✅ Products saved to: {json_file}")
        
        # Step 9: Save analysis summary
        print("\n💾 Saving analysis summary...")
        with open("amazon_airpods_analysis.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print("✅ Analysis saved to: amazon_airpods_analysis.json")
        
        # Step 10: Try to save to Supabase if credentials are available
        print("\n💾 Attempting to save to Supabase...")
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if supabase_url and supabase_key:
            try:
                db_result = scraper.save_to_supabase(supabase_url, supabase_key, "scraped_products")
                if db_result.get('success'):
                    print(f"✅ Successfully saved {db_result['saved_count']} products to Supabase")
                else:
                    print(f"❌ Failed to save to Supabase: {db_result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Error saving to Supabase: {e}")
        else:
            print("⚠️ Supabase credentials not found. Set SUPABASE_URL and SUPABASE_KEY environment variables to save to database.")
        
        # Step 11: Print summary
        print("\n📊 Scraping Summary:")
        print(scraper.get_summary())
        
        print("\n🎉 Scraping completed successfully!")
        
        return {
            'products': products,
            'product_count': len(products),
            'csv_file': csv_file,
            'json_file': json_file,
            'analysis_file': 'amazon_airpods_analysis.json'
        }
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run the scraping process
    result = asyncio.run(scrape_amazon_airpods_direct())
    
    if result:
        print(f"\n📊 Final Results:")
        print(f"- Products extracted: {result['product_count']}")
        print(f"- CSV file: {result['csv_file']}")
        print(f"- JSON file: {result['json_file']}")
        print(f"- Analysis file: {result['analysis_file']}")
    else:
        print("❌ Scraping failed")
