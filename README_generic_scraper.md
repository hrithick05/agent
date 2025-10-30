# Generic Platform Scraper

A flexible, universal scraper that can extract product data from any e-commerce platform by accepting URL and selector configurations programmatically.

## Features

- **Universal**: Works with any e-commerce platform
- **Flexible Selectors**: Supports CSS, XPath, and regex patterns
- **Async**: Built on crawl4ai for fast, reliable HTML fetching
- **Standardized Output**: Fixed CSV format matching your requirements
- **Robust**: Multiple fallback selectors and error handling
- **Easy Integration**: Simple function-based API

## Quick Start

### Basic Usage

```python
import asyncio
from generic_scraper import GenericPlatformScraper

# Define selectors for your platform
selector_config = {
    'product_container': {
        'type': 'css',
        'selectors': ['div.product', 'div[data-id]']
    },
    'name': {
        'type': 'css',
        'selectors': ['h3.product-title', 'a.product-link'],
        'attribute': 'title'  # Get title attribute
    },
    'current_price': {
        'type': 'css',
        'selectors': ['span.price', '.current-price'],
        'regex': r'₹([\d,]+)'  # Extract price with regex
    }
}

# Create scraper
scraper = GenericPlatformScraper(
    url="https://example-store.com/products",
    selector_config=selector_config,
    site_name="example_store"
)

# Scrape and save
async def main():
    await scraper.scrape()
    csv_file = scraper.save_to_csv("products.csv")
    print(f"Saved to: {csv_file}")

asyncio.run(main())
```

### Using Convenience Function

```python
from generic_scraper import scrape_platform

csv_file = await scrape_platform(
    url="https://www.flipkart.com/search?q=phone+case",
    selector_config=flipkart_selectors,
    site_name="flipkart"
)
```

## Selector Configuration

### Supported Selector Types

1. **CSS Selectors** (default)
```python
'name': {
    'type': 'css',
    'selectors': ['h3.title', 'a.product-link'],
    'attribute': 'title'  # Optional: get attribute instead of text
}
```

2. **Regex Patterns**
```python
'price': {
    'type': 'regex',
    'selectors': [r'₹([\d,]+)'],
    'pattern': r'₹([\d,]+)'
}
```

3. **XPath Selectors** (limited support)
```python
'rating': {
    'type': 'xpath',
    'selectors': ['.//span[@class="rating"]/text()']
}
```

### Complete Configuration Example

```python
selector_config = {
    'product_container': {
        'type': 'css',
        'selectors': ['div.product-item', 'div[data-product]']
    },
    'name': {
        'type': 'css',
        'selectors': ['h2.product-title', 'a.product-link'],
        'attribute': 'title'
    },
    'current_price': {
        'type': 'css',
        'selectors': ['.price-current', '.current-price'],
        'regex': r'₹([\d,]+)'
    },
    'original_price': {
        'type': 'css',
        'selectors': ['.price-original', 'del']
    },
    'rating': {
        'type': 'css',
        'selectors': ['.rating', '.stars'],
        'regex': r'(\d+\.?\d*)'
    },
    'reviews': {
        'type': 'css',
        'selectors': ['.review-count', 'span:contains("reviews")']
    },
    'discount': {
        'type': 'css',
        'selectors': ['.discount', 'span:contains("% off")']
    },
    'offers': {
        'type': 'css',
        'selectors': ['.offers', '.coupons']
    },
    'delivery': {
        'type': 'css',
        'selectors': ['.delivery-info', 'span:contains("delivery")']
    },
    'availability': {
        'type': 'css',
        'selectors': ['.stock', '.availability']
    }
}
```

## Output Format

The scraper outputs data in a standardized CSV format with these columns:

- `index`: Product number
- `name`: Product name
- `current_price`: Current selling price
- `original_price`: Original/MRP price
- `rating`: Product rating
- `reviews`: Number of reviews
- `discount`: Discount percentage
- `offers`: Available offers
- `delivery`: Delivery information
- `availability`: Stock availability
- `site`: Site/platform name
- `scraped_at`: Timestamp

## Examples

### Example 1: Flipkart (Advanced Configuration)

```python
from generic_scraper import GenericPlatformScraper
from config_converter import get_flipkart_advanced_config

# Use pre-configured Flipkart selectors
selector_config = get_flipkart_advanced_config()

scraper = GenericPlatformScraper(
    url="https://www.flipkart.com/search?q=phone+case",
    selector_config=selector_config,
    site_name="flipkart"
)

await scraper.scrape()
csv_file = scraper.save_to_csv("flipkart_products.csv")
```

### Example 2: Convert from main.py Configurations

```python
from config_converter import convert_all_configs
from generic_scraper import GenericPlatformScraper

# Convert existing main.py configurations
configs = convert_all_configs()
amazon_config = configs['amazon']

scraper = GenericPlatformScraper(
    url="https://www.amazon.in/s?k=fridge",
    selector_config=amazon_config,
    site_name="amazon"
)

await scraper.scrape()
```

### Example 3: Simple Configuration Helper

```python
from generic_scraper import create_selector_config, GenericPlatformScraper

# Create simple configuration
selector_config = create_selector_config(
    product_container=['div.product', 'div[class*="item"]'],
    name_selectors=['h3', 'h2', 'a[title]'],
    price_selectors=['span.price', 'div.price'],
    rating_selectors=['span.rating', 'div.stars']
)

scraper = GenericPlatformScraper(
    url="https://example-store.com/products",
    selector_config=selector_config,
    site_name="example"
)
```

## Advanced Features

### Multiple Extraction Strategies

```python
'name': {
    'type': 'css',
    'selectors': [
        'h2.product-title',      # Primary selector
        'a.product-link',       # Fallback 1
        'img[alt]'              # Fallback 2
    ],
    'attribute': 'title'        # Get title attribute
}
```

### Regex Cleanup

```python
'current_price': {
    'type': 'css',
    'selectors': ['.price'],
    'regex': r'₹([\d,]+)'       # Extract only price number
}
```

### Attribute Extraction

```python
'name': {
    'type': 'css',
    'selectors': ['a.product-link'],
    'attribute': 'title'        # Get title attribute instead of text
}
```

## Error Handling

The scraper includes robust error handling:

- **Selector Fallbacks**: If one selector fails, tries the next
- **Validation**: Ensures products have meaningful data
- **Logging**: Detailed logs for debugging
- **Graceful Degradation**: Continues even if some products fail

## Testing

Run the test suite:

```bash
python test_generic_scraper.py
```

Run examples:

```bash
python example_usage.py
```

## Files

- `generic_scraper.py` - Main scraper class
- `config_converter.py` - Convert main.py configs to new format
- `example_usage.py` - Usage examples
- `test_generic_scraper.py` - Test suite
- `README_generic_scraper.md` - This documentation

## Integration with Existing Code

The generic scraper is designed to work alongside your existing `main.py`:

1. **Backward Compatible**: Keep using `main.py` for existing workflows
2. **Easy Migration**: Convert existing configs with `config_converter.py`
3. **Flexible**: Use generic scraper for new platforms or custom needs

## Performance

- **Async**: Non-blocking HTML fetching
- **Efficient**: Only extracts configured fields
- **Robust**: Handles large product catalogs
- **Fast**: Optimized selector matching

## Troubleshooting

### Common Issues

1. **No products found**: Check product container selectors
2. **Missing data**: Add more fallback selectors
3. **Invalid selectors**: Use browser dev tools to verify selectors
4. **Rate limiting**: Add delays between requests

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

To add support for new platforms:

1. Identify the HTML structure
2. Create selector configuration
3. Test with sample products
4. Add to examples if useful for others
