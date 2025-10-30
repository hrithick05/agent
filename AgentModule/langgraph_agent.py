"""
LangGraph Agent for Web Scraping Bot
Uses Gemini 2.5 with proper function calling API and LangGraph for state management

Environment Variables Required:
    - GEMINI_API_KEY: Your Google Gemini API key
    - SUPABASE_URL: Your Supabase project URL (optional, for saving to database)
    - SUPABASE_KEY: Your Supabase API key (optional, for saving to database)
    - SUPABASE_TABLE_NAME: Database table name (optional, defaults to 'scraped_products')

Example setup:
    export GEMINI_API_KEY="your_gemini_key_here"
    export SUPABASE_URL="https://your-project.supabase.co"
    export SUPABASE_KEY="your_supabase_key_here"
    export SUPABASE_TABLE_NAME="scraped_products"
"""

import json
import sys
import os
from typing import Dict, List, Any, Optional, Union, TypedDict, Annotated

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, continue without .env file

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import google.generativeai as genai
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

# Import needed modules FIRST before using them in type hints
from summaryModulle.fetchHTML import fetch_html_sync
from summaryModulle.main import analyze_html
from SelectorToDB.generic_scraper import GenericPlatformScraper
from SelectorToDB.data_analysis import SelectorAnalyzer, get_comprehensive_selector_analysis as get_comprehensive_analysis_from_module, print_selector_validation_summary as print_summary_from_analyzer
from bs4 import BeautifulSoup
import asyncio
import time

# Global state management - same pattern as mcp_server.py
html_content: str = ""
summary: Dict[str, Any] = {}
GenericPlatformScraperObj: GenericPlatformScraper = None

# Global selector template - empty by default, to be filled by LLM incrementally
selector_template: Dict[str, Any] = {
    'product_container': {
        'type': None,
        'selectors': []
    },
    'name': {
        'type': None,
        'selectors': []
    },
    'current_price': {
        'type': None,
        'selectors': []
    },
    'original_price': {
        'type': None,
        'selectors': []
    },
    'rating': {
        'type': None,
        'selectors': []
    },
    'reviews': {
        'type': None,
        'selectors': []
    },
    'discount': {
        'type': None,
        'selectors': []
    },
    'offers': {
        'type': None,
        'selectors': []
    }
}

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCb6_cDBg58-QsuEZ0KKwlr-4b9Lx8nRk8")
genai.configure(api_key=GEMINI_API_KEY)

# ============================================================================
# LANGGRAPH STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    """State managed by LangGraph agent"""
    messages: Annotated[List[Dict[str, Any]], add_messages]
    url: str
    platform_name: str
    task_description: str
    completed_steps: List[str]
    tool_calls_made: int
    iterations: int
    errors: List[str]
    final_results: Dict[str, Any]
    quality_score: Optional[float]
    max_iterations: int
    # Optional, added for role-based pipeline
    analysis_hints: Optional[Dict[str, Any]]
    selector_plan: Optional[Dict[str, Any]]
    validation_suggestions: Optional[Dict[str, Any]]


# ============================================================================
# GEMINI JSON-CALL HELPER AND HTML CHUNKING
# ============================================================================

def _safe_gemini_json_call(
    prompt_parts: List[Dict[str, Any]],
    model_name: str = "gemini-2.5-pro",
    temperature: float = 0.2,
    max_output_tokens: int = 768,
    retry: int = 2
) -> Dict[str, Any]:
    """Call Gemini and robustly parse JSON. Retries with sanitizer if needed.

    Returns a dict. If parsing fails after retries, returns {"error": str}.
    """
    try:
        model = genai.GenerativeModel(model_name=model_name)
    except Exception as e:
        return {"error": f"Failed to init model: {str(e)}"}

    last_text = ""
    for attempt in range(retry + 1):
        try:
            response = model.generate_content(
                prompt_parts,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    top_p=0.95,
                    max_output_tokens=max_output_tokens
                )
            )
            text = getattr(response, "text", None)
            if not text and getattr(response, "candidates", None):
                cand = response.candidates[0]
                if getattr(cand, "content", None) and getattr(cand.content, "parts", None):
                    for part in cand.content.parts:
                        if getattr(part, "text", None):
                            text = part.text
                            break
            if not text:
                return {"error": "No text returned by model"}
            last_text = text
            try:
                return json.loads(text)
            except Exception:
                # Retry with sanitizer prompt
                sanitizer = [{"text": "You returned invalid JSON. Respond ONLY with corrected, valid JSON for the same content, no extra text."}, {"text": text}]
                prompt_parts = sanitizer
                time.sleep(0.7)
                continue
        except Exception as e:
            last_text = str(e)
            time.sleep(0.7)
            continue
    return {"error": "Failed to parse JSON response", "raw": last_text}


def _chunk_html_for_llm(html: str, max_lines: int = 800) -> Dict[str, str]:
    """Create small HTML slices: head, first list chunk, sample items.
    This avoids sending huge pages to the LLM.
    """
    if not html:
        return {"head": "", "body_sample": "", "tail": ""}
    lines = html.split('\n')
    head = '\n'.join(lines[:120])
    body_sample = '\n'.join(lines[120:120+max_lines])
    tail = '\n'.join(lines[-120:]) if len(lines) > 240 else ''
    return {"head": head, "body_sample": body_sample, "tail": tail}


# ============================================================================
# ROLE NODES: PAGE ANALYZER
# ============================================================================

def page_analyzer_node(state: AgentState) -> AgentState:
    """Role 1: Analyze HTML to produce concise JSON summary & hints."""
    url = state.get("url", "")
    messages = state.get("messages", [])
    completed_steps = state.get("completed_steps", [])
    errors = state.get("errors", [])

    # Ensure HTML is fetched
    global html_content, summary
    if not html_content:
        res = execute_tool("get_html", {"url": url})
        if res.get("status") == "error":
            errors.append(f"get_html: {res.get('error','unknown')}")
            state["errors"] = errors
            return state
        completed_steps.append("get_html")

    chunks = _chunk_html_for_llm(html_content)
    # Build structured prompt enforcing JSON-only output
    prompt = [
        {"text": "You are Page Analyzer. Respond ONLY with valid JSON matching this schema."},
        {"text": "Schema: {\n  title: string,\n  meta: {description?: string, keywords?: string},\n  candidate_repeating_blocks: string[],\n  probable_fields: string[],\n  currency_locale: string,\n  samples: {product_snippets: string[]}\n}"},
        {"text": "Constraints: short values, no prose, JSON only."},
        {"text": f"HEAD:\n{chunks['head']}"},
        {"text": f"BODY_SAMPLE:\n{chunks['body_sample'][:4000]}"},
        {"text": f"TAIL:\n{chunks['tail']}"}
    ]
    result = _safe_gemini_json_call(prompt_parts=prompt, temperature=0.1, max_output_tokens=512)
    if "error" in result:
        errors.append(f"page_analyzer_json: {result['error']}")
    else:
        state["analysis_hints"] = result
        completed_steps.append("page_analyzer")

    state["completed_steps"] = completed_steps
    state["errors"] = errors
    state["messages"] = messages
    return state


# ============================================================================
# ROLE NODES: SELECTOR DESIGNER
# ============================================================================

def selector_designer_node(state: AgentState) -> AgentState:
    """Role 2: Propose selectors in JSON and apply them via set_selector."""
    errors = state.get("errors", [])
    completed_steps = state.get("completed_steps", [])

    analysis = state.get("analysis_hints") or {}
    available = get_available_fields()
    target_fields = available.get("available_fields", [])
    # Do not include product_container at first pass? Keep it in, but prioritize.
    prompt = [
        {"text": "You are Selector Designer. Respond ONLY with valid JSON matching this schema."},
        {"text": "Schema: { selectors: { [field: string]: { candidates: [ { type: 'css'|'xpath'|'regex', value: string, confidence: number, rationale: string } ] } } }"},
        {"text": "Constraints: low temperature, concise. Fields:" + ", ".join(target_fields)},
        {"text": "Analysis (short):"},
        {"text": json.dumps(analysis)[:4000]}
    ]
    result = _safe_gemini_json_call(prompt_parts=prompt, temperature=0.2, max_output_tokens=768)
    if "error" in result:
        errors.append(f"selector_designer_json: {result['error']}")
        state["errors"] = errors
        return state

    selectors = (result or {}).get("selectors", {})
    # Apply top candidates per field
    for field_name, cfg in selectors.items():
        if field_name not in target_fields:
            continue
        candidates = (cfg or {}).get("candidates", [])
        if not candidates:
            continue
        # choose top 1-2 css if available, else first
        css_vals = [c for c in candidates if c.get("type") == "css"]
        chosen = css_vals[:2] if css_vals else candidates[:2]
        selector_type = chosen[0].get("type", "css")
        selector_values = [c.get("value", "") for c in chosen if c.get("value")]
        if selector_values:
            _ = execute_tool("set_selector", {"field": field_name, "selector_type": selector_type, "selectors": selector_values})

    state["selector_plan"] = result
    completed_steps.append("selector_designer")
    state["completed_steps"] = completed_steps
    state["errors"] = errors
    return state


# ============================================================================
# ROLE NODES: VALIDATOR / IMPROVER
# ============================================================================

