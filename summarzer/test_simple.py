import asyncio
import os
import sys
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import json

# Set environment variables to avoid Unicode issues
os.environ['PYTHONIOENCODING'] = 'utf-8'

async def main():
    """
    Simple Crawl4AI implementation for JavaScript-heavy pages
    """
    
    print("Starting Crawl4AI test for Meesho...")
    
    # Define extraction strategy for product data
    extraction_strategy = JsonCssExtractionStrategy(
        schema={
            "products": [
                {
                    "name": "h3, h4, h5, [class*='title'], [class*='name']",
                    "price": "[class*='price'], span:contains('₹'), div:contains('₹')",
                    "image": "img[src], img[data-src]",
                    "link": "a[href]",
                    "rating": "[class*='rating'], [class*='star']",
                    "reviews": "[class*='review'], [class*='rating']",
                    "discount": "[class*='discount'], [class*='offer']"
                }
            ]
        }
    )
    
    try:
        # Create crawler with minimal configuration
        async with AsyncWebCrawler(verbose=False) as crawler:
            
            print("Crawler initialized successfully!")
            print("Starting crawl...")
            
            # Run the crawler with JavaScript handling
            result = await crawler.arun(
                url="https://www.meesho.com/search?q=perfumes",
                extraction_strategy=extraction_strategy,
                delay_before_return_html=10,  # Wait 10 seconds for JS to load
                wait_for="networkidle",  # Wait for network to be idle
                js_code=[
                    # Wait for initial load
                    "await new Promise(resolve => setTimeout(resolve, 3000));",
                    # Scroll to load more content
                    "window.scrollTo(0, document.body.scrollHeight);",
                    "await new Promise(resolve => setTimeout(resolve, 2000));",
                    "window.scrollTo(0, document.body.scrollHeight);",
                    "await new Promise(resolve => setTimeout(resolve, 2000));",
                ],
                word_count_threshold=10,
                cache_mode="bypass"
            )
            
            print("Crawl completed!")
            print(f"Status: {result.success}")
            print(f"Content length: {len(result.cleaned_html)} characters")
            print(f"Markdown length: {len(result.markdown)} characters")
            
            # Analyze extracted products
            if result.extracted_content:
                print("\nExtracted Product Data:")
                try:
                    extracted_data = json.loads(result.extracted_content)
                    if 'products' in extracted_data and extracted_data['products']:
                        products = extracted_data['products']
                        print(f"Found {len(products)} products!")
                        
                        # Show first 5 products
                        for i, product in enumerate(products[:5], 1):
                            print(f"\nProduct {i}:")
                            for key, value in product.items():
                                if value and str(value).strip():
                                    print(f"  {key}: {value}")
                    else:
                        print("No products found in extracted data")
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")
                    print("Raw extracted content:")
                    print(result.extracted_content[:500])
            else:
                print("No extracted content found")
            
            # Check content quality
            print(f"\nContent Analysis:")
            if len(result.markdown) > 5000:
                print("Good content length - likely captured dynamic content")
            elif len(result.markdown) > 1000:
                print("Moderate content length - some content captured")
            else:
                print("Low content length - may not have captured dynamic content")
            
            # Look for product indicators
            indicators = ['perfume', 'price', '₹', 'Rs', 'rating', 'review', 'discount']
            found_indicators = [ind for ind in indicators if ind.lower() in result.markdown.lower()]
            print(f"E-commerce indicators found: {found_indicators}")
            
            # Save results
            results_data = {
                "url": result.url,
                "success": result.success,
                "extracted_content": result.extracted_content,
                "markdown_preview": result.markdown[:2000],
                "html_length": len(result.cleaned_html),
                "markdown_length": len(result.markdown),
                "indicators_found": found_indicators
            }
            
            with open("meesho_simple_crawl_results.json", "w", encoding="utf-8") as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            print(f"\nResults saved to: meesho_simple_crawl_results.json")
            
            return result
            
    except Exception as e:
        print(f"Error during crawling: {e}")
        return None

if __name__ == "__main__":
    # Run the simple crawling
    asyncio.run(main())

