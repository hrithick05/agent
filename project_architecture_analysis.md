# CrawlBot Project Architecture Analysis

## Project Overview
This is a comprehensive web scraping and data analysis system with three main modules working together to provide intelligent HTML analysis, flexible scraping capabilities, and data validation.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CrawlBot System                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │  summaryModulle │    │  SelectorToDB   │    │ AgentModule  │ │
│  │                 │    │                 │    │              │ │
│  │ • HTML Analysis │    │ • Generic       │    │ • AI Agent   │ │
│  │ • Summarization │    │   Scraping      │    │ • Tool       │ │
│  │ • Pattern       │    │ • Data Analysis │    │   Integration│ │
│  │   Detection     │    │ • Validation    │    │ • Google     │ │
│  │ • Field Hints   │    │ • Supabase      │    │   GenAI      │ │
│  │                 │    │   Integration   │    │              │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           │                       │                       │     │
│           └───────────────────────┼───────────────────────┘     │
│                                   │                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                Data Flow & Integration                      │ │
│  │                                                             │ │
│  │  HTML Fetch → Analysis → Selector Config → Scraping → DB   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Module Analysis

### 1. summaryModulle/ - HTML Analysis & Intelligence

#### Core Components:
- **fetchHTML.py**: HTML fetching using Crawl4AI
- **main.py**: Advanced HTML summarization and analysis

#### Key Features:
```python
# HTML Analysis Capabilities
- DOM Structure Analysis (tags, classes, IDs)
- Repeated Pattern Detection
- Field Hint Generation (title, price, image, link, rating)
- Text Pattern Recognition (currency, ratings, emails, phones)
- Form Analysis with Security Redaction
- JavaScript-heavy Site Detection
- XPath Generation for Long Text Nodes
- Confidence Scoring
```

#### HTMLSummarizer Class:
```python
class HTMLSummarizer:
    def __init__(self, html_text, source_path=None, base_url=None)
    def summarize(self, top_n=20) -> Dict[str, Any]
    def _summarize_lxml(self, top_n)  # Advanced analysis with lxml
    def _summarize_bs4(self, top_n)   # Fallback with BeautifulSoup
```

#### Analysis Output Structure:
```json
{
  "total_nodes": 1234,
  "top_tags": [["div", 456], ["span", 234]],
  "repeats": {
    "top_repeated": [
      {
        "signature": {"tag": "div", "classes": ["product"], "child_count": 5},
        "count": 20,
        "sample_nodes": ["<div>...</div>"],
        "suggested_css": "div.product"
      }
    ]
  },
  "field_hint_map": {
    "title": [".//h1/text()", ".//h2//a//span/text()"],
    "price": [".//span[contains(@class,'price')]/text()"],
    "rating": [".//span[contains(@class,'rating')]/text()"]
  },
  "confidence_summary": {
    "js_score": 0.15,
    "is_likely_js_heavy": true
  }
}
```

### 2. SelectorToDB/ - Generic Scraping & Data Management

#### Core Components:
- **generic_scraper.py**: Universal scraper with flexible selectors
- **data_analysis.py**: Selector validation and performance analysis
- **config_converter.py**: Configuration management and conversion
- **main.py**: Legacy universal scraper (site-specific)
- **app.py**: Application wrapper with Supabase integration

#### GenericPlatformScraper Class:
```python
class GenericPlatformScraper:
    def __init__(self, html_content, selector_config, site_name, url=None)
    def scrape(self) -> List[Dict]
    def save_to_csv(self, filename=None) -> str
    def save_to_json(self, filename=None) -> str
    def save_to_supabase(self, supabase_url, supabase_key, table_name) -> Dict
```

#### Selector Configuration Format:
```python
selector_config = {
    'product_container': {
        'type': 'css',
        'selectors': ['div[data-component-type="s-search-result"]']
    },
    'name': {
        'type': 'css',
        'selectors': ['h2.a-size-medium span', 'h2.a-size-medium'],
        'attribute': 'title'  # Optional attribute extraction
    },
    'current_price': {
        'type': 'css',
        'selectors': ['span.a-price-whole'],
        'regex': r'₹([\d,]+)'  # Optional regex cleaning
    }
}
```