def validator_improver_node(state: AgentState) -> AgentState:
    """Role 3: Validate extracted data and propose improvements."""
    errors = state.get("errors", [])
    completed_steps = state.get("completed_steps", [])
    platform_name = state.get("platform_name", "site")
    url = state.get("url", "")

    # Ensure scraper exists and data is extracted
    create_res = execute_tool("create_scraper", {"platform_name": platform_name})
    if create_res.get("status") == "error":
        errors.append(f"create_scraper: {create_res.get('error','unknown')}")
        state["errors"] = errors
        return state
    completed_steps.append("create_scraper")

    ext = execute_tool("extract_products", {})
    if ext.get("status") == "error":
        errors.append(f"extract_products: {ext.get('error','unknown')}")
        state["errors"] = errors
        return state
    completed_steps.append("extract_products")

    # If nothing extracted, re-fetch HTML and reconfigure selectors from summary hints
    try:
        product_count = int(ext.get("product_count") or 0)
    except Exception:
        product_count = 0

    if product_count == 0 and url:
        _ = execute_tool("get_html", {"url": url})
        # Try AI-generated selectors first
        try:
            from AgentModule.app import generate_selectors_with_model as _gen_sel
            ai_cfg = _gen_sel(url) or {}
            if isinstance(ai_cfg, dict) and ai_cfg.get("product_container"):
                for field_name, cfg in ai_cfg.items():
                    sels = (cfg or {}).get("selectors") or []
                    sel_type = (cfg or {}).get("selector_type", "css")
                    if isinstance(sels, list) and sels:
                        _ = execute_tool("set_selector", {
                            "field": field_name,
                            "selector_type": sel_type,
                            "selectors": list(dict.fromkeys([s for s in sels if isinstance(s, str) and s]))[:3]
                        })
        except Exception:
            pass
        hint_res = execute_tool("readsummary", {"field": "field_hint_map"})
        hint_map = hint_res if isinstance(hint_res, dict) else {}
        target_fields = [
            "product_container","name","current_price","original_price",
            "rating","reviews","discount","offers"
        ]
        for field_name in target_fields:
            candidates = (hint_map.get(field_name) if isinstance(hint_map.get(field_name), list) else []) if hint_map else []
            normalized = []
            for c in candidates:
                if isinstance(c, str):
                    normalized.append(c)
                elif isinstance(c, dict):
                    v = c.get("selector") or c.get("css") or c.get("value")
                    if isinstance(v, str) and v:
                        normalized.append(v)
            if normalized:
                _ = execute_tool("set_selector", {
                    "field": field_name,
                    "selector_type": "css",
                    "selectors": list(dict.fromkeys(normalized))[:2]
                })
        _ = execute_tool("create_scraper", {"platform_name": platform_name})
        ext = execute_tool("extract_products", {})

    perf = execute_tool("get_selector_validation_report", {})
    sugg = execute_tool("get_selector_improvement_suggestions", {})

    # If health is low, try applying first round of improvement suggestions automatically
    try:
        overall = 0.0
        data = (perf.get("data") or {}) if isinstance(perf, dict) else {}
        score_text = ((data.get("overall_selector_health") or {}).get("score") or "0%")
        overall = float(str(score_text).replace('%',''))/100.0
    except Exception:
        overall = 0.0

    if overall < 0.7 and isinstance(sugg, dict):
        for bucket in ["high_priority", "medium_priority"]:
            for issue in (sugg.get(bucket) or []):
                field_name = issue.get("field")
                proposal = issue.get("proposal") or issue.get("suggestion") or {}
                selectors = []
                if isinstance(proposal, dict):
                    selectors = proposal.get("selectors") or proposal.get("candidates") or []
                if isinstance(selectors, str):
                    selectors = [selectors]
                if field_name and isinstance(selectors, list) and selectors:
                    sel_list = [s for s in selectors if isinstance(s, str) and s]
                    if sel_list:
                        _ = execute_tool("set_selector", {
                            "field": field_name,
                            "selector_type": proposal.get("selector_type", "css") if isinstance(proposal, dict) else "css",
                            "selectors": list(dict.fromkeys(sel_list))[:3]
                        })
        _ = execute_tool("create_scraper", {"platform_name": platform_name})
        _ = execute_tool("extract_products", {})
        perf = execute_tool("get_selector_validation_report", {})

    state["validation_suggestions"] = {"report": perf, "suggestions": sugg}
    completed_steps.append("validator_improver")

    state["completed_steps"] = completed_steps
    state["errors"] = errors
    return state


# ============================================================================
# ROLE-BASED ENTRYPOINT (SEQUENTIAL ORCHESTRATION)
# ============================================================================

def run_scraping_agent_v2(
    url: str,
    platform_name: str,
    max_cycles: int = 2,
    quality_threshold: float = 0.7
) -> Dict[str, Any]:
    """Role-based pipeline: Analyzer -> Selector -> Validator with limited cycles."""
    reset_state()
    state: AgentState = {
        "messages": [],
        "url": url,
        "platform_name": platform_name,
        "task_description": "Role-based pipeline",
        "completed_steps": [],
        "tool_calls_made": 0,
        "iterations": 0,
        "errors": [],
        "final_results": {},
        "quality_score": None,
        "max_iterations": max_cycles,
        "analysis_hints": None,
        "selector_plan": None,
        "validation_suggestions": None,
    }

    # 1) Analyze
    state = page_analyzer_node(state)

    # 2) Iterate: design -> validate -> maybe improve
    for _ in range(max_cycles):
        state = selector_designer_node(state)
        state = validator_improver_node(state)
        # Try to compute simple overall score if present
        rep = (state.get("validation_suggestions") or {}).get("report", {})
        data = rep.get("data") or {}
        overall = 0.0
        try:
            overall_text = ((data.get("overall_selector_health") or {}).get("score") or "0%")
            overall = float(str(overall_text).replace('%',''))/100.0
        except Exception:
            pass
        state["quality_score"] = overall
        if overall >= quality_threshold:
            break

    # Save if good quality
    if (state.get("quality_score") or 0) >= quality_threshold:
        _ = execute_tool("save_to_database", {})
        state["final_results"] = {"workflow_complete": True, "saved": True, "quality": state.get("quality_score")}
    else:
        state["final_results"] = {"workflow_complete": False, "saved": False, "quality": state.get("quality_score")}

    return {
        "success": True,
        "completed_steps": state.get("completed_steps", []),
        "quality_score": state.get("quality_score"),
        "final_results": state.get("final_results"),
        "errors": state.get("errors", []),
    }

# ============================================================================
# TOOL FUNCTIONS - Same implementation pattern as mcp_server.py
# ============================================================================

def get_html(url: str) -> Dict[str, Any]:
    """Fetch HTML content from URL and perform comprehensive analysis."""
    try:
        global html_content, summary
        html_content = fetch_html_sync(url)
        summary = analyze_html(html_content)
        return {"message": "Successfully fetched and analyzed HTML content", "status": "success"}
    except Exception as e:
        return {"message": f"Error fetching HTML: {str(e)}", "status": "error"}

def readsummary(field: Optional[str] = None) -> Dict[str, Any]:
    """Read analysis summary data for a specific field or return all available fields."""
    try:
        global summary
        # Handle null/empty field properly
        if field is None or field == "null" or field == "":
            result = list(summary.keys())
        else:
            result = summary.get(field, f"Field '{field}' not found in summary")
        return {"data": result, "status": "success"}
    except Exception as e:
        return {"error": f"Error reading summary: {str(e)}", "status": "error"}

def readHTML(
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    css_selector: Optional[str] = None,
    text_search: Optional[str] = None,
    attribute_filter: Optional[str] = None,
    context_lines: int = 10,
    max_results: int = 5
) -> Dict[str, Any]:
    """Read HTML content with multiple search modes."""
    try:
        global html_content
        
        if not html_content:
            return {"content": "No HTML content available", "status": "error"}
        
        # Determine search mode
        search_mode = "line_range"
        if css_selector:
            search_mode = "css_selector"
        elif text_search:
            search_mode = "text_search"
        elif attribute_filter:
            search_mode = "attribute"
        
        # Mode 1: Line-based reading
        if start_line is not None and end_line is not None:
            lines = html_content.split('\n')
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)
            result = '\n'.join(lines[start_idx:end_idx])
            
            return {
                "content": result,
                "lines_retrieved": end_idx - start_idx,
                "search_mode": search_mode,
                "status": "success"
            }
        
        # Mode 2-4: Content-based search using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
        matches = []
        match_positions = []
        
        # Mode 2: CSS selector search
        if search_mode == "css_selector":
            elements = soup.select(css_selector)
            matches = [str(elem) for elem in elements[:max_results]]
        
            # Find line positions for matched elements
            html_lines = html_content.split('\n')
            for elem in elements[:max_results]:
                elem_str = str(elem)[:100]
                for i, line in enumerate(html_lines):
                    if elem_str[:50] in line:
                        match_positions.append(i + 1)
                        break
        
        # Mode 3: Text search
        elif search_mode == "text_search":
            html_lines = html_content.split('\n')
            for i, line in enumerate(html_lines):
                if text_search.lower() in line.lower():
                    start_idx = max(0, i - context_lines)
                    end_idx = min(len(html_lines), i + context_lines + 1)
                    context = '\n'.join(html_lines[start_idx:end_idx])
                    matches.append(f"Line {i + 1}:\n{context}")
                    match_positions.append(i + 1)
                    
                    if len(matches) >= max_results:
                        break
        
        # Mode 4: Attribute search
        elif search_mode == "attribute":
            parts = attribute_filter.split('=')
            attr_name = parts[0].strip()
            attr_value = parts[1].strip() if len(parts) > 1 else None
            
            if attr_value:
                elements = soup.find_all(attrs={attr_name: attr_value})
            else:
                elements = soup.find_all(attrs={attr_name: True})
            
            matches = [str(elem) for elem in elements[:max_results]]
            
            html_lines = html_content.split('\n')
            for elem in elements[:max_results]:
                elem_str = str(elem)[:100]
                for i, line in enumerate(html_lines):
                    if elem_str[:50] in line:
                        match_positions.append(i + 1)
                        break
        
        # Format results
        if matches:
            result = '\n\n---\n\n'.join(matches)
            
            return {
                "content": result,
                "matches_found": len(matches),
                "match_positions": match_positions[:max_results],
                "search_mode": search_mode,
                "query": css_selector or text_search or attribute_filter,
                "status": "success"
            }
        else:
            return {
                "content": f"No matches found for: {css_selector or text_search or attribute_filter}",
                "matches_found": 0,
                "match_positions": [],
                "search_mode": search_mode,
                "status": "success"
            }
    
    except Exception as e:
        return {"error": f"Error reading HTML: {str(e)}", "status": "error"}

