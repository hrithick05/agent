import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import json

async def main():
    """
    Advanced Crawl4AI implementation using Adaptive Crawling
    This uses the new Adaptive Crawling feature for JavaScript-heavy pages
    """
    
    # Configure browser for stealth and JavaScript execution
    browser_config = {
        "headless": True,  # Set to False to see browser in action
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "extra_args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-images",  # Faster loading
        ]
    }
    
    # Use LLM-based extraction strategy for better product detection
    extraction_strategy = LLMExtractionStrategy(
        provider="ollama/llama3.1",  # You can change this to your preferred LLM
        api_token="your-api-token",  # Replace with your API token
        instruction="""
        Extract all product information from this e-commerce page. 
        Look for:
        - Product names/titles
        - Prices (current and original)
        - Product images
        - Ratings and reviews
        - Discounts and offers
        - Product links
        
        Return the data in JSON format with this structure:
        {
            "products": [
                {
                    "name": "product name",
                    "current_price": "current price",
                    "original_price": "original price if available",
                    "image_url": "product image URL",
                    "product_url": "product page URL",
                    "rating": "rating if available",
                    "reviews": "number of reviews if available",
                    "discount": "discount percentage if available",
                    "offers": "special offers if available"
                }
            ]
        }
        """
    )
    
    async with AsyncWebCrawler(browser_config=browser_config) as crawler:
        print("🚀 Starting Adaptive Crawl for JavaScript-heavy page...")
        print("=" * 60)
        
        # Use adaptive crawling with custom JavaScript execution
        result = await crawler.arun(
            url="https://www.meesho.com/search?q=perfumes",
            extraction_strategy=extraction_strategy,
            # Adaptive crawling parameters
            word_count_threshold=50,  # Minimum words to consider content loaded
            delay_before_return_html=10,  # Wait 10 seconds for JS to load
            wait_for="networkidle",  # Wait for network to be idle
            # Custom JavaScript to handle dynamic loading
            js_code=[
                # Wait for initial load
                "await new Promise(resolve => setTimeout(resolve, 3000));",
                
                # Scroll to trigger lazy loading
                "window.scrollTo(0, document.body.scrollHeight);",
                "await new Promise(resolve => setTimeout(resolve, 2000));",
                
                # Scroll back up and down to trigger more loading
                "window.scrollTo(0, 0);",
                "await new Promise(resolve => setTimeout(resolve, 1000));",
                "window.scrollTo(0, document.body.scrollHeight);",
                "await new Promise(resolve => setTimeout(resolve, 2000));",
                
                # Try to click "Load More" button if it exists
                "const loadMoreBtn = document.querySelector('[class*=\"load\"], [class*=\"more\"], button:contains(\"Load\")');",
                "if (loadMoreBtn) { loadMoreBtn.click(); await new Promise(resolve => setTimeout(resolve, 3000)); }",
                
                # Final scroll to ensure all content is loaded
                "window.scrollTo(0, document.body.scrollHeight);",
                "await new Promise(resolve => setTimeout(resolve, 2000));",
            ],
            # Additional options for better content extraction
            cache_mode="bypass",
            remove_overlay=True,  # Remove overlays that might block content
            simulate_user=True,   # Simulate human-like behavior
        )
        
        print(f"✅ Adaptive Crawl completed!")
        print(f"📊 Status: {result.success}")
        print(f"📄 Content length: {len(result.cleaned_html)} characters")
        print(f"📝 Markdown length: {len(result.markdown)} characters")
        print("=" * 60)
        
        # Analyze the results
        if result.extracted_content:
            print("🎯 EXTRACTED PRODUCT DATA:")
            print("=" * 60)
            try:
                extracted_data = json.loads(result.extracted_content)
                if 'products' in extracted_data and extracted_data['products']:
                    print(f"Found {len(extracted_data['products'])} products:")
                    for i, product in enumerate(extracted_data['products'][:10], 1):  # Show first 10
                        print(f"\n📦 Product {i}:")
                        for key, value in product.items():
                            if value and str(value).strip():
                                print(f"  {key}: {value}")
                else:
                    print("No products found in extracted data")
                    print("Raw extracted content:")
                    print(result.extracted_content[:500])
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print("Raw extracted content:")
                print(result.extracted_content[:1000])
        else:
            print("❌ No extracted content found")
        
        # Check if we got meaningful content
        if len(result.markdown) > 1000:
            print("\n" + "=" * 60)
            print("📋 CONTENT ANALYSIS:")
            print("=" * 60)
            
            # Look for product-related keywords in the content
            keywords = ['perfume', 'price', '₹', 'Rs', 'rating', 'review', 'discount', 'offer']
            found_keywords = [kw for kw in keywords if kw.lower() in result.markdown.lower()]
            print(f"Found keywords: {found_keywords}")
            
            # Show a sample of the content
            print(f"\n📝 Content sample (first 500 chars):")
            print(result.markdown[:500])
            
            if 'perfume' in result.markdown.lower():
                print("✅ Successfully found perfume-related content!")
            else:
                print("⚠️ No perfume-related content found - page might still be loading")
        
        # Save comprehensive results
        results_data = {
            "url": result.url,
            "success": result.success,
            "extracted_content": result.extracted_content,
            "markdown_preview": result.markdown[:3000],
            "html_length": len(result.cleaned_html),
            "markdown_length": len(result.markdown),
            "crawl_timestamp": result.timestamp if hasattr(result, 'timestamp') else None,
            "metadata": result.metadata if hasattr(result, 'metadata') else None
        }
        
        with open("meesho_adaptive_crawl_results.json", "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Comprehensive results saved to: meesho_adaptive_crawl_results.json")
        
        return result

if __name__ == "__main__":
    # Run the adaptive crawling
    asyncio.run(main())
