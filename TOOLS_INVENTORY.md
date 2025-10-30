# 🛠️ COMPLETE TOOLS INVENTORY - Missile Project

## 📋 ALL AVAILABLE TOOLS

### 🌐 HTML Fetching & Analysis Tools
1. **`get_html(url: str)`**
   - Fetches HTML content from URL using Crawl4AI
   - Analyzes HTML structure and creates summary
   - Updates global `html_content` and `summary` variables
   - Location: `AgentModule/app.py`, `AgentModule/mcp_server.py`

2. **`readsummary(field: Optional[str])`**
   - Reads HTML analysis summary data
   - Returns specific field or all available fields
   - Fields: 'repeats', 'field_hint_map', 'text_patterns', 'confidence_summary', etc.
   - Location: `AgentModule/app.py`, `AgentModule/mcp_server.py`

3. **`readHTML(start_line: int, end_line: int)`**
   - Reads specific lines of HTML content
   - Useful for detailed DOM structure analysis
   - Location: `AgentModule/app.py`, `AgentModule/mcp_server.py`

### 🎯 Selector Configuration Tools
4. **`get_available_fields()`**
   - Lists all available fields for selector configuration
   - Returns field descriptions and usage examples
   - Location: `AgentModule/app.py`, `AgentModule/mcp_server.py`

5. **`set_selector(field: str, selector_type: str, selectors: List[str])`**
   - Configures CSS/XPath selectors for a specific field
   - Updates global `selector_template`
   - Fields: product_container, name, current_price, original_price, rating, reviews, discount, offers
   - Location: `AgentModule/app.py`, `AgentModule/mcp_server.py`

### 🔧 Scraper Creation & Data Extraction Tools
6. **`create_scraper(platform_name: str)`** ⭐ KEY TOOL
   - Creates GenericPlatformScraper instance
   - Stores in global `GenericPlatformScraperObj`
   - MUST be called before `extract_products()`
   - Location: `AgentModule/mcp_server.py` (reference), `AgentModule/langgraph_agent.py` (helper)

7. **`extract_products()`** ⭐ KEY TOOL
   - Extracts product data using configured scraper
   - Uses global `GenericPlatformScraperObj`
   - MUST be called after `create_scraper()`
   - Returns products JSON with product_count
   - Location: `AgentModule/mcp_server.py` (reference), `AgentModule/langgraph_agent.py` (helper)

### 🔍 Data Inspection Tools
8. **`inspect_extracted_data(field, show_na_only, limit, sample_mode)`**
   - Inspects actual extracted product data
   - Shows statistics, N/A rates, problem fields
   - Can filter by field, show N/A only, or sample mode
   - Location: `AgentModule/mcp_server.py`, `AgentModule/langgraph_agent.py` (helper)

### 📊 Validation & Analysis Tools
9. **`get_selector_performance_tool()`** / **`get_selector_performance()`**
   - Analyzes selector performance and success rates
   - Shows field-by-field extraction statistics
   - Returns overall success rate
   - Location: `AgentModule/app.py` (wrapper), `SelectorToDB/data_analysis.py` (core)

10. **`validate_price_selectors_tool()`** / **`validate_price_selectors()`**
    - Validates price selector performance
    - Checks price format, range, consistency
    - Location: `AgentModule/app.py` (wrapper), `SelectorToDB/data_analysis.py` (core)

11. **`validate_rating_selectors_tool()`** / **`validate_rating_selectors()`**
    - Validates rating selector performance
    - Checks rating range (1-5), format
    - Location: `AgentModule/app.py` (wrapper), `SelectorToDB/data_analysis.py` (core)

12. **`validate_review_selectors_tool()`** / **`validate_review_selectors()`**
    - Validates review count selector performance
    - Checks review count format, consistency
    - Location: `AgentModule/app.py` (wrapper), `SelectorToDB/data_analysis.py` (core)

13. **`validate_name_selectors_tool()`** / **`validate_name_selectors()`**
    - Validates product name selector performance
    - Checks name length, uniqueness, format
    - Location: `AgentModule/app.py` (wrapper), `SelectorToDB/data_analysis.py` (core)

14. **`get_selector_validation_report_tool()`** / **`get_selector_validation_report()`**
    - Comprehensive validation report for all selectors
    - Overall health score and recommendations
    - Location: `AgentModule/app.py` (wrapper), `SelectorToDB/data_analysis.py` (core)

15. **`get_selector_improvement_suggestions_tool()`** / **`get_selector_improvement_suggestions()`**
    - Provides suggestions for improving selector performance
    - Actionable recommendations based on analysis
    - Location: `AgentModule/app.py` (wrapper), `SelectorToDB/data_analysis.py` (core)

16. **`get_comprehensive_selector_analysis_tool()`** / **`get_comprehensive_selector_analysis()`**
    - Complete analysis of selector quality and data extraction
    - Combines all validation metrics
    - Location: `AgentModule/app.py` (wrapper), `SelectorToDB/data_analysis.py` (core)

### 💾 Export & Summary Tools
17. **`export_selector_analysis_to_json_tool(filename)`** / **`export_selector_analysis_to_json(filename)`**
    - Exports analysis results to JSON file
    - Location: `AgentModule/app.py` (wrapper), `SelectorToDB/data_analysis.py` (core)

18. **`print_selector_validation_summary_tool()`** / **`print_selector_validation_summary()`**
    - Prints validation summary to console
    - Location: `AgentModule/app.py` (wrapper), `SelectorToDB/data_analysis.py` (core)

### 💾 Database Tools
19. **`save_to_DB()`** / **`save_to_database()`**
    - Saves validated product data to Supabase database
    - Only saves if data quality is good
    - Location: `AgentModule/app.py`, `AgentModule/mcp_server.py`

### 🔄 State Management Tools (MCP Server Only)
20. **`get_current_state()`**
    - Gets current global state (HTML, summary, selectors, scraper status)
    - Location: `AgentModule/mcp_server.py`

21. **`reset_state()`**
    - Resets all global variables to initial state
    - Location: `AgentModule/mcp_server.py`

## 📝 TOOL USAGE PATTERN (Following mcp_server.py)

**CORRECT SEQUENCE:**
1. `get_html(url)` → Fetch and analyze HTML
2. `readsummary()` → Understand structure
3. `readHTML()` → Analyze specific sections (optional)
4. `get_available_fields()` → See available fields (optional)
5. `set_selector(field, type, selectors)` → Configure all selectors
6. **`create_scraper(platform_name)`** → Create scraper instance ⚠️ REQUIRED
7. **`extract_products()`** → Extract data ⚠️ REQUIRED
8. `inspect_extracted_data()` → Inspect data (optional but recommended)
9. `get_selector_performance_tool()` → Check performance
10. `validate_*_selectors_tool()` → Validate specific fields
11. `get_selector_validation_report_tool()` → Overall health
12. `save_to_DB()` → Save if quality passes

**⚠️ CRITICAL:** Steps 6 and 7 MUST be in order and both called before validation!