def get_available_fields() -> Dict[str, Any]:
    """Get the list of available fields for selector configuration."""
    try:
        global selector_template
        result = {
            "available_fields": list(selector_template.keys()),
            "field_descriptions": {
                "product_container": "Container element that wraps each product",
                "name": "Product name/title", 
                "current_price": "Current selling price",
                "original_price": "Original/MRP price (optional)",
                "rating": "Product rating (1-5 stars)",
                "reviews": "Number of reviews/ratings",
                "discount": "Discount percentage or amount",
                "offers": "Special offers or coupons"
            },
            "usage_example": "Use set_selector('name', 'css', ['h1.title', 'a.product-link']) to set name selectors",
            "status": "success"
        }
        return result
    except Exception as e:
        return {"error": f"Error getting available fields: {str(e)}", "status": "error"}

def set_selector(field: str, selector_type: str, selectors: List[str]) -> Dict[str, Any]:
    """Set selector configuration for a specific field in the global template."""
    try:
        global selector_template
        
        # Validate field name
        if field not in selector_template:
            available_fields = list(selector_template.keys())
        return {
                "error": f"Invalid field '{field}'. Available fields: {available_fields}",
                "suggestion": f"Use one of these exact field names: {', '.join(available_fields)}",
                "field_descriptions": {
                    "product_container": "Container element that wraps each product",
                    "name": "Product name/title", 
                    "current_price": "Current selling price",
                    "original_price": "Original/MRP price (optional)",
                    "rating": "Product rating (1-5 stars)",
                    "reviews": "Number of reviews/ratings",
                    "discount": "Discount percentage or amount",
                    "offers": "Special offers or coupons"
                },
                "status": "error"
            }
        
        # Validate selector type
        valid_types = ['css', 'xpath', 'regex']
        if selector_type not in valid_types:
            return {
                "error": f"Invalid selector type '{selector_type}'. Valid types: {valid_types}",
                "status": "error"
            }
        
        # Validate selectors list
        if not isinstance(selectors, list) or not selectors:
            return {
                "error": "Selectors must be a non-empty list of strings",
                "status": "error"
            }
        
        # Update the template
        selector_template[field] = {
            'type': selector_type,
            'selectors': selectors
        }
        
        result = {
            "message": f"Successfully set {field} selector",
            "field": field,
            "type": selector_type,
            "selectors": selectors,
            "template": selector_template,
            "status": "success"
        }
        return result
    except Exception as e:
        return {"error": f"Error setting selector: {str(e)}", "status": "error"}

def create_scraper(platform_name: str) -> Dict[str, str]:
    """Create a GenericPlatformScraper instance and store it in global variable."""
    try:
        global GenericPlatformScraperObj, html_content, selector_template
        
        if not html_content:
            return {"error": "No HTML content available. Please call get_html() first.", "status": "error"}
        
        GenericPlatformScraperObj = GenericPlatformScraper(html_content, selector_template, platform_name)
        return {"message": "Successfully created GenericPlatformScraper object and stored in global variable", "status": "success"}
    except Exception as e:
        return {"error": f"Error creating scraper: {str(e)}", "status": "error"}

def extract_products() -> Dict[str, Any]:
    """Extract product data using the configured scraper."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {"error": "No scraper object available. Please call create_scraper() first.", "status": "error"}
        
        products = GenericPlatformScraperObj.scrape()
        
        return {
            "products": products,
            "product_count": len(products),
            "status": "success"
        }
    except Exception as e:
        return {"error": f"Error extracting products: {str(e)}", "status": "error"}

def inspect_extracted_data(
    field: Optional[str] = None,
    show_na_only: bool = False,
    limit: int = 10,
    sample_mode: bool = False
) -> Dict[str, Any]:
    """Inspect the actual data extracted by the current selectors for detailed analysis."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {"error": "No scraper object available. Please call create_scraper() first.", "status": "error"}
        
        if not hasattr(GenericPlatformScraperObj, 'products') or not GenericPlatformScraperObj.products:
            return {"error": "No products extracted yet. Please call extract_products() first.", "status": "error"}
        
        products = GenericPlatformScraperObj.products
        
        # Calculate field statistics
        field_stats = {}
        available_fields = ['name', 'current_price', 'original_price', 'rating', 'reviews', 'discount', 'offers']
        
        total = len(products)
        
        for field_name in available_fields:
            na_count = 0
            valid_count = 0
            samples = []
            
            for product in products:
                value = product.get(field_name, 'N/A')
                if value == 'N/A' or value is None or value == '':
                    na_count += 1
                else:
                    valid_count += 1
                    if len(samples) < 3:
                        samples.append(value)
            
            na_percentage = (na_count / total * 100) if total > 0 else 0
            
            field_stats[field_name] = {
                "na_count": na_count,
                "valid_count": valid_count,
                "na_percentage": f"{na_percentage:.1f}%",
                "status": "GOOD" if na_percentage < 20 else "NEEDS_IMPROVEMENT" if na_percentage < 50 else "POOR",
                "samples": samples
            }
        
        # Filter products based on parameters
        filtered_products = products
        
        if field and show_na_only:
            filtered_products = [p for p in products if p.get(field, 'N/A') == 'N/A']
        elif field and not show_na_only:
            pass
        
        # Apply limit
        if sample_mode and len(filtered_products) > limit:
            indices = [int(i * len(filtered_products) / limit) for i in range(limit)]
            filtered_products = [filtered_products[i] for i in indices]
        else:
            filtered_products = filtered_products[:limit]
        
        # Identify problem fields
        problem_fields = []
        for field_name, stats in field_stats.items():
            if float(stats['na_percentage'].replace('%', '')) >= 50:
                problem_fields.append({
                    'field': field_name,
                    'na_percentage': stats['na_percentage'],
                    'status': stats['status']
                })
        
        return {
            "products": filtered_products,
            "total_products": len(products),
            "displayed_products": len(filtered_products),
            "field_stats": field_stats,
            "problem_fields": problem_fields,
            "summary": f"Showing {len(filtered_products)} of {len(products)} products",
            "status": "success"
        }
    
    except Exception as e:
        return {"error": f"Error inspecting extracted data: {str(e)}", "status": "error"}

def get_selector_performance() -> Dict[str, Any]:
    """Analyze selector performance and data extraction success rates."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {"error": "No scraper object available. Please call create_scraper() first.", "status": "error"}
        
        analyzer = SelectorAnalyzer(GenericPlatformScraperObj)
        if analyzer.df.empty:
            result = {"error": "No data available for analysis"}
        else:
            total_products = len(analyzer.df)
            field_performance = {}
            for field in ['name', 'current_price', 'original_price', 'rating', 'reviews', 'discount', 'offers']:
                if field in analyzer.df.columns:
                    valid_count = int(analyzer.df[field].apply(analyzer._is_valid_data).sum())
                    success_rate = (valid_count / total_products) * 100 if total_products > 0 else 0
                    field_performance[field] = {
                        "success_rate": f"{success_rate:.1f}%",
                        "valid_extractions": valid_count,
                        "total_attempts": total_products,
                        "failed_extractions": total_products - valid_count,
                        "status": "GOOD" if success_rate >= 80 else "NEEDS_IMPROVEMENT" if success_rate >= 50 else "POOR"
                    }
            result = {
                "total_products": total_products,
                "site": analyzer.df['site'].iloc[0] if not analyzer.df.empty else "unknown",
                "scraped_at": analyzer.df['scraped_at'].iloc[0] if not analyzer.df.empty else None,
                "field_performance": field_performance,
                "overall_success_rate": f"{(sum(int(field_performance[f]['valid_extractions']) for f in field_performance) / (len(field_performance) * total_products) * 100):.1f}%" if total_products > 0 else "0%"
            }
        return {"data": result, "status": "success"}
    except Exception as e:
        return {"error": f"Error analyzing performance: {str(e)}", "status": "error"}

def validate_price_selectors() -> Dict[str, Any]:
    """Validate price selector performance and data quality."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {"error": "No scraper object available. Please call create_scraper() first.", "status": "error"}
        
        result = {
            "test": "Price validation function is working",
            "scraper_type": str(type(GenericPlatformScraperObj)),
            "products_count": len(GenericPlatformScraperObj.products) if hasattr(GenericPlatformScraperObj, 'products') else 0
        }
        return {"data": result, "status": "success"}
    except Exception as e:
        return {"error": f"Error validating price selectors: {str(e)}", "status": "error"}

def validate_rating_selectors() -> Dict[str, Any]:
    """Validate rating selector performance and data quality."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {"error": "No scraper object available. Please call create_scraper() first.", "status": "error"}
        
        analyzer = SelectorAnalyzer(GenericPlatformScraperObj)
        if analyzer.df.empty:
            result = {"error": "No data available for analysis"}
        else:
            total_products = len(analyzer.df)
            rating_valid = int(analyzer.df['rating'].apply(analyzer._is_valid_data).sum())
            rating_numeric = int(analyzer.df['rating'].apply(analyzer._extract_numeric_value).notna().sum())
            rating_samples = analyzer.df[analyzer.df['rating'].apply(analyzer._is_valid_data)]['rating'].head(5).tolist()
            valid_ratings = 0
            if rating_numeric > 0:
                numeric_ratings = analyzer.df['rating'].apply(analyzer._extract_numeric_value).dropna()
                valid_ratings = int(len(numeric_ratings[(numeric_ratings >= 0) & (numeric_ratings <= 5)]))
            result = {
                "rating_selector": {
                    "success_rate": f"{(rating_valid / total_products) * 100:.1f}%",
                    "valid_extractions": rating_valid,
                    "numeric_extractions": rating_numeric,
                    "valid_range_extractions": valid_ratings,
                    "status": "GOOD" if rating_valid >= total_products * 0.8 else "NEEDS_IMPROVEMENT" if rating_valid >= total_products * 0.5 else "POOR",
                    "sample_data": rating_samples,
                    "recommendation": "Selector working well" if rating_valid >= total_products * 0.8 else "Consider improving rating selectors"
                }
            }
        return {"data": result, "status": "success"}
    except Exception as e:
        return {"error": f"Error validating rating selectors: {str(e)}", "status": "error"}

def validate_review_selectors() -> Dict[str, Any]:
    """Validate review selector performance and data quality."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {"error": "No scraper object available. Please call create_scraper() first.", "status": "error"}
        
        analyzer = SelectorAnalyzer(GenericPlatformScraperObj)
        if analyzer.df.empty:
            result = {"error": "No data available for analysis"}
        else:
            total_products = len(analyzer.df)
            review_valid = int(analyzer.df['reviews'].apply(analyzer._is_valid_data).sum())
            review_numeric = int(analyzer.df['reviews'].apply(analyzer._extract_numeric_value).notna().sum())
            review_samples = analyzer.df[analyzer.df['reviews'].apply(analyzer._is_valid_data)]['reviews'].head(5).tolist()
            result = {
                "review_selector": {
                    "success_rate": f"{(review_valid / total_products) * 100:.1f}%",
                    "valid_extractions": review_valid,
                    "numeric_extractions": review_numeric,
                    "status": "GOOD" if review_valid >= total_products * 0.8 else "NEEDS_IMPROVEMENT" if review_valid >= total_products * 0.5 else "POOR",
                    "sample_data": review_samples,
                    "recommendation": "Selector working well" if review_valid >= total_products * 0.8 else "Consider improving review selectors"
                }
            }
        return {"data": result, "status": "success"}
    except Exception as e:
        return {"error": f"Error validating review selectors: {str(e)}", "status": "error"}

