"""Fetch a URL with Crawl4AI and save raw HTML to a file (function-based).

Prereqs:
  pip install crawl4ai
  crawl4ai-setup   # installs Playwright browsers

Usage:
  from fetch_html_crawl4ai import fetch_html
  await fetch_html("https://example.com", "output.html")
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "This script requires 'crawl4ai'. Install with: pip install crawl4ai"
    ) from exc


async def fetch_html(url: str, output_file: str, wait_ms: int = 0) -> str:
    """
    Fetch HTML from URL using Crawl4AI and save to file.
    
    Args:
        url: Target URL to fetch
        output_file: Output HTML file path
        wait_ms: Wait time in milliseconds (default: 0)
    
    Returns:
        Path to the saved HTML file
    
    Raises:
        Exception: If scraping fails
    """
    config = CrawlerRunConfig()
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        if not getattr(result, "success", False):
            msg = getattr(result, "error_message", "Unknown error")
            raise Exception(f"Failed to scrape {url}: {msg}")

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

        # Save raw HTML
        html: str = getattr(result, "html", "") or ""
        with open(output_file, "w", encoding="utf-8", errors="ignore") as f:
            f.write(html)
        
        print(f"✅ HTML saved to {output_file} ({len(html)} bytes)")
        return output_file


def fetch_html_sync(url: str, output_file: str, wait_ms: int = 0) -> str:
    """
    Synchronous wrapper for fetch_html function.
    
    Args:
        url: Target URL to fetch
        output_file: Output HTML file path
        wait_ms: Wait time in milliseconds (default: 0)
    
    Returns:
        Path to the saved HTML file
    """
    return asyncio.run(fetch_html(url, output_file, wait_ms))


async def main():
    """Example usage of the fetch_html function"""
    print("🌐 HTML Fetcher Examples")
    print("=" * 50)
    
    # Example 1: Fetch Flipkart phone cases
    print("📱 Example 1: Fetching Flipkart Phone Cases")
    try:
        html_file = await fetch_html(
            url="https://www.meesho.com/search?q=perfumes",
            output_file="pages/meesho_perfumes.html"
        )
        print(f"✅ Success: {html_file}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Example 2: Fetch Amazon fridges
    print("🧊 Example 2: Fetching Amazon Fridges")
    try:
        html_file = await fetch_html(
            url="https://www.amazon.in/s?k=fridge+double+door+fridge+5+star",
            output_file="pages/amazon_fridges.html"
        )
        print(f"✅ Success: {html_file}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Example 3: Using sync wrapper
    print("🔄 Example 3: Using Sync Wrapper")
    try:
        html_file = fetch_html_sync(
            url="https://www.flipkart.com/search?q=airpods",
            output_file="pages/flipkart_airpods.html"
        )
        print(f"✅ Success: {html_file}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())


