import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=True
    )
    
    run_config = CrawlerRunConfig(
        # DON'T use wait_for at all!
        # wait_for="css:.product-item",  ❌ REMOVE THIS LINE
        
        # Just use these:
        wait_until="networkidle",  # Wait for page to finish loading
        page_timeout=60000,
        delay_before_return_html=3.0,  # Extra 3 seconds for safety
        cache_mode=CacheMode.BYPASS
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://thelittle.in/categories/school-stationery",
            config=run_config
        )
        
        if result.success:
            print("✅ SUCCESS!")
            print(f"HTML length: {len(result.html)} characters")
            
            # Save the HTML
            with open('scraped_products.html', 'w', encoding='utf-8') as f:
                f.write(result.html)
            
            print("Saved to scraped_products.html")
        else:
            print(f"❌ Error: {result.error_message}")

asyncio.run(main())
