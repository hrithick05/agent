import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import json

async def main():
    """
    Crawl4AI implementation using Virtual Scroll for infinite scroll pages
    This handles pages with lazy loading and infinite scroll like Meesho
    """
    
    # Configure browser for optimal performance
    browser_config = {
        "headless": True,  # Set to False to see browser in action
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "extra_args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor"
        ]
    }
    
    # Define comprehensive extraction schema for e-commerce products
    extraction_schema = {
        "products": [
            {
                "name": "h1, h2, h3, h4, h5, [class*='title'], [class*='name'], [class*='product-title'], [class*='product-name']",
                "current_price": "[class*='price'], [class*='current-price'], [class*='selling-price'], span:contains('₹'), div:contains('₹'), [class*='amount']",
                "original_price": "[class*='mrp'], [class*='original-price'], [class*='strike'], [class*='was-price']",
                "image": "img[src], img[data-src], img[data-lazy-src], [class*='product-image'] img",
                "link": "a[href*='/p/'], a[href*='/product/'], a[href*='/dp/']",
                "rating": "[class*='rating'], [class*='star'], [class*='score'], [class*='review-rating']",
                "reviews": "[class*='review'], [class*='rating-count'], [class*='review-count']",
                "discount": "[class*='discount'], [class*='offer'], [class*='save'], [class*='off']",
                "availability": "[class*='stock'], [class*='available'], [class*='out-of-stock']"
            }
        ]
    }
    
    # Create extraction strategy
    extraction_strategy = JsonCssExtractionStrategy(schema=extraction_schema)
    
    async with AsyncWebCrawler(browser_config=browser_config) as crawler:
        print("🚀 Starting Virtual Scroll Crawl for infinite scroll page...")
        print("=" * 60)
        
        # Advanced JavaScript for handling virtual scroll and lazy loading
        virtual_scroll_js = [
            # Wait for initial page load
            "await new Promise(resolve => setTimeout(resolve, 3000));",
            
            # Function to scroll and wait for content to load
            "async function scrollAndWait() {",
            "  const initialHeight = document.body.scrollHeight;",
            "  window.scrollTo(0, document.body.scrollHeight);",
            "  await new Promise(resolve => setTimeout(resolve, 2000));",
            "  const newHeight = document.body.scrollHeight;",
            "  return newHeight > initialHeight;",
            "}",
            
            # Perform multiple scrolls to load all content
            "let scrollCount = 0;",
            "let maxScrolls = 10;",  # Maximum number of scroll attempts
            "while (scrollCount < maxScrolls) {",
            "  const hasNewContent = await scrollAndWait();",
            "  if (!hasNewContent) break;",
            "  scrollCount++;",
            "  console.log(`Scroll ${scrollCount} completed`);",
            "}",
            
            # Try to trigger any "Load More" buttons
            "const loadMoreSelectors = [",
            "  'button:contains(\"Load More\")',",
            "  'button:contains(\"Show More\")',",
            "  '[class*=\"load-more\"]',",
            "  '[class*=\"show-more\"]',",
            "  '[class*=\"pagination\"] button'",
            "];",
            "for (const selector of loadMoreSelectors) {",
            "  try {",
            "    const btn = document.querySelector(selector);",
            "    if (btn && btn.offsetParent !== null) {",
            "      btn.click();",
            "      await new Promise(resolve => setTimeout(resolve, 3000));",
            "    }",
            "  } catch (e) { console.log('Button not found:', selector); }",
            "}",
            
            # Final scroll to ensure all content is visible
            "window.scrollTo(0, document.body.scrollHeight);",
            "await new Promise(resolve => setTimeout(resolve, 2000));",
            
            # Scroll back to top to ensure we have the full page
            "window.scrollTo(0, 0);",
            "await new Promise(resolve => setTimeout(resolve, 1000));",
        ]
        
        # Run the crawler with virtual scroll handling
        result = await crawler.arun(
            url="https://www.meesho.com/search?q=perfumes",
            extraction_strategy=extraction_strategy,
            # Virtual scroll and lazy loading parameters
            delay_before_return_html=15,  # Wait 15 seconds for all content to load
            wait_for="networkidle",
            js_code=virtual_scroll_js,
            # Additional options
            cache_mode="bypass",
            remove_overlay=True,
            simulate_user=True,
            word_count_threshold=100,  # Higher threshold for better content detection
        )
        
        print(f"✅ Virtual Scroll Crawl completed!")
        print(f"📊 Status: {result.success}")
        print(f"📄 Content length: {len(result.cleaned_html)} characters")
        print(f"📝 Markdown length: {len(result.markdown)} characters")
        print("=" * 60)
        
        # Analyze extracted products
        if result.extracted_content:
            print("🎯 EXTRACTED PRODUCT DATA:")
            print("=" * 60)
            try:
                extracted_data = json.loads(result.extracted_content)
                if 'products' in extracted_data and extracted_data['products']:
                    products = extracted_data['products']
                    print(f"Found {len(products)} products!")
                    
                    # Filter out empty products
                    valid_products = [p for p in products if any(v for v in p.values() if v and str(v).strip())]
                    print(f"Valid products (with data): {len(valid_products)}")
                    
                    # Show first 10 products
                    for i, product in enumerate(valid_products[:10], 1):
                        print(f"\n📦 Product {i}:")
                        for key, value in product.items():
                            if value and str(value).strip():
                                # Truncate long values
                                display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                                print(f"  {key}: {display_value}")
                else:
                    print("No products found in extracted data")
                    print("Raw extracted content:")
                    print(result.extracted_content[:1000])
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print("Raw extracted content:")
                print(result.extracted_content[:1000])
        else:
            print("❌ No extracted content found")
        
        # Content analysis
        print("\n" + "=" * 60)
        print("📋 CONTENT ANALYSIS:")
        print("=" * 60)
        
        # Check for e-commerce indicators
        ecommerce_indicators = [
            'perfume', 'price', '₹', 'Rs', 'rating', 'review', 'discount', 
            'offer', 'add to cart', 'buy now', 'product', 'item'
        ]
        found_indicators = [ind for ind in ecommerce_indicators if ind.lower() in result.markdown.lower()]
        print(f"E-commerce indicators found: {found_indicators}")
        
        # Check content quality
        if len(result.markdown) > 5000:
            print("✅ Good content length - likely captured dynamic content")
        elif len(result.markdown) > 1000:
            print("⚠️ Moderate content length - some content captured")
        else:
            print("❌ Low content length - may not have captured dynamic content")
        
        # Show content sample
        print(f"\n📝 Content sample (first 800 chars):")
        print(result.markdown[:800])
        
        # Save results
        results_data = {
            "url": result.url,
            "success": result.success,
            "extracted_content": result.extracted_content,
            "markdown_preview": result.markdown[:4000],
            "html_length": len(result.cleaned_html),
            "markdown_length": len(result.markdown),
            "ecommerce_indicators_found": found_indicators,
            "content_quality": "Good" if len(result.markdown) > 5000 else "Moderate" if len(result.markdown) > 1000 else "Low"
        }
        
        with open("meesho_virtual_scroll_results.json", "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: meesho_virtual_scroll_results.json")
        
        return result

if __name__ == "__main__":
    # Run the virtual scroll crawling
    asyncio.run(main())