#### Data Analysis Features:
```python
# Selector Performance Analysis
- Success rate calculation per field
- Data quality validation
- Improvement suggestions
- Comprehensive reporting

# Validation Functions
- validate_price_selectors()
- validate_rating_selectors()
- validate_name_selectors()
- get_selector_performance()
- get_comprehensive_selector_analysis()
```

### 3. AgentModule/ - AI Agent Integration

#### Purpose:
- Integrates with Google GenAI
- Provides tool-based interface for scraping operations
- Acts as intelligent orchestrator

#### Planned Tools:
```python
# Tool 1: Summary Reading
def readsummary(field_name: str) -> str

# Tool 2: HTML Content Access
def readhtml(start_index: int, end_index: int) -> str

# Tool 3: Scraping Execution
def scrape(url: str, selector: Dict) -> GenericPlatformScraper

# Tool 4-N: Data Analysis Tools
# (All functions from data_analysis.py)

# Tool N+1: Database Saving
def save_to_supabase(scraper_object)
```

## Data Flow Architecture

### 1. HTML Fetching & Analysis Pipeline
```
URL → fetchHTML.py → HTML Content → HTMLSummarizer → Analysis JSON
```

### 2. Scraping Pipeline
```
HTML Content + Selector Config → GenericPlatformScraper → Products List
```

### 3. Data Validation Pipeline
```
Products List → SelectorAnalyzer → Performance Report → Improvement Suggestions
```

### 4. Storage Pipeline
```
Products List → CSV/JSON/Supabase → Persistent Storage
```

## Integration Points

### summaryModulle ↔ SelectorToDB
```python
# HTML analysis provides selector hints
from summaryModulle.fetchHTML import fetch_html_sync
from summaryModulle.main import analyze_html

# Analysis results inform selector configuration
html_content = fetch_html_sync(url)
analysis = analyze_html(html_content)
# Use analysis['field_hint_map'] to build selectors
```

### SelectorToDB ↔ AgentModule
```python
# Agent uses scraper and analysis tools
from SelectorToDB.generic_scraper import GenericPlatformScraper
from SelectorToDB.data_analysis import get_selector_performance

# Agent orchestrates the entire workflow
scraper = GenericPlatformScraper(html_content, selectors, site_name)
products = scraper.scrape()
performance = get_selector_performance(scraper)
```

## Key Design Patterns

### 1. Strategy Pattern
- Multiple selector types (CSS, XPath, Regex)
- Multiple parsers (lxml, BeautifulSoup)
- Multiple output formats (CSV, JSON, Supabase)

### 2. Template Method Pattern
- GenericPlatformScraper provides template
- Site-specific configurations customize behavior
- Consistent output format regardless of input

### 3. Observer Pattern
- Logging system tracks scraping progress
- Analysis functions observe scraper state
- Performance metrics collected automatically

### 4. Factory Pattern
- Configuration converters create selector configs
- Multiple scraper instances for different sites
- Dynamic selector generation from analysis

## Strengths of the Architecture

1. **Modularity**: Clear separation of concerns
2. **Flexibility**: Universal scraper works with any site
3. **Intelligence**: HTML analysis provides smart selector hints
4. **Validation**: Comprehensive data quality checking
5. **Scalability**: Easy to add new sites and features
6. **Integration**: Seamless database and AI agent integration

## Usage Examples

### Basic Scraping Workflow
```python
# 1. Fetch and analyze HTML
html_content = fetch_html_sync("https://example.com")
analysis = analyze_html(html_content)

# 2. Create selectors based on analysis
selectors = create_selectors_from_analysis(analysis)

# 3. Scrape data
scraper = GenericPlatformScraper(html_content, selectors, "example")
products = scraper.scrape()

# 4. Validate and analyze
performance = get_selector_performance(scraper)
print_selector_validation_summary(scraper)

# 5. Save to database
scraper.save_to_supabase(url, key, "products")
```

### Advanced Analysis Workflow
```python
# Comprehensive analysis
analysis = get_comprehensive_selector_analysis(scraper)
suggestions = get_selector_improvement_suggestions(scraper)
export_selector_analysis_to_json(scraper, "analysis.json")
```

This architecture provides a robust, intelligent, and scalable solution for web scraping with built-in analysis, validation, and integration capabilities.
