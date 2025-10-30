from SelectorToDB.generic_scraper import GenericPlatformScraper, create_selector_config, convert_main_config, scrape_platform, scrape_and_save_to_supabase
from summaryModulle.fetchHTML import fetch_html_sync
from typing import Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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

def scraper(URL: str, selector_config: Dict, site_name: str):
    """Example: Scraping Amazon fridges"""
    print("🛒 Example: Scraping Amazon Fridges")
    print("=" * 50)
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync(URL)
    
    # Step 2: Create scraper with HTML content
    scraper = GenericPlatformScraper(
        html_content=html_content,
        selector_config=selector_config,
        site_name=site_name,
        url=URL
    )
    
    # Step 3: Scrape products
    products = scraper.scrape()
    print(f"Found {len(products)} products")
    
    # Step 4: Save to CSV
    csv_file = scraper.save_to_csv(f"{site_name}.csv")
    print(f"📄 CSV saved: {csv_file}")
    
    # Step 5: Save to Supabase
    print("\n🗄️ Saving to Supabase...")
    supabase_result = save_to_supabase(scraper)
    
    print(scraper.get_summary())
    print()

def save_to_supabase(scraper: GenericPlatformScraper):
    """Save scraped data to Supabase database"""
    # Get Supabase credentials from environment variables
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    TABLE_NAME = os.getenv('SUPABASE_TABLE_NAME', 'scraped_products')
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Supabase credentials not found in environment variables")
        print("Please check your .env file contains:")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_KEY=your_supabase_key")
        return {"error": "Missing Supabase credentials"}
    
    try:
        # Save to Supabase
        result = scraper.save_to_supabase(SUPABASE_URL, SUPABASE_KEY, TABLE_NAME)
        
        if result.get('success'):
            print(f"✅ Successfully saved {result['saved_count']} products to Supabase table '{result['table_name']}'")
            print(f"📊 Site: {result['site']}")
            print(f"⏰ Saved at: {result['scraped_at']}")
        else:
            print(f"❌ Failed to save to Supabase: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error saving to Supabase: {e}")
        return {"error": str(e)}


def main():
    # Method 1: Using the main scraper function (saves to both CSV and Supabase)
    scraper(URL="https://www.amazon.in/s?k=fridge+double+door+fridge+5+star", selector_config=amazon_selectors, site_name="amazon")
    
    print("\n" + "="*80 + "\n")
if __name__ == "__main__":
    main()