# Web Scraping Bot MCP Server

This is a FastMCP server that provides web scraping tools for LLM applications. It converts all our scraping functionality into MCP-compatible tools.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install fastmcp
```

### 2. Run the MCP Server

#### Option A: Standard stdio transport (recommended for LLM integration)
```bash
cd AgentModule
python mcp_server.py
```

#### Option B: HTTP transport (for web-based clients)
Modify the last line in `mcp_server.py`:
```python
# Change this line:
mcp.run()

# To this:
mcp.run(transport="http", host="0.0.0.0", port=8000)
```

Then run:
```bash
python mcp_server.py
```
The server will be available at `http://localhost:8000/mcp/`

### 3. Test the Server
```bash
python test_mcp_client.py
```

## 🛠️ Available Tools

The MCP server provides the following tools:

### Core HTML and Analysis Tools
- **`get_html(url)`** - Fetch and analyze HTML content from URL
- **`readsummary(field)`** - Read analysis summary data for specific field
- **`readHTML(start_line, end_line)`** - Read HTML content by line numbers

### Selector Configuration Tools
- **`get_available_fields()`** - Get list of available selector fields
- **`set_selector(field, type, selectors)`** - Set selector configuration
- **`create_scraper(platform_name)`** - Create scraper instance

### Data Extraction Tools
- **`extract_products()`** - Extract product data using configured selectors

### Analysis and Validation Tools
- **`get_selector_performance()`** - Analyze selector performance
- **`validate_price_selectors()`** - Validate price selector performance
- **`validate_rating_selectors()`** - Validate rating selector performance
- **`validate_review_selectors()`** - Validate review selector performance
- **`validate_name_selectors()`** - Validate name selector performance
- **`get_selector_validation_report()`** - Get comprehensive validation report
- **`get_selector_improvement_suggestions()`** - Get improvement suggestions
- **`get_comprehensive_selector_analysis()`** - Get complete analysis

### Export and Save Tools
- **`export_selector_analysis_to_json(filename)`** - Export analysis to JSON
- **`save_to_database()`** - Save data to Supabase database

### Utility Tools
- **`get_current_state()`** - Get current state of all global variables
- **`reset_state()`** - Reset all global variables to initial state

## 🔧 Usage Examples

### Basic Workflow
```python
import asyncio
from fastmcp import Client

async def scrape_website():
    client = Client("stdio")  # or "http://localhost:8000/mcp"
    
    async with client:
        # 1. Fetch HTML
        await client.call_tool("get_html", {"url": "https://example.com"})
        
        # 2. Set selectors
        await client.call_tool("set_selector", {
            "field": "name",
            "selector_type": "css", 
            "selectors": ["h1.title"]
        })
        
        # 3. Create scraper
        await client.call_tool("create_scraper", {"platform_name": "example"})
        
        # 4. Extract data
        result = await client.call_tool("extract_products", {})
        
        # 5. Analyze performance
        analysis = await client.call_tool("get_selector_performance", {})
        
        print(f"Extracted {result['product_count']} products")

asyncio.run(scrape_website())
```

## 🌐 Integration with LLMs

### Claude Desktop Integration
Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "web-scraping-bot": {
      "command": "python",
      "args": ["/path/to/AgentModule/mcp_server.py"]
    }
  }
}
```

### OpenAI GPT Integration
Use the HTTP transport and connect via the MCP protocol.

## 📊 Global State Management

The server maintains global state across tool calls:
- **`html_content`** - Current HTML content
- **`summary`** - Analysis summary data
- **`selector_template`** - Current selector configuration
- **`GenericPlatformScraperObj`** - Current scraper instance

## 🔍 Error Handling

All tools return structured responses:
```python
{
    "status": "success" | "error",
    "data": {...},  # or "error": "error message"
    "message": "Success message"
}
```

## 🚨 Environment Variables

For database functionality, set:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase API key
- `SUPABASE_TABLE_NAME` - Database table name (optional, defaults to 'scraped_products')

## 🧪 Testing

Run the test client to verify server functionality:
```bash
python test_mcp_client.py
```

## 📝 Notes

- The server uses stdio transport by default for LLM integration
- All tools maintain state across calls
- Error messages are designed to help LLMs understand and fix issues
- The server is production-ready with comprehensive error handling