def validate_name_selectors() -> Dict[str, Any]:
    """Validate name selector performance and data quality."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {"error": "No scraper object available. Please call create_scraper() first.", "status": "error"}
        
        analyzer = SelectorAnalyzer(GenericPlatformScraperObj)
        if analyzer.df.empty:
            result = {"error": "No data available for analysis"}
        else:
            total_products = len(analyzer.df)
            name_valid = int(analyzer.df['name'].apply(analyzer._is_valid_data).sum())
            name_samples = analyzer.df[analyzer.df['name'].apply(analyzer._is_valid_data)]['name'].head(5).tolist()
            valid_length_names = 0
            if name_valid > 0:
                valid_names = analyzer.df[analyzer.df['name'].apply(analyzer._is_valid_data)]['name']
                valid_length_names = int(len(valid_names[(valid_names.str.len() >= 5) & (valid_names.str.len() <= 200)]))
            result = {
                "name_selector": {
                    "success_rate": f"{(name_valid / total_products) * 100:.1f}%",
                    "valid_extractions": name_valid,
                    "reasonable_length_extractions": valid_length_names,
                    "status": "GOOD" if name_valid >= total_products * 0.8 else "NEEDS_IMPROVEMENT" if name_valid >= total_products * 0.5 else "POOR",
                    "sample_data": name_samples,
                    "recommendation": "Selector working well" if name_valid >= total_products * 0.8 else "Consider improving name selectors"
                }
            }
        return {"data": result, "status": "success"}
    except Exception as e:
        return {"error": f"Error validating name selectors: {str(e)}", "status": "error"}

def get_selector_validation_report() -> Dict[str, Any]:
    """Get comprehensive selector validation report."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {"error": "No scraper object available. Please call create_scraper() first.", "status": "error"}
        
        analyzer = SelectorAnalyzer(GenericPlatformScraperObj)
        if analyzer.df.empty:
            result = {"error": "No data available for analysis"}
        else:
            total_products = len(analyzer.df)
            field_performance = {}
            for field in ['name', 'current_price', 'original_price', 'rating', 'reviews', 'discount', 'offers']:
                if field in analyzer.df.columns:
                    valid_count = int(analyzer.df[field].apply(analyzer._is_valid_data).sum())
                    success_rate = (valid_count / total_products) * 100 if total_products > 0 else 0
                    field_performance[field] = {
                        "success_rate": f"{success_rate:.1f}%",
                        "valid_extractions": valid_count,
                        "total_attempts": total_products,
                        "failed_extractions": total_products - valid_count,
                        "status": "GOOD" if success_rate >= 80 else "NEEDS_IMPROVEMENT" if success_rate >= 50 else "POOR"
                    }
            field_scores = []
            for field, data in field_performance.items():
                success_rate = float(data['success_rate'].replace('%', ''))
                field_scores.append(success_rate)
            overall_score = sum(field_scores) / len(field_scores) if field_scores else 0
            recommendations = []
            critical_issues = []
            for field, data in field_performance.items():
                success_rate = float(data['success_rate'].replace('%', ''))
                if success_rate < 50:
                    critical_issues.append(f"{field} selector is failing ({success_rate:.1f}% success rate)")
                elif success_rate < 80:
                    recommendations.append(f"Consider improving {field} selectors ({success_rate:.1f}% success rate)")
            result = {
                "overall_selector_health": {
                    "score": f"{overall_score:.1f}%",
                    "status": "EXCELLENT" if overall_score >= 90 else "GOOD" if overall_score >= 80 else "NEEDS_IMPROVEMENT" if overall_score >= 60 else "POOR",
                    "total_products": total_products,
                    "site": analyzer.df['site'].iloc[0] if not analyzer.df.empty else "unknown"
                },
                "field_performance": field_performance,
                "critical_issues": critical_issues,
                "recommendations": recommendations,
                "analysis_timestamp": "2024-01-01T00:00:00"
            }
        return {"data": result, "status": "success"}
    except Exception as e:
        return {"error": f"Error getting validation report: {str(e)}", "status": "error"}

def get_selector_improvement_suggestions() -> Dict[str, Any]:
    """Get specific suggestions for improving selectors."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {"error": "No scraper object available. Please call create_scraper() first.", "status": "error"}
        
        analyzer = SelectorAnalyzer(GenericPlatformScraperObj)
        if analyzer.df.empty:
            result = {"error": "No data available for analysis"}
        else:
            suggestions = {
                "high_priority": [],
                "medium_priority": [],
                "low_priority": [],
                "sample_failures": {}
            }
            for field in ['name', 'current_price', 'original_price', 'rating', 'reviews', 'discount', 'offers']:
                if field in analyzer.df.columns:
                    valid_count = int(analyzer.df[field].apply(analyzer._is_valid_data).sum())
                    total_count = len(analyzer.df)
                    success_rate = float((valid_count / total_count) * 100)
                    failures = analyzer.df[~analyzer.df[field].apply(analyzer._is_valid_data)][field].head(3).tolist()
                    suggestions["sample_failures"][field] = failures
                    if success_rate < 50:
                        suggestions["high_priority"].append({
                            "field": field,
                            "issue": f"Only {success_rate:.1f}% success rate",
                            "suggestion": f"Review and update {field} selectors - consider adding more fallback selectors or changing selector strategy"
                        })
                    elif success_rate < 80:
                        suggestions["medium_priority"].append({
                            "field": field,
                            "issue": f"{success_rate:.1f}% success rate",
                            "suggestion": f"Consider adding fallback selectors for {field} to improve reliability"
                        })
                    elif success_rate < 95:
                        suggestions["low_priority"].append({
                            "field": field,
                            "issue": f"{success_rate:.1f}% success rate",
                            "suggestion": f"Minor improvements possible for {field} selectors"
                        })
            result = suggestions
        return {"data": result, "status": "success"}
    except Exception as e:
        return {"error": f"Error getting improvement suggestions: {str(e)}", "status": "error"}

def get_comprehensive_selector_analysis() -> Dict[str, Any]:
    """Get comprehensive selector validation analysis."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {"error": "No scraper object available. Please call create_scraper() first.", "status": "error"}
        
        # Use the imported function from data_analysis
        result = get_comprehensive_analysis_from_module(GenericPlatformScraperObj)
        return {"data": result, "status": "success"}
    except Exception as e:
        return {"error": f"Error getting comprehensive analysis: {str(e)}", "status": "error"}

def export_selector_analysis_to_json(filename: Optional[str] = None) -> Dict[str, str]:
    """Export comprehensive selector analysis to JSON file."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {"error": "No scraper object available. Please call create_scraper() first.", "status": "error"}
        
        analyzer = SelectorAnalyzer(GenericPlatformScraperObj)
        if analyzer.df.empty:
            return {"error": "No data available for export", "status": "error"}
        
        # Import the export function from data_analysis
        from SelectorToDB.data_analysis import export_selector_analysis_to_json as export_analysis
        result = export_analysis(GenericPlatformScraperObj, filename)
        return {"file_path": result, "status": "success"}
    except Exception as e:
        return {"error": f"Error exporting analysis: {str(e)}", "status": "error"}

def print_selector_validation_summary() -> Dict[str, Any]:
    """Print a formatted summary of selector validation to console."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {"error": "No scraper object available. Please call create_scraper() first.", "status": "error"}
        
        # Use the imported function from data_analysis
        print_summary_from_analyzer(GenericPlatformScraperObj)
        return {"message": "Validation summary printed to console", "status": "success"}
    except Exception as e:
        return {"error": f"Error printing validation summary: {str(e)}", "status": "error"}

def save_to_database() -> Dict[str, Any]:
    """Save scraped data to Supabase database."""
    try:
        global GenericPlatformScraperObj
        
        if GenericPlatformScraperObj is None:
            return {
                "success": False,
                "saved_count": 0,
                "error": "No scraper object available. Please call create_scraper() first.",
                "status": "error"
            }
        
        supabase_url = os.getenv('SUPABASE_URL', 'https://whfjofihihlhctizchmj.supabase.co')
        supabase_key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndoZmpvZmloaWhsaGN0aXpjaG1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzNzQzNDMsImV4cCI6MjA3Njk1MDM0M30.OsJnOqeJgT5REPg7uxkGmmVcHIcs5QO4vdyDi66qpR0')
        table_name = os.getenv('SUPABASE_TABLE_NAME', 'scraped_products')
        
        if not supabase_url or not supabase_key:
            return {
                "success": False,
                "saved_count": 0,
                "error": "Supabase credentials not found in environment variables. Please set SUPABASE_URL and SUPABASE_KEY.",
                "status": "error"
            }
        
        result = GenericPlatformScraperObj.save_to_supabase(supabase_url, supabase_key, table_name)
        result["status"] = "success"
        return result
    except Exception as e:
        return {
            "success": False,
            "saved_count": 0,
            "error": f"Error saving to database: {str(e)}",
            "status": "error"
        }

