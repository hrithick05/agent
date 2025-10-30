#!/usr/bin/env python3
"""
Configuration Converter
Converts existing main.py site configurations to generic scraper format.
"""

from generic_scraper import convert_main_config, create_selector_config

# Import the site configurations from main.py
def get_main_configs():
    """Get site configurations from main.py format"""
    return {
        'amazon': {
            'name': 'Amazon India',
            'url': 'https://www.amazon.in/s?k=fridge+double+door+fridge+5+star',
            'product_selector': 'div[data-component-type="s-search-result"]',
            'name_selectors': [
                'h2.a-size-medium span',
                'h2.a-size-medium',
                'span.a-size-medium'
            ],
            'price_selectors': [
                'span.a-price-whole',
                '.a-price .a-price-whole',
                'span.a-price[data-a-size="xl"]'
            ],
            'original_price_selectors': [
                'span.a-price.a-text-price',
                'span.a-text-price'
            ],
            'rating_selectors': [
                'span.a-size-small.a-color-base',
                '.a-icon-alt'
            ],
            'reviews_selectors': [
                'span.a-size-mini',
                'a[href*="customerReviews"] span'
            ],
            'discount_selectors': [
                'span:contains("% off")',
                'span:contains("off")'
            ],
            'offers_selectors': [
                'span.s-coupon-unclipped',
                'span.a-color-base:contains("coupon")',
                'span:contains("back with")'
            ]
        },
        
        'flipkart': {
            'name': 'Flipkart',
            'url': 'https://www.flipkart.com/search?q=phone%20case',
            'product_selector': 'div[class*="_4WELSP"]',
            'name_selectors': [
                'a[class*="wjcEIp"]',
                'a[title]',
                'img[alt]',
                'a[href*="/p/"]'
            ],
            'price_selectors': [
                'div[class*="Nx9bqj"]',
                'div[class*="hl05eU"] div[class*="Nx9bqj"]',
                'div:contains("₹")',
                'span:contains("₹")'
            ],
            'original_price_selectors': [
                'div[class*="yRaY8j"]',
                'div[class*="hl05eU"] div[class*="yRaY8j"]',
                'span[class*="strike"]',
                'del'
            ],
            'rating_selectors': [
                'div[class*="XQDdHH"]',
                'span[class*="Y1HWO0"] div[class*="XQDdHH"]',
                'div[class*="_5OesEi"] span[class*="Y1HWO0"] div[class*="XQDdHH"]',
                'div[class*="star"]',
                'span[class*="rating"]'
            ],
            'reviews_selectors': [
                'span[class*="Wphh3N"]',
                'div[class*="_5OesEi"] span[class*="Wphh3N"]',
                'span:contains("(")',
                'span:contains("ratings")',
                'div:contains("ratings")'
            ],
            'discount_selectors': [
                'div[class*="UkUFwK"] span',
                'div[class*="hl05eU"] div[class*="UkUFwK"] span',
                'span:contains("% off")',
                'div:contains("% off")'
            ],
            'offers_selectors': [
                'div[class*="+7E521"]',
                'div[class*="oUss6M"]',
                'div[class*="offer"]',
                'span[class*="coupon"]',
                'div:contains("Save")'
            ]
        },
        
        'meesho': {
            'name': 'Meesho',
            'url': 'https://www.meesho.com/search?q=perfumes',
            'product_selector': 'div[class*="product"]',
            'name_selectors': [
                'div[class*="title"]',
                'h1', 'h2', 'h3',
                'span[class*="title"]'
            ],
            'price_selectors': [
                'span[class*="price"]',
                'div[class*="price"]',
                'span[class*="amount"]'
            ],
            'original_price_selectors': [
                'span[class*="strike"]',
                'span[class*="original"]'
            ],
            'rating_selectors': [
                'span[class*="rating"]',
                'div[class*="star"]',
                'span[class*="score"]'
            ],
            'reviews_selectors': [
                'span[class*="review"]',
                'span:contains("ratings")'
            ],
            'discount_selectors': [
                'span:contains("% off")',
                'span:contains("off")'
            ],
            'offers_selectors': [
                'span[class*="offer"]',
                'div[class*="coupon"]'
            ]
        },
        
        'sathya': {
            'name': 'Sathya Store',
            'url': 'https://www.sathya.store/search?category=&q=vivo+mobile',
            'product_selector': 'div.product-box',
            'name_selectors': [
                'a[href*="/category/"]',
                'img[alt]',
                'h4',
                'h3',
                'div[class*="title"]'
            ],
            'price_selectors': [
                'h4:contains("₹")',
                'span:contains("₹")',
                'div:contains("₹")',
                'p:contains("₹")'
            ],
            'original_price_selectors': [
                'span[class*="strike"]',
                'span[class*="original"]',
                'del',
                'span:contains("MRP")',
                'span:contains("M.R.P")',
                'div:contains("MRP")',
                'p:contains("MRP")'
            ],
            'rating_selectors': [
                'div[class*="star"]',
                'span[class*="rating"]',
                'div[class*="review"]',
                'div[class*="rating"]',
                'span[class*="score"]',
                'div[class*="Rating"]'
            ],
            'reviews_selectors': [
                'span[class*="review"]',
                'span:contains("ratings")',
                'div:contains("ratings")',
                'span:contains("Reviews")',
                'div:contains("Reviews")',
                'span[class*="Review"]'
            ],
            'discount_selectors': [
                'span:contains("% off")',
                'span:contains("off")',
                'div:contains("Save")'
            ],
            'offers_selectors': [
                'span[class*="offer"]',
                'div[class*="coupon"]',
                'div:contains("Save")'
            ]
        }
    }

