"""Simple HTML Fetcher using Crawl4AI

Prereqs:
  pip install crawl4ai
  crawl4ai-setup

Usage:
  from fetchHTML import fetch_html
  html_content = await fetch_html("https://example.com")
  # or save to file
  html_content = await fetch_html("https://example.com", "output.html")
"""

import asyncio
import os
from typing import Optional

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
except Exception as exc:
    raise SystemExit(
        "This script requires 'crawl4ai'. Install with: pip install crawl4ai"
    ) from exc


async def fetch_html(url: str, output_file: Optional[str] = None) -> str:
    """
    Fetch HTML from URL using Crawl4AI.
    
    Args:
        url: Target URL to fetch
        output_file: Optional file path to save HTML (if None, only returns content)
    
    Returns:
        HTML content as string
    
    Raises:
        Exception: If scraping fails
    """
    config = CrawlerRunConfig()
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        if not getattr(result, "success", False):
            msg = getattr(result, "error_message", "Unknown error")
            raise Exception(f"Failed to scrape {url}: {msg}")

        # Get HTML content
        html_content: str = getattr(result, "html", "") or ""
        
        # Save to file if path provided
        if output_file:
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            with open(output_file, "w", encoding="utf-8", errors="ignore") as f:
                f.write(html_content)
            print(f"✅ HTML saved to {output_file} ({len(html_content)} bytes)")
        
        return html_content


def fetch_html_sync(url: str, output_file: Optional[str] = None) -> str:
    """
    Synchronous wrapper for fetch_html function.
    
    Args:
        url: Target URL to fetch
        output_file: Optional file path to save HTML (if None, only returns content)
    
    Returns:
        HTML content as string
    """
    return asyncio.run(fetch_html(url, output_file))