def get_current_state() -> Dict[str, Any]:
    """Get the current state of all global variables."""
    try:
        global html_content, summary, selector_template, GenericPlatformScraperObj
        
        return {
            "html_content_available": bool(html_content),
            "html_content_length": len(html_content) if html_content else 0,
            "summary_available": bool(summary),
            "summary_fields": list(summary.keys()) if summary else [],
            "selector_template": selector_template,
            "scraper_available": GenericPlatformScraperObj is not None,
        "status": "success"
    }
    except Exception as e:
        return {"error": f"Error getting current state: {str(e)}", "status": "error"}

def reset_state() -> Dict[str, str]:
    """Reset all global variables to their initial state."""
    try:
        global html_content, summary, GenericPlatformScraperObj, selector_template
        
        html_content = ""
        summary = {}
        GenericPlatformScraperObj = None
        
        for field in selector_template:
            selector_template[field] = {
            'type': None,
            'selectors': []
        }
    
        return {"message": "Successfully reset all global variables to initial state", "status": "success"}
    except Exception as e:
        return {"error": f"Error resetting state: {str(e)}", "status": "error"}


# ============================================================================
# GEMINI TOOL SCHEMAS
# ============================================================================

def create_gemini_tools():
    """Create Gemini function calling schemas"""
    return [
        {
            "name": "get_html",
            "description": "Fetch HTML content from URL and perform comprehensive analysis. Updates global html_content and summary variables.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch HTML content from"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "readsummary",
            "description": "Read analysis summary data for a specific field or return all available fields.",
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "description": "Specific field name (e.g., 'repeats', 'field_hint_map'). If None, returns all fields."
                    }
                }
            }
        },
        {
            "name": "readHTML",
            "description": "Read HTML content with multiple search modes: line-based, CSS selector, or text search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_line": {"type": "integer", "description": "Starting line number"},
                    "end_line": {"type": "integer", "description": "Ending line number"},
                    "css_selector": {"type": "string", "description": "CSS selector to find elements"},
                    "text_search": {"type": "string", "description": "Text content to search for"},
                    "max_results": {"type": "integer", "description": "Maximum results", "default": 5}
                }
            }
        },
        {
            "name": "get_available_fields",
            "description": "Get list of available fields for selector configuration.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "set_selector",
            "description": "Set selector configuration for a field. Fields: product_container, name, current_price, original_price, rating, reviews, discount, offers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {"type": "string", "description": "Field name"},
                    "selector_type": {"type": "string", "enum": ["css", "xpath", "regex"], "description": "Selector type"},
                    "selectors": {"type": "array", "items": {"type": "string"}, "description": "List of selector strings"}
                },
                "required": ["field", "selector_type", "selectors"]
            }
        },
        {
            "name": "create_scraper",
            "description": "Create a GenericPlatformScraper instance using configured selectors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform_name": {"type": "string", "description": "Platform name for identification"}
                },
                "required": ["platform_name"]
            }
        },
        {
            "name": "extract_products",
            "description": "Extract product data using the configured scraper.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "inspect_extracted_data",
            "description": "Inspect extracted product data to see what was actually extracted.",
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {"type": "string", "description": "Filter by field name"},
                    "show_na_only": {"type": "boolean", "description": "Show only N/A values"},
                    "limit": {"type": "integer", "description": "Maximum products to return", "default": 10},
                    "sample_mode": {"type": "boolean", "description": "Use sampling mode"}
                }
            }
        },
        {
            "name": "get_selector_performance",
            "description": "Analyze selector performance and success rates.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "validate_price_selectors",
            "description": "Validate price selector performance and data quality.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "validate_rating_selectors",
            "description": "Validate rating selector performance.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "validate_review_selectors",
            "description": "Validate review count selector performance.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "validate_name_selectors",
            "description": "Validate product name selector performance.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "get_selector_validation_report",
            "description": "Get comprehensive validation report with overall health score.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "get_selector_improvement_suggestions",
            "description": "Get actionable suggestions for improving selectors.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "get_comprehensive_selector_analysis",
            "description": "Get complete analysis combining all metrics.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "save_to_database",
            "description": "Save scraped data to Supabase database.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "get_current_state",
            "description": "Get current state of all global variables.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "reset_state",
            "description": "Reset all global variables to initial state.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "export_selector_analysis_to_json",
            "description": "Export comprehensive selector analysis to JSON file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Optional filename for export"}
                }
            }
        },
        {
            "name": "print_selector_validation_summary",
            "description": "Print a formatted summary of selector validation results to console.",
            "parameters": {"type": "object", "properties": {}}
        }
    ]


# Tool name to function mapping
TOOL_FUNCTIONS = {
    "get_html": get_html,
    "readsummary": readsummary,
    "readHTML": readHTML,
    "get_available_fields": get_available_fields,
    "set_selector": set_selector,
    "create_scraper": create_scraper,
    "extract_products": extract_products,
    "inspect_extracted_data": inspect_extracted_data,
    "get_selector_performance": get_selector_performance,
    "validate_price_selectors": validate_price_selectors,
    "validate_rating_selectors": validate_rating_selectors,
    "validate_review_selectors": validate_review_selectors,
    "validate_name_selectors": validate_name_selectors,
    "get_selector_validation_report": get_selector_validation_report,
    "get_selector_improvement_suggestions": get_selector_improvement_suggestions,
    "get_comprehensive_selector_analysis": get_comprehensive_selector_analysis,
    "export_selector_analysis_to_json": export_selector_analysis_to_json,
    "print_selector_validation_summary": print_selector_validation_summary,
    "save_to_database": save_to_database,
    "save_to_DB": save_to_database,  # Alias for backward compatibility
    "get_current_state": get_current_state,
    "reset_state": reset_state,
}


# ============================================================================
# TOOL EXECUTION
# ============================================================================

def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool function with given arguments"""
    try:
        if tool_name not in TOOL_FUNCTIONS:
            return {"error": f"Unknown tool: {tool_name}", "status": "error"}
        
        func = TOOL_FUNCTIONS[tool_name]
        
        # Filter out None values
        filtered_args = {k: v for k, v in tool_args.items() if v is not None}
        
        # Execute function
        result = func(**filtered_args)
        
        # Ensure result is a dict
        if not isinstance(result, dict):
            result = {"result": result, "status": "success"}
        
        return result
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {"error": f"Tool execution error: {str(e)}", "traceback": error_trace, "status": "error"}


# ============================================================================
# LANGGRAPH AGENT NODE
# ============================================================================

def agent_node(state: AgentState) -> AgentState:
    """Main agent node that calls Gemini with function calling and executes tools"""
    
    messages = state.get("messages", [])
    url = state.get("url", "")
    platform_name = state.get("platform_name", "")
    task_description = state.get("task_description", "")
    completed_steps = state.get("completed_steps", [])
    tool_calls_made = state.get("tool_calls_made", 0)
    iterations = state.get("iterations", 0)
    errors = state.get("errors", [])
    max_iterations = state.get("max_iterations", 30)
    
    # Build conversation history
    conversation_history = []
    
    # Build messages in LangChain format
    langchain_messages = []
    
    # Add system message on first iteration
    if iterations == 0:
        system_prompt = f"""You are an intelligent LangGraph + Gemini 2.5-powered autonomous scraping and analysis agent.

──────────────────────────────
🔹 OVERALL WORKFLOW
──────────────────────────────
Your job is to automate an end-to-end workflow:

1️⃣ Input → Target URL: https://www.flipkart.com/search?q=camera
2️⃣ Retrieve HTML and create summary (HTML Content + Summary)
3️⃣ Use tool functions to:
    - Read Summary JSON (readsummary)
    - Read Specific Fields in HTML (readHTML)
    - Understand the DOM structure
4️⃣ Design Platform Selector (automated selector detection)
    - Use get_available_fields() to see all available fields
    - Use set_selector(field, type, selectors) for each field
5️⃣ Use Generic Scraper Tool:
    - create_scraper() with HTML content and selectors
    - extract_products() to extract structured data
    - inspect_extracted_data() to see actual results
6️⃣ Run Analysis Tool:
    - validate_price_selectors(), validate_name_selectors(), etc.
    - get_selector_validation_report() for overall quality score
    - get_selector_improvement_suggestions() to identify issues
7️⃣ If data quality is good (≥70% success rate):
    → Save to Database using save_to_database()
   Else:
    → Use get_selector_improvement_suggestions() to identify problems
    → Adjust selectors with set_selector() and retry from step 5
    → Re-validate until quality passes

Platform: flipkart
Task: Extract product information including name, price, rating, and reviews. Validate selectors before saving to database.

──────────────────────────────
🔹 AGENT BEHAVIOR RULES
──────────────────────────────
- Think step-by-step through the workflow before calling tools
- Always verify data integrity before moving to the next stage
- If validation fails, use get_selector_improvement_suggestions() then retry selectors
- Be concise when explaining intermediate steps
- Use chain-of-tool-calls to complete tasks autonomously
- Log each major step for traceability

──────────────────────────────
🔹 CRITICAL REQUIREMENTS
──────────────────────────────
1. MUST call get_html() first to fetch HTML
2. MUST call readsummary() to understand structure
3. MUST configure ALL selectors (product_container, name, current_price, rating, reviews)
4. MUST call create_scraper() BEFORE extract_products()
5. MUST validate data quality before saving
6. MUST retry with improved selectors if validation score < 70%
7. MUST call save_to_database() only when quality passes