def convert_all_configs():
    """Convert all main.py configurations to generic scraper format"""
    main_configs = get_main_configs()
    converted_configs = {}
    
    for site_name, config in main_configs.items():
        converted_configs[site_name] = convert_main_config(config)
        print(f"✅ Converted {site_name} configuration")
    
    return converted_configs

def get_flipkart_advanced_config():
    """Get advanced Flipkart configuration based on out.json analysis"""
    return {
        'product_container': {
            'type': 'css',
            'selectors': ['div[data-id]', 'div[class*="slAVV4"]', 'div[class*="_4WELSP"]']
        },
        'name': {
            'type': 'css',
            'selectors': ['img[alt]', 'a[class*="wjcEIp"]', 'a[title]', 'a[href*="/p/"]']
        },
        'current_price': {
            'type': 'css',
            'selectors': ['div[class*="Nx9bqj"]', 'div[class*="hl05eU"] div[class*="Nx9bqj"]', 'div:contains("₹")', 'span:contains("₹")']
        },
        'original_price': {
            'type': 'css',
            'selectors': ['div[class*="yRaY8j"]', 'div[class*="hl05eU"] div[class*="yRaY8j"]', 'span[class*="strike"]', 'del']
        },
        'rating': {
            'type': 'css',
            'selectors': ['div[class*="XQDdHH"]', 'span[class*="Y1HWO0"] div[class*="XQDdHH"]', 'div[class*="_5OesEi"] span[class*="Y1HWO0"] div[class*="XQDdHH"]', 'div[class*="star"]', 'span[class*="rating"]']
        },
        'reviews': {
            'type': 'css',
            'selectors': ['span[class*="Wphh3N"]', 'div[class*="_5OesEi"] span[class*="Wphh3N"]', 'span:contains("(")', 'span:contains("ratings")', 'div:contains("ratings")']
        },
        'discount': {
            'type': 'css',
            'selectors': ['div[class*="UkUFwK"] span', 'div[class*="hl05eU"] div[class*="UkUFwK"] span', 'span:contains("% off")', 'div:contains("% off")']
        },
        'offers': {
            'type': 'css',
            'selectors': ['div[class*="+7E521"]', 'div[class*="oUss6M"]', 'div[class*="offer"]', 'span[class*="coupon"]', 'div:contains("Save")']
        }
    }

def print_config_examples():
    """Print example configurations for different platforms"""
    print("🔧 Configuration Examples")
    print("=" * 50)
    
    # Convert all main.py configs
    converted = convert_all_configs()
    
    print("\n📋 Available Platform Configurations:")
    for site_name in converted.keys():
        print(f"  - {site_name}")
    
    print("\n📝 Example Usage:")
    print("""
# Using converted main.py configs
from config_converter import convert_all_configs
from generic_scraper import GenericPlatformScraper

configs = convert_all_configs()
scraper = GenericPlatformScraper(
    url="https://www.flipkart.com/search?q=phone+case",
    selector_config=configs['flipkart'],
    site_name="flipkart"
)
await scraper.scrape()
    """)
    
    print("\n📝 Advanced Flipkart Configuration:")
    advanced_config = get_flipkart_advanced_config()
    print(f"Product containers: {advanced_config['product_container']['selectors']}")
    print(f"Name selectors: {advanced_config['name']['selectors']}")
    print(f"Price selectors: {advanced_config['current_price']['selectors']}")

if __name__ == "__main__":
    print_config_examples()
