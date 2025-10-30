#!/usr/bin/env python3
"""
Example Usage of Generic Platform Scraper
Demonstrates how to use the GenericPlatformScraper with different platforms.
"""

from generic_scraper import GenericPlatformScraper, create_selector_config, convert_main_config, scrape_platform
from summaryModulle.fetchHTML import fetch_html_sync

# Example 1: Flipkart configuration using the FIXED selectors from out.json analysis
flipkart_selectors = {
    'product_container': {
        'type': 'css',
        'selectors': ['div[data-id]', 'div[class*="slAVV4"]', 'div[class*="_4WELSP"]']  # Fixed: data-id first
    },
    'name': {
        'type': 'css',
        'selectors': ['img[alt]', 'a[class*="wjcEIp"]', 'a[title]', 'a[href*="/p/"]']  # Fixed: img alt first
    },
    'current_price': {
        'type': 'css',
        'selectors': ['div[class*="Nx9bqj"]', 'div[class*="hl05eU"] div[class*="Nx9bqj"]', 'div:contains("₹")', 'span:contains("₹")']  # Added fallbacks
    },
    'original_price': {
        'type': 'css',
        'selectors': ['div[class*="yRaY8j"]', 'div[class*="hl05eU"] div[class*="yRaY8j"]', 'span[class*="strike"]', 'del']  # Added fallbacks
    },
    'rating': {
        'type': 'css',
        'selectors': ['div[class*="XQDdHH"]', 'span[class*="Y1HWO0"] div[class*="XQDdHH"]', 'div[class*="_5OesEi"] span[class*="Y1HWO0"] div[class*="XQDdHH"]', 'div[class*="star"]', 'span[class*="rating"]']  # Enhanced
    },
    'reviews': {
        'type': 'css',
        'selectors': ['span[class*="Wphh3N"]', 'div[class*="_5OesEi"] span[class*="Wphh3N"]', 'span:contains("(")', 'span:contains("ratings")', 'div:contains("ratings")']  # Enhanced
    },
    'discount': {
        'type': 'css',
        'selectors': ['div[class*="UkUFwK"] span', 'div[class*="hl05eU"] div[class*="UkUFwK"] span', 'span:contains("% off")', 'div:contains("% off")']  # Enhanced
    },
    'offers': {
        'type': 'css',
        'selectors': ['div[class*="+7E521"]', 'div[class*="oUss6M"]', 'div[class*="offer"]', 'span[class*="coupon"]', 'div:contains("Save")']  # Enhanced
    }
}

# Example 2: Amazon configuration (simplified from main.py)
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

# Example 3: Simple configuration using helper function
simple_selectors = create_selector_config(
    product_container=['div.product', 'div[class*="item"]'],
    name_selectors=['h3', 'h2', 'a[title]'],
    price_selectors=['span.price', 'div.price', '.cost'],
    original_price_selectors=['span.original-price', 'del'],
    rating_selectors=['span.rating', 'div.stars'],
    reviews_selectors=['span.reviews', 'div.review-count']
)

def example_flipkart_scraping():
    """Example: Scraping Flipkart phone cases"""
    print("🛒 Example 1: Scraping Flipkart Phone Cases")
    print("=" * 50)
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync("https://www.flipkart.com/search?q=phone+case")
    
    # Step 2: Create scraper with HTML content
    scraper = GenericPlatformScraper(
        html_content=html_content,
        selector_config=flipkart_selectors,
        site_name="flipkart",
        url="https://www.flipkart.com/search?q=phone+case"
    )
    
    # Step 3: Scrape products
    products = scraper.scrape()
    csv_file = scraper.save_to_csv("flipkart_phone_cases.csv")
    json_file = scraper.save_to_json("flipkart_phone_cases.json")
    
    print(scraper.get_summary())
    print(f"📄 CSV saved: {csv_file}")
    print(f"📄 JSON saved: {json_file}")
    print()

def example_amazon_scraping():
    """Example: Scraping Amazon fridges"""
    print("🛒 Example 2: Scraping Amazon Fridges")
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

def example_simple_scraping():
    """Example: Using the convenience function"""
    print("🛒 Example 3: Using Convenience Function")
    print("=" * 50)
    
    # Step 1: Fetch HTML content
    print("📡 Fetching HTML content...")
    html_content = fetch_html_sync("https://www.flipkart.com/search?q=airpods")
    
    # Step 2: Use convenience function
    csv_file = scrape_platform(
        html_content=html_content,
        selector_config=flipkart_selectors,
        site_name="flipkart_airpods"
    )
    
    print(f"📄 CSV saved: {csv_file}")
    print()

def example_advanced_configuration():
    """Example: Advanced configuration with different selector types"""
    print("🛒 Example 4: Advanced Configuration")
    print("=" * 50)
    
    # Advanced configuration with different selector types
    advanced_selectors = {
        'product_container': {
            'type': 'css',
            'selectors': ['div.product-item', 'div[data-product]']
        },
        'name': {
            'type': 'css',
            'selectors': ['h2.product-title', 'a.product-link'],
            'attribute': 'title'  # Get title attribute
        },
        'current_price': {
            'type': 'css',
            'selectors': ['.price-current', '.current-price'],
            'regex': r'₹([\d,]+)'  # Extract price with regex
        },
        'rating': {
            'type': 'regex',
            'selectors': [r'(\d+\.?\d*)\s*stars?'],  # Regex pattern
            'pattern': r'(\d+\.?\d*)\s*stars?'
        }
    }
    
    print("Advanced configuration created (not executed to avoid errors)")
    print("This shows how to use different selector types and patterns")
    print()

def main():
    """Run all examples"""
    print("🚀 Generic Platform Scraper Examples")
    print("=" * 60)
    print()
    
    try:
        # Run examples
        example_flipkart_scraping()
        example_amazon_scraping()
        example_simple_scraping()
        example_advanced_configuration()
        
        print("✅ All examples completed!")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")

if __name__ == "__main__":
    main()