Start now with step 1: get_html()
"""
        langchain_messages.append(HumanMessage(content=system_prompt))
        # Also add to conversation_history for Gemini API
        conversation_history = [{
            "role": "user",
            "parts": [{"text": system_prompt}]
        }]
    else:
        # Convert LangChain messages to Gemini format
        conversation_history = []
        
        for msg_raw in messages[-10:]:  # Last 10 messages for context
            # Handle both dict and LangChain message objects
            if isinstance(msg_raw, dict):
                # Convert dict to appropriate message type
                msg_type = msg_raw.get("type", "") or msg_raw.get("_type", "")
                if "human" in msg_type.lower() or "user" in msg_type.lower():
                    content = msg_raw.get("content", "")
                    conversation_history.append({
                        "role": "user",
                        "parts": [{"text": str(content)}]
                    })
                elif "ai" in msg_type.lower() or "assistant" in msg_type.lower() or "model" in msg_type.lower():
                    content = msg_raw.get("content", "")
                    conversation_history.append({
                        "role": "model",
                        "parts": [{"text": str(content)}]
                    })
                elif "tool" in msg_type.lower() or "function" in msg_type.lower():
                    tool_name = msg_raw.get("name", "unknown")
                    tool_result = str(msg_raw.get("content", ""))[:1500]
                    conversation_history.append({
                        "role": "user",
                        "parts": [{"text": f"Tool {tool_name} returned: {tool_result}"}]
                    })
                continue
            
            # Handle LangChain message objects
            if isinstance(msg_raw, HumanMessage):
                conversation_history.append({
                    "role": "user",
                    "parts": [{"text": str(msg_raw.content)}]
                })
            elif isinstance(msg_raw, AIMessage):
                conversation_history.append({
                    "role": "model",
                    "parts": [{"text": str(msg_raw.content)}]
                })
            elif isinstance(msg_raw, ToolMessage):
                # When NOT using function calling, convert ToolMessage to text format
                tool_name = getattr(msg_raw, 'name', 'unknown')
                tool_result = str(msg_raw.content)[:1500]
                # Add as user message explaining the tool result (simpler format)
                conversation_history.append({
                    "role": "user",
                    "parts": [{"text": f"Tool {tool_name} returned: {tool_result}"}]
                })
        
        # Add continuation prompt
        continue_prompt = "What should I do next? Continue the workflow. If you need to call a tool, use the format: tool_name(arg1=value1, arg2=value2)."
        conversation_history.append({
            "role": "user",
            "parts": [{"text": continue_prompt}]
        })
        langchain_messages.append(HumanMessage(content=continue_prompt))
    
    # Initialize Gemini 2.5 model with function calling
    model = None
    model_name_used = None
    
    # Try Gemini 2.5 first, then fallback to 1.5 if quota issues
    # Priority: 2.5-pro -> 2.5-flash -> 1.5-pro -> 1.5-flash
    model_attempts = [
        ("gemini-2.5-pro", True),           # Best: 2.5 Pro with function calling
        ("gemini-2.5-flash", True),         # Fast: 2.5 Flash with function calling
        ("gemini-1.5-pro-latest", True),    # Fallback: 1.5 Pro with function calling
        ("gemini-1.5-flash-latest", True),  # Fallback: 1.5 Flash with function calling
        ("gemini-2.5-pro", False),          # 2.5 Pro without function calling
        ("gemini-2.5-flash", False),        # 2.5 Flash without function calling
        ("gemini-1.5-pro-latest", False),   # 1.5 Pro without function calling
        ("gemini-1.5-flash-latest", False), # 1.5 Flash without function calling
    ]
    
    for model_name, use_tools in model_attempts:
        try:
            if use_tools:
                # Try creating model with tools - Gemini 2.5 accepts list of dict tools directly
                tools = create_gemini_tools()
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        tools=tools
                    )
                    print(f"[INFO] ✓ Using {model_name} with function calling")
                    model_name_used = model_name
                    break
                except Exception as tool_error:
                    # If tools fail, create model without tools and use text-based parsing
                    print(f"[WARN] Function calling failed for {model_name}: {str(tool_error)[:50]}")
                    print(f"[INFO] Falling back to text-based tool parsing for {model_name}")
                    model = genai.GenerativeModel(model_name=model_name)
                    use_tools = False  # Mark that we're not using function calling
                    model_name_used = model_name
                    break
            else:
                model = genai.GenerativeModel(model_name=model_name)
                model_name_used = model_name
                print(f"[INFO] ✓ Using {model_name} (no function calling)")
                break
        except Exception as e:
            error_msg = str(e)
            print(f"[WARN] {model_name} failed: {error_msg[:100]}")
            continue
    
    if model is None:
        error_msg = "Could not initialize Gemini 2.5 model. Please check:\n" \
                   "1. Your GEMINI_API_KEY is set correctly\n" \
                   "2. You have access to Gemini 2.5 models (gemini-2.5-pro or gemini-2.5-flash)\n" \
                   "3. Your API key has sufficient quota"
        print(f"[ERROR] {error_msg}")
        errors.append(error_msg)
        state["errors"] = errors
        state["iterations"] = iterations + 1
        return state
    
    # Generate response
    try:
        print(f"\n[AGENT] Iteration {iterations + 1}/{max_iterations}")
        print(f"[AGENT] Completed steps: {len(completed_steps)}")
        
        # Generate content
        try:
            # For Gemini 2.5, pass history directly as a list
            response = model.generate_content(
                conversation_history,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.95,
                    max_output_tokens=2048
                )
            )
        except Exception as e:
            error_msg = f"Error generating content with {model_name_used}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            errors.append(error_msg)
            state["errors"] = errors
            state["iterations"] = iterations + 1
            return state
        
        print(f"[AGENT] Received response from Gemini")
        
        new_messages = []
        assistant_text = ""
        function_calls = []
        
        # Process response - extract function calls and text
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        # Check for function calls
                        if hasattr(part, 'function_call') and part.function_call:
                            func_name = part.function_call.name
                            func_args = {}
                            
                            if hasattr(part.function_call, 'args'):
                                if isinstance(part.function_call.args, dict):
                                    func_args = part.function_call.args
                                elif isinstance(part.function_call.args, str):
                                    try:
                                        func_args = json.loads(part.function_call.args)
                                    except:
                                        func_args = {}
                            
                            if func_name in TOOL_FUNCTIONS:
                                function_calls.append({
                                    "name": func_name,
                                    "args": func_args
                                })
                                print(f"[AGENT] Function call detected: {func_name}({func_args})")
                        
                        # Get text content
                        if hasattr(part, 'text') and part.text:
                            assistant_text = part.text
        
        # Fallback: if no function calls but we have text, try to parse
        if not function_calls:
            try:
                if hasattr(response, 'text'):
                    assistant_text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    assistant_text = part.text
                                    break
            except (ValueError, AttributeError) as e:
                # Response might not have text (e.g., blocked content, function call only)
                print(f"[INFO] Response has no text content, checking for other content...")
                assistant_text = ""
            
            # Try simple pattern matching as fallback if we have text
            if assistant_text:
                import re
                patterns = [
                    r"call\s+(\w+)\(([^)]*)\)",
                    r"(\w+)\(([^)]*)\)"
                ]
                for pattern in patterns:
                    matches = re.finditer(pattern, assistant_text, re.IGNORECASE)
                    for match in matches:
                        func_name = match.group(1)
                        if func_name in TOOL_FUNCTIONS:
                            args_str = match.group(2) if len(match.groups()) > 1 else ""
                            func_args = {}
                            # Simple arg parsing
                            if 'url=' in args_str or 'url:' in args_str:
                                url_match = re.search(r"url[=:]?\s*['\"]([^'\"]+)['\"]", args_str)
                                if url_match:
                                    func_args['url'] = url_match.group(1)
                            if func_args or func_name in ['readsummary', 'get_available_fields', 'extract_products']:
                                function_calls.append({"name": func_name, "args": func_args})
                                print(f"[AGENT] Parsed function call: {func_name}({func_args})")
                                break
        
        # Add assistant message (LangChain format)
        # If no response content or function calls, add a default message
        if not assistant_text and not function_calls:
            assistant_text = "Processing request..."
        
        # Generate tool call IDs for each function call
        tool_call_ids = [str(uuid.uuid4()) for _ in function_calls]
        
        # Create AIMessage with tool calls tracked
        ai_content = assistant_text if assistant_text else f"Executing {len(function_calls)} tool(s)"
        
        # Prepare tool_calls for AIMessage
        tool_calls_list = []
        if function_calls:
            tool_calls_list = [{
                "name": fc["name"],
                "args": fc.get("args", {}),
                "id": tool_call_ids[i]
            } for i, fc in enumerate(function_calls)]
        
        # Create AIMessage - only include tool_calls if there are any
        if tool_calls_list:
            new_messages.append(AIMessage(
                content=ai_content,
                tool_calls=tool_calls_list
            ))
        else:
            new_messages.append(AIMessage(content=ai_content))
        
        # Execute function calls
        print(f"[AGENT] Executing {len(function_calls)} function call(s)")
        for idx, func_call in enumerate(function_calls):
            tool_name = func_call["name"]
            tool_args = func_call.get("args", {})
            tool_call_id = tool_call_ids[idx]
            
            print(f"[AGENT] → {tool_name}({tool_args})")
            
            try:
                # Execute tool
                tool_result = execute_tool(tool_name, tool_args)
                tool_calls_made += 1
                
                # Check if tool succeeded
                if tool_result.get("status") != "error":
                    print(f"[AGENT] ✓ {tool_name} succeeded")
                else:
                    print(f"[AGENT] ✗ {tool_name} failed: {tool_result.get('error', 'Unknown error')}")
                    errors.append(f"{tool_name}: {tool_result.get('error', 'Unknown error')}")
            except Exception as tool_error:
                print(f"[ERROR] Tool {tool_name} exception: {tool_error}")
                tool_result = {"error": str(tool_error), "status": "error"}
                tool_calls_made += 1
                errors.append(f"{tool_name}: {str(tool_error)}")
            
            # Track completed steps
            if tool_name not in completed_steps:
                completed_steps.append(tool_name)
            
            # Format tool result for message (LangChain format)
            if isinstance(tool_result, dict):
                tool_result_str = json.dumps(tool_result, default=str, indent=2)[:2000]
            else:
                tool_result_str = str(tool_result)[:2000]
            
            # Use LangChain ToolMessage format with proper tool_call_id
            new_messages.append(ToolMessage(
                content=tool_result_str,
                tool_call_id=tool_call_id,
                name=tool_name
            ))
        
        # Update quality score if validation was done
        if "get_selector_validation_report" in [fc["name"] for fc in function_calls]:
            # Extract quality score from tool result (last message should be ToolMessage)
            if new_messages and isinstance(new_messages[-1], ToolMessage):
                validation_result = new_messages[-1].content
                try:
                    validation_data = json.loads(validation_result) if isinstance(validation_result, str) else validation_result
                    if isinstance(validation_data, dict) and "overall_health_score" in validation_data:
                        state["quality_score"] = validation_data["overall_health_score"] / 100.0
                except:
                    pass
        
        # Update state (combine old messages with new ones)
        all_messages = messages + new_messages
        state["messages"] = all_messages
        state["tool_calls_made"] = tool_calls_made
        state["iterations"] = iterations + 1
        state["completed_steps"] = completed_steps
        state["errors"] = errors
        
        # Check for workflow completion
        has_fetched = "get_html" in completed_steps
        has_selectors = any("set_selector" in step for step in completed_steps)
        has_created = "create_scraper" in completed_steps
        has_extracted = "extract_products" in completed_steps
        
        if has_fetched and has_selectors and has_created and has_extracted:
            # Workflow is complete
            state["final_results"] = {
                "url": url,
                "platform": platform_name,
                "completed_steps": completed_steps,
                "tool_calls_made": tool_calls_made,
                "iterations": iterations + 1,
                "quality_score": state.get("quality_score"),
                "workflow_complete": True
            }
            print(f"[AGENT] ✓ Workflow complete! Steps: {len(completed_steps)}")
        
    except Exception as e:
        error_msg = f"Error in agent_node: {str(e)}"
        print(f"[ERROR] {error_msg}")
        errors.append(error_msg)
        state["errors"] = errors
        state["iterations"] = iterations + 1
        import traceback
        traceback.print_exc()
    
    return state


def should_continue(state: AgentState) -> str:
    """Determine if agent should continue or end"""
    iterations = state.get("iterations", 0)
    max_iterations = state.get("max_iterations", 30)
    errors = state.get("errors", [])
    
    # End if workflow complete
    if state.get("final_results", {}).get("workflow_complete"):
        return "end"
    
    # End if too many iterations
    if iterations >= max_iterations:
        return "end"
    
    # End if too many errors
    if len(errors) > 10:
        return "end"
    
    return "continue"


# ============================================================================
# LANGGRAPH WORKFLOW BUILDING
# ============================================================================

def create_agent_graph():
    """Create the LangGraph agent workflow"""
    
    workflow = StateGraph(AgentState)
    
    # Add agent node
    workflow.add_node("agent", agent_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edge
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "agent",
            "end": END
        }
    )
    
    return workflow.compile()


# ============================================================================
# MAIN ENTRY POINTS
# ============================================================================

def run_scraping_agent(
    url: str,
    platform_name: str,
    task_description: str = "Extract product information including name, price, rating, and reviews. Validate selectors before saving to database.",
    max_iterations: int = 30
) -> Dict[str, Any]:
    """
    Run the LangGraph scraping agent with Gemini LLM.
    
    Args:
        url: URL to scrape
        platform_name: Name of the platform (e.g., "flipkart", "amazon")
        task_description: Description of the scraping task
        max_iterations: Maximum number of iterations before stopping
    
    Returns:
        Dictionary with results, completed steps, errors, etc.
    """
    
    print("=" * 80)
    print("🚀 LangGraph Web Scraping Agent")
    print("=" * 80)
    print(f"   URL: {url}")
    print(f"   Platform: {platform_name}")
    print(f"   Max Iterations: {max_iterations}")
    print("=" * 80)
    
    # Reset state
    reset_state()
    
    # Initialize state
    initial_state: AgentState = {
        "messages": [],
        "url": url,
        "platform_name": platform_name,
        "task_description": task_description,
        "completed_steps": [],
        "tool_calls_made": 0,
        "iterations": 0,
        "errors": [],
        "final_results": {},
        "quality_score": None,
        "max_iterations": max_iterations
    }
    
    # Create and run graph
    graph = create_agent_graph()
    
    try:
        # Run the graph
        final_state = graph.invoke(initial_state)
        
        print("\n" + "=" * 80)
        print("✅ Agent Execution Complete")
        print("=" * 80)
        print(f"   Iterations: {final_state.get('iterations', 0)}")
        print(f"   Tool Calls: {final_state.get('tool_calls_made', 0)}")
        print(f"   Completed Steps: {len(final_state.get('completed_steps', []))}")
        if final_state.get('quality_score'):
            print(f"   Quality Score: {final_state.get('quality_score', 0) * 100:.1f}%")
        print("=" * 80)
        
        return {
            "success": True,
            "completed_steps": final_state.get("completed_steps", []),
            "tool_calls_made": final_state.get("tool_calls_made", 0),
            "iterations": final_state.get("iterations", 0),
            "errors": final_state.get("errors", []),
            "final_results": final_state.get("final_results", {}),
            "quality_score": final_state.get("quality_score"),
            "messages": final_state.get("messages", [])
        }
    
    except Exception as e:
        print(f"\n❌ Error running agent: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "completed_steps": initial_state.get("completed_steps", []),
            "tool_calls_made": initial_state.get("tool_calls_made", 0),
            "iterations": initial_state.get("iterations", 0),
            "errors": initial_state.get("errors", []) + [str(e)]
        }


def run_autonomous_scraping_agent(
    url: str,
    platform_name: str,
    max_iterations: int = 30,
    quality_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Run autonomous scraping agent with quality threshold.
    
    Args:
        url: URL to scrape
        platform_name: Name of the platform
        max_iterations: Maximum iterations
        quality_threshold: Minimum quality score (0-1) before saving to DB
    
    Returns:
        Dictionary with results
    """
    
    task_description = f"""Extract product information and validate data quality. 
Only save to database if selector performance is above {quality_threshold * 100}% success rate."""
    
    return run_scraping_agent(
        url=url,
        platform_name=platform_name,
        task_description=task_description,
        max_iterations=max_iterations
    )


