from SelectorToDB.generic_scraper import GenericPlatformScraper, create_selector_config, convert_main_config, scrape_platform
from summaryModulle.fetchHTML import fetch_html_sync


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

def example_amazon_scraping():
    """Example: Scraping Amazon fridges"""
    print("🛒 Example: Scraping Amazon Fridges")
    print("=" * 50)
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync("https://www.amazon.in/s?k=fridge+double+door+fridge+5+star")
    
    # Step 2: Create scraper with HTML content
    scraper = GenericPlatformScraper(
        html_content=html_content,
        selector_config=amazon_selectors,
        site_name="amazon",
        url="https://www.amazon.in/s?k=fridge+double+door+fridge+5+star"
    )
    
    # Step 3: Scrape products
    products = scraper.scrape()
    csv_file = scraper.save_to_csv("amazon_fridges.csv")
    
    print(scraper.get_summary())
    print(f"📄 CSV saved: {csv_file}")
    print()

def main():
    example_amazon_scraping()

if __name__ == "__main__":
    main()