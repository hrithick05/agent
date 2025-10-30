# LangGraph + Gemini 2.5 Autonomous Scraping Agent

This agent implements the same functionality as `mcp_server.py` but uses LangGraph for state management and Gemini 2.5 for intelligent tool orchestration.

## Architecture

- **LangGraph**: Manages agent state and workflow orchestration
- **Gemini 2.5**: Powers autonomous decision-making and tool calling
- **Global State**: Uses same global variables as `mcp_server.py` (`html_content`, `summary`, `selector_template`, `GenericPlatformScraperObj`)

## Workflow (Matches mcp_server.py Pattern)

1. **Fetch HTML**: `get_html(url)` - Fetches and analyzes HTML
2. **Understand Structure**: `readsummary()`, `readHTML()`, `get_available_fields()`
3. **Configure Selectors**: `set_selector(field, selector_type, selectors)` for each field
4. **Create Scraper**: `create_scraper(platform_name)` - Creates scraper instance
5. **Extract Products**: `extract_products()` - Extracts product data
6. **Inspect Data** (Optional): `inspect_extracted_data()` - View extracted data and stats
7. **Validate**: Run validation tools (`get_selector_performance_tool()`, etc.)
8. **Save to DB**: `save_to_DB()` - Save if quality passes
9. **Export & Summary**: Export analysis and provide final summary

## Key Differences from Original Agent

- **Two-step extraction**: Uses `create_scraper()` + `extract_products()` instead of combined `scrape()`
- **Matches mcp_server.py pattern**: Exact same tool sequence and behavior
- **Inspects data**: Can inspect extracted data before validation
- **Better error handling**: Clear error messages matching MCP server

## Usage

```python
from AgentModule.langgraph_agent import run_autonomous_scraping_agent

result = run_autonomous_scraping_agent(
    url="https://www.flipkart.com/search?q=phone+case",
    platform_name="flipkart",
    max_iterations=30,
    quality_threshold=0.7
)
```

## Available Tools (Same as mcp_server.py)

- `get_html(url)`: Fetch and analyze HTML
- `readsummary(field)`: Read summary data
- `readHTML(start_line, end_line)`: Read HTML lines
- `get_available_fields()`: List available fields
- `set_selector(field, selector_type, selectors)`: Configure selectors
- `create_scraper(platform_name)`: Create scraper instance
- `extract_products()`: Extract product data
- `inspect_extracted_data(field, show_na_only, limit, sample_mode)`: Inspect data
- `get_selector_performance_tool()`: Analyze performance
- `validate_price_selectors_tool()`: Validate prices
- `validate_rating_selectors_tool()`: Validate ratings
- `validate_review_selectors_tool()`: Validate reviews
- `validate_name_selectors_tool()`: Validate names
- `get_selector_validation_report_tool()`: Get validation report
- `get_selector_improvement_suggestions_tool()`: Get improvement suggestions
- `get_comprehensive_selector_analysis_tool()`: Complete analysis
- `export_selector_analysis_to_json_tool(filename)`: Export to JSON
- `print_selector_validation_summary_tool()`: Print summary
- `save_to_DB()`: Save to database

## Global State

The agent uses the same global state as `mcp_server.py`:
- `html_content`: Fetched HTML content
- `summary`: HTML analysis summary
- `selector_template`: Configured selectors
- `GenericPlatformScraperObj`: Scraper instance

All tools access these globals from `AgentModule.app` module.