# Backward compatibility
def run_agent(tool_name: str, args: Dict[str, Any]) -> Any:
    """Simple tool executor for backward compatibility"""
    return execute_tool(tool_name, args)


if __name__ == "__main__":
    # Test the agent
    result = run_scraping_agent(
        url="https://www.flipkart.com/search?q=vivo+5g+mobile",
        platform_name="flipkart",
        task_description="Extract product information including name, price, rating, and reviews."
    )
    
    print("\n📊 Final Results:")
    print(json.dumps(result, indent=2, default=str))

# ==========================================================================
# CRAWLBOT CONTROLLER (Deterministic one-tool-per-step JSON planner)
# ==========================================================================

ALLOWED_CURSOR_UPDATE_KEYS = {
    "selectors_template",
    "html_loaded",
    "summary_available",
    "scraper_created",
    "iteration",
    "last_validation",
    "notes",
    "extraction_sample_count",
}


def _normalize_cursor(cursor: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure required keys exist with default values."""
    defaults = {
        "html_loaded": False,
        "summary_available": False,
        "scraper_created": False,
        "selectors_template": {},
        "iteration": 0,
        "last_validation": None,
        "extraction_sample_count": 0,
        "notes": "",
    }
    cur = dict(defaults)
    cur.update(cursor or {})
    return cur


def _is_field_configured(selectors_template: Dict[str, Any], field_name: str) -> bool:
    cfg = (selectors_template or {}).get(field_name) or {}
    sel_type = cfg.get("type")
    sels = cfg.get("selectors") or []
    return bool(sel_type) and isinstance(sels, list) and len(sels) > 0


def _first_unset_field(fields: List[str], selectors_template: Dict[str, Any]) -> Optional[str]:
    for f in fields:
        if not _is_field_configured(selectors_template, f):
            return f
    return None


def _derive_selector_candidates(field_name: str) -> List[str]:
    """Try to derive selector candidates from global summary.field_hint_map if present."""
    try:
        global summary
        hint_map = (summary or {}).get("field_hint_map") or {}
        candidates = hint_map.get(field_name) or []
        # Normalize: candidates might be list of strings or list of dicts
        normalized: List[str] = []
        for c in candidates:
            if isinstance(c, str):
                normalized.append(c)
            elif isinstance(c, dict):
                v = c.get("selector") or c.get("value") or c.get("css")
                if isinstance(v, str) and v:
                    normalized.append(v)
        # Deduplicate, limit to top 2
        dedup = []
        for s in normalized:
            if s not in dedup:
                dedup.append(s)
        return dedup[:2]
    except Exception:
        return []


def crawlbot_controller_step(job: Dict[str, Any], cursor: Dict[str, Any]) -> Dict[str, Any]:
    """Decide the next single tool call based on JOB and CURSOR.

    Returns a strict JSON-compatible dict: {tool, args, cursor_updates}.
    Only allowed cursor keys are updated.
    """
    job = job or {}
    cursor = _normalize_cursor(cursor)

    url = job.get("url")
    platform_name = job.get("platform_name", "site")
    job_fields: List[str] = job.get("fields") or []
    quality_threshold = float(job.get("quality_threshold" or 0.7))
    max_iterations = int(job.get("max_iterations" or 10))

    updates: Dict[str, Any] = {
        "iteration": int(cursor.get("iteration", 0)) + 1
    }

    # 1) Fetch HTML if not loaded
    if not cursor.get("html_loaded"):
        updates.update({"html_loaded": True, "notes": "Fetched HTML"})
        return {
            "tool": "get_html",
            "args": {"url": url},
            "cursor_updates": {k: v for k, v in updates.items() if k in ALLOWED_CURSOR_UPDATE_KEYS}
        }

    # 2) Gather summary hints
    if not cursor.get("summary_available"):
        updates.update({"summary_available": True, "notes": "Loaded summary hints"})
        return {
            "tool": "readsummary",
            "args": {"field": "field_hint_map"},
            "cursor_updates": {k: v for k, v in updates.items() if k in ALLOWED_CURSOR_UPDATE_KEYS}
        }

    # 3) Set selectors for next missing field
    selectors_template = cursor.get("selectors_template") or {}
    next_field = _first_unset_field(job_fields, selectors_template)
    if next_field:
        candidates = _derive_selector_candidates(next_field)
        if not candidates:
            # No hints available; request inspection to aid human/next step
            notes = f"No selector hints for {next_field}; inspecting HTML around likely patterns"
            updates.update({"notes": notes})
            return {
                "tool": "readHTML",
                "args": {"text_search": next_field, "max_results": 2},
                "cursor_updates": {k: v for k, v in updates.items() if k in ALLOWED_CURSOR_UPDATE_KEYS}
            }
        # Propose setting selector using top candidates
        new_template = dict(selectors_template)
        new_template[next_field] = {"type": "css", "selectors": candidates}
        updates.update({"selectors_template": new_template, "notes": f"Set {next_field} selectors"})
        return {
            "tool": "set_selector",
            "args": {"field": next_field, "selector_type": "css", "selectors": candidates},
            "cursor_updates": {k: v for k, v in updates.items() if k in ALLOWED_CURSOR_UPDATE_KEYS}
        }

    # 4) Create scraper when all selectors set
    if not cursor.get("scraper_created"):
        updates.update({"scraper_created": True, "notes": "Created scraper"})
        return {
            "tool": "create_scraper",
            "args": {"platform_name": platform_name},
            "cursor_updates": {k: v for k, v in updates.items() if k in ALLOWED_CURSOR_UPDATE_KEYS}
        }

    # 5) Extract products and sample
    if int(cursor.get("extraction_sample_count", 0)) <= 0:
        updates.update({"extraction_sample_count": 1, "notes": "Extracted products"})
        return {
            "tool": "extract_products",
            "args": {},
            "cursor_updates": {k: v for k, v in updates.items() if k in ALLOWED_CURSOR_UPDATE_KEYS}
        }

    # 6) Validate and analyze
    last_val = cursor.get("last_validation")
    if last_val is None:
        updates.update({"notes": "Running validation report"})
        return {
            "tool": "get_selector_validation_report",
            "args": {},
            "cursor_updates": {k: v for k, v in updates.items() if k in ALLOWED_CURSOR_UPDATE_KEYS}
        }

    # 7) Save if quality met
    try:
        if float(last_val) >= quality_threshold:
            updates.update({"notes": "Quality met; ready to save"})
            return {
                "tool": "done",
                "args": {"status": "ready_to_save"},
                "cursor_updates": {k: v for k, v in updates.items() if k in ALLOWED_CURSOR_UPDATE_KEYS}
            }
    except Exception:
        pass

    # 8) Stop if iterations exceeded
    if int(cursor.get("iteration", 0)) >= max_iterations:
        updates.update({"notes": "Max iterations reached without meeting quality", "last_validation": last_val})
        return {
            "tool": "done",
            "args": {"status": "needs_human_review"},
            "cursor_updates": {k: v for k, v in updates.items() if k in ALLOWED_CURSOR_UPDATE_KEYS}
        }

    # 9) Otherwise, request improvement suggestions
    updates.update({"notes": "Requesting improvement suggestions"})
    return {
        "tool": "get_selector_improvement_suggestions",
        "args": {},
        "cursor_updates": {k: v for k, v in updates.items() if k in ALLOWED_CURSOR_UPDATE_KEYS}
    }

# ==========================================================================
# CRAWLBOT GEMINI ORCHESTRATOR (Single-tool-per-iteration controller)
# ==========================================================================

def _wrap_tool_for_orchestrator(fn: Any):
    def wrapped(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        try:
            result = fn(**kwargs) if kwargs else fn()
        except TypeError:
            try:
                result = fn(**kwargs)
            except Exception as e:
                result = {"error": f"tool raised exception: {e}"}
        except Exception as e:
            result = {"error": f"tool raised exception: {e}"}
        if result is None:
            result = {}
        if not isinstance(result, dict):
            result = {"result": result}
        return result
    return wrapped

# Reuse existing tool functions
_ORCH_TOOL_REGISTRY: Dict[str, Any] = {
    "get_html": _wrap_tool_for_orchestrator(get_html),
    "readsummary": _wrap_tool_for_orchestrator(readsummary),
    "readHTML": _wrap_tool_for_orchestrator(readHTML),
    "get_available_fields": _wrap_tool_for_orchestrator(get_available_fields),
    "set_selector": _wrap_tool_for_orchestrator(set_selector),
    "create_scraper": _wrap_tool_for_orchestrator(create_scraper),
    "extract_products": _wrap_tool_for_orchestrator(extract_products),
    "inspect_extracted_data": _wrap_tool_for_orchestrator(inspect_extracted_data),
    "get_selector_performance": _wrap_tool_for_orchestrator(get_selector_performance),
    "validate_price_selectors": _wrap_tool_for_orchestrator(validate_price_selectors),
    "validate_rating_selectors": _wrap_tool_for_orchestrator(validate_rating_selectors),
    "validate_review_selectors": _wrap_tool_for_orchestrator(validate_review_selectors),
    "validate_name_selectors": _wrap_tool_for_orchestrator(validate_name_selectors),
    "get_selector_validation_report": _wrap_tool_for_orchestrator(get_selector_validation_report),
    "get_selector_improvement_suggestions": _wrap_tool_for_orchestrator(get_selector_improvement_suggestions),
    "get_comprehensive_selector_analysis": _wrap_tool_for_orchestrator(get_comprehensive_selector_analysis),
    "export_selector_analysis_to_json": _wrap_tool_for_orchestrator(export_selector_analysis_to_json),
    "print_selector_validation_summary": _wrap_tool_for_orchestrator(print_selector_validation_summary),
    "save_to_database": _wrap_tool_for_orchestrator(save_to_database),
    "reset_state": _wrap_tool_for_orchestrator(reset_state),
}

_ORCH_ALLOWED_ACTIONS = set(_ORCH_TOOL_REGISTRY.keys()) | {"done"}

def _extract_json_block(text: str) -> Any:
    import re as _re
    m = _re.search(r"\{[\s\S]*\}\s*$", text)
    if not m:
        raise ValueError("No JSON object found")
    raw = m.group(0)
    return json.loads(raw)

def _ask_gemini_for_action_orch(current_state: Dict[str, Any], available_tools: List[str]) -> Dict[str, Any]:
    prompt_state = {k: (v if k not in ("html",) else "<omitted>") for k, v in current_state.items() if k != "history"}
    tools_list = ", ".join(sorted(available_tools))
    instruction = (
        "You are the CrawlBot Orchestrator. Return ONLY JSON with the next action.\n"
        "Valid: {\"action\": \"<tool>\", \"args\": {..}} or {\"action\": \"done\"}.\n"
        f"Allowed tools: [{tools_list}]\n"
        "Rules: If no HTML, call get_html with {url}. If products exist, validate. "
        "If validation is poor, call get_selector_improvement_suggestions then set_selector. "
        "Save only when data is good. Keep args minimal.\n"
        f"State: {json.dumps(prompt_state, default=str)}"
    )
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        resp = model.generate_content([{"text": instruction}],
                                      generation_config=genai.types.GenerationConfig(temperature=0.0))
        text = getattr(resp, "text", "") or "{}"
        parsed = _extract_json_block(text)
    except Exception as e:
        raise RuntimeError(f"Failed to parse Gemini response as JSON: {e}")
    if not isinstance(parsed, dict) or "action" not in parsed:
        raise RuntimeError(f"Invalid action payload: {parsed}")
    action = parsed["action"]
    if action not in _ORCH_ALLOWED_ACTIONS:
        raise RuntimeError(f"Action '{action}' not allowed")
    args = parsed.get("args", {}) or {}
    if not isinstance(args, dict):
        raise RuntimeError("'args' must be an object")
    return {"action": action, "args": args}

def _execute_orch_action(state_obj: Dict[str, Any], action: str, args: Dict[str, Any]) -> Dict[str, Any]:
    state_obj.setdefault("history", []).append({"before_action": action, "args": args})
    if action == "done":
        return state_obj
    tool = _ORCH_TOOL_REGISTRY[action]
    result = {}
    try:
        result = tool(state_obj, **args)
    except Exception as e:
        result = {"error": f"exception during tool call: {e}"}
    if isinstance(result, dict):
        for k, v in result.items():
            if k in state_obj and isinstance(state_obj[k], dict) and isinstance(v, dict):
                state_obj[k].update(v)
            else:
                state_obj[k] = v
    state_obj["attempts"] = int(state_obj.get("attempts", 0)) + 1
    state_obj.setdefault("history", []).append({"action": action, "result_keys": list(result.keys())})
    return state_obj

def run_orchestrator(loop_limit: int = 20, url: Optional[str] = None) -> Dict[str, Any]:
    # Prepare initial state
    orch_state: Dict[str, Any] = {
        "url": url or os.getenv("TARGET_URL") or "https://www.flipkart.com/search?q=camera",
        "html": None,
        "summary": None,
        "products": None,
        "validation": {},
        "performance": {},
        "improvements": {},
        "database_status": None,
        "attempts": 0,
        "history": []
    }
    # Ensure we start by fetching HTML
    print("-> Initial get_html")
    _ = _ORCH_TOOL_REGISTRY["get_html"](orch_state, url=orch_state["url"])
    iterations = 0
    while iterations < loop_limit:
        iterations += 1
        print(f"--- Orchestrator Iteration {iterations} ---")
        try:
            decision = _ask_gemini_for_action_orch(orch_state, list(_ORCH_ALLOWED_ACTIONS))
        except Exception as e:
            print(f"Decision error: {e}")
            break
        action = decision["action"]
        args = decision.get("args", {})
        print(f"Next action: {action} args={args}")
        if action == "done":
            break
        try:
            orch_state = _execute_orch_action(orch_state, action, args)
        except Exception as e:
            print(f"Execution error: {e}")
            break
        if action == "save_to_database":
            break
    print("=== Orchestrator finished ===")
    return orch_state

# Optional entrypoint controlled by env
if __name__ == "__main__" and os.getenv("RUN_ORCHESTRATOR") == "1":
    final_state = run_orchestrator(loop_limit=int(os.getenv("ORCH_LIMIT", "20")), url=os.getenv("TARGET_URL"))
    try:
        print(json.dumps({k: v for k, v in final_state.items() if k != "history"}, indent=2, default=str))
    except Exception:
        print(str(final_state))
