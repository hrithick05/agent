from typing import TypedDict, Dict, Any, List, Optional, Literal

import json

# LangGraph imports
from langgraph.graph import StateGraph, START, END

# Import direct tools from app.py (non-MCP)
from AgentModule.app import (
    get_html,
    readsummary,
    readHTML,
    scrape,
    set_selector,
    get_available_fields,
    save_to_DB,
    get_selector_performance_tool,
    validate_price_selectors_tool,
    validate_rating_selectors_tool,
    validate_review_selectors_tool,
    validate_name_selectors_tool,
    get_selector_validation_report_tool,
    get_selector_improvement_suggestions_tool,
    get_comprehensive_selector_analysis_tool,
    export_selector_analysis_to_json_tool,
    print_selector_validation_summary_tool,
    generate_selectors_with_model,
)


class ScrapingAgentState(TypedDict):
    url: str
    platform_name: str
    target_fields: List[str]
    current_step: str
    completed_steps: List[str]
    html_content: Optional[str]
    summary: Optional[Dict[str, Any]]
    selector_template: Dict[str, Any]
    scraper_created: bool
    products_extracted: List[Dict[str, Any]]
    performance_analysis: Optional[Dict[str, Any]]
    validation_results: Dict[str, Any]
    improvement_suggestions: Optional[Dict[str, Any]]
    final_results: Optional[Dict[str, Any]]
    errors: List[str]
    success: bool


def fetch_html_node(state: ScrapingAgentState) -> ScrapingAgentState:
    try:
        result = get_html(state['url'])
        if 'error' in result:
            return {**state, "current_step": "error", "errors": state.get("errors", []) + [f"HTML fetch failed: {result['error']}"], "success": False}
        summary_result = readsummary()
        summary_data = summary_result if isinstance(summary_result, dict) else {}
        return {**state, "current_step": "analyze_html", "completed_steps": state.get("completed_steps", []) + ["fetch_html"], "html_content": "HTML content fetched successfully", "summary": summary_data, "success": True}
    except Exception as e:
        return {**state, "current_step": "error", "errors": state.get("errors", []) + [f"HTML fetch error: {str(e)}"], "success": False}


def analyze_html_node(state: ScrapingAgentState) -> ScrapingAgentState:
    try:
        fields_result = get_available_fields()
        available_fields = fields_result.get("available_fields", [])
        if not available_fields:
            available_fields = ["product_container", "name", "current_price", "original_price", "rating", "reviews", "discount", "offers"]
        return {**state, "current_step": "configure_selectors", "completed_steps": state.get("completed_steps", []) + ["analyze_html"], "target_fields": available_fields, "success": True}
    except Exception as e:
        return {**state, "current_step": "error", "errors": state.get("errors", []) + [f"HTML analysis error: {str(e)}"], "success": False}


def configure_selectors_node(state: ScrapingAgentState) -> ScrapingAgentState:
    try:
        selector_configs = generate_selectors_with_model(state.get("url", "")) or {}
        if not selector_configs:
            return {**state, "current_step": "error", "errors": state.get("errors", []) + ["Model failed to produce selectors or no hints available."], "success": False}
        # Require product_container
        pcfg = selector_configs.get("product_container", {})
        if not isinstance(pcfg, dict) or not pcfg.get("selectors"):
            return {**state, "current_step": "error", "errors": state.get("errors", []) + ["Model output missing product_container selectors"], "success": False}
        selector_template: Dict[str, Any] = {}
        target_fields = state.get("target_fields", []) or list(selector_configs.keys())
        for field, config in selector_configs.items():
            if field in target_fields:
                result = set_selector(config["field"], config["selector_type"], config["selectors"])
                if "error" not in result:
                    selector_template[field] = result.get("template", {}).get(field, {})
        return {**state, "current_step": "create_scraper", "completed_steps": state.get("completed_steps", []) + ["configure_selectors"], "selector_template": selector_template, "success": True}
    except Exception as e:
        return {**state, "current_step": "error", "errors": state.get("errors", []) + [f"Selector configuration error: {str(e)}"], "success": False}


def create_scraper_node(state: ScrapingAgentState) -> ScrapingAgentState:
    try:
        result = scrape(state["selector_template"], state["platform_name"])
        if "error" in result:
            return {**state, "current_step": "error", "errors": state.get("errors", []) + [f"Scraper creation failed: {result['error']}"], "success": False}
        return {**state, "current_step": "extract_products", "completed_steps": state.get("completed_steps", []) + ["create_scraper"], "scraper_created": True, "success": True}
    except Exception as e:
        return {**state, "current_step": "error", "errors": state.get("errors", []) + [f"Scraper creation error: {str(e)}"], "success": False}


def extract_products_node(state: ScrapingAgentState) -> ScrapingAgentState:
    try:
        from AgentModule.app import GenericPlatformScraperObj
        products: List[Dict[str, Any]] = []
        if GenericPlatformScraperObj is not None:
            products = GenericPlatformScraperObj.scrape()
        return {**state, "current_step": "analyze_performance", "completed_steps": state.get("completed_steps", []) + ["extract_products"], "products_extracted": products, "success": True}
    except Exception as e:
        return {**state, "current_step": "error", "errors": state.get("errors", []) + [f"Product extraction error: {str(e)}"], "success": False}


def analyze_performance_node(state: ScrapingAgentState) -> ScrapingAgentState:
    try:
        performance_result = get_selector_performance_tool()
        validation_results = {
            "price": validate_price_selectors_tool(),
            "rating": validate_rating_selectors_tool(),
            "review": validate_review_selectors_tool(),
            "name": validate_name_selectors_tool(),
        }
        improvement_result = get_selector_improvement_suggestions_tool()
        return {**state, "current_step": "generate_report", "completed_steps": state.get("completed_steps", []) + ["analyze_performance"], "performance_analysis": performance_result, "validation_results": validation_results, "improvement_suggestions": improvement_result, "success": True}
    except Exception as e:
        return {**state, "current_step": "error", "errors": state.get("errors", []) + [f"Performance analysis error: {str(e)}"], "success": False}


def generate_report_node(state: ScrapingAgentState) -> ScrapingAgentState:
    try:
        comprehensive_analysis = get_comprehensive_selector_analysis_tool()
        json_file = export_selector_analysis_to_json_tool("scraping_analysis.json")
        print_selector_validation_summary_tool()
        health_data = {}
        if isinstance(comprehensive_analysis, dict) and 'validation_report' in comprehensive_analysis:
            health_data = comprehensive_analysis['validation_report'].get('overall_selector_health', {})
        final_results = {
            "url": state["url"],
            "platform": state["platform_name"],
            "products_found": len(state.get("products_extracted", [])),
            "performance": state.get("performance_analysis", {}),
            "validation": state.get("validation_results", {}),
            "improvements": state.get("improvement_suggestions", {}),
            "comprehensive_analysis": comprehensive_analysis,
            "health_data": health_data,
            "export_file": json_file,
            "completed_steps": state.get("completed_steps", [])
        }
        return {**state, "current_step": "save_data", "completed_steps": state.get("completed_steps", []) + ["generate_report"], "final_results": final_results, "success": True}
    except Exception as e:
        final_results = {
            "url": state["url"],
            "platform": state["platform_name"],
            "products_found": len(state.get("products_extracted", [])),
            "performance": state.get("performance_analysis", {}),
            "validation": state.get("validation_results", {}),
            "improvements": state.get("improvement_suggestions", {}),
            "comprehensive_analysis": {"error": str(e)},
            "health_data": {},
            "export_file": "Failed to export",
            "completed_steps": state.get("completed_steps", [])
        }
        return {**state, "current_step": "save_data", "completed_steps": state.get("completed_steps", []) + ["generate_report"], "final_results": final_results, "success": True}


def save_data_node(state: ScrapingAgentState) -> ScrapingAgentState:
    try:
        _ = save_to_DB()
        return {**state, "current_step": "complete", "completed_steps": state.get("completed_steps", []) + ["save_data"], "success": True}
    except Exception as e:
        return {**state, "current_step": "error", "errors": state.get("errors", []) + [f"Data save error: {str(e)}"], "success": False}


def error_node(state: ScrapingAgentState) -> ScrapingAgentState:
    return {**state, "current_step": "error", "success": False}


def build_scraping_agent():
    graph = StateGraph(ScrapingAgentState)
    graph.add_node("fetch_html", fetch_html_node)
    graph.add_node("analyze_html", analyze_html_node)
    graph.add_node("configure_selectors", configure_selectors_node)
    graph.add_node("create_scraper", create_scraper_node)
    graph.add_node("extract_products", extract_products_node)
    graph.add_node("analyze_performance", analyze_performance_node)
    graph.add_node("generate_report", generate_report_node)
    graph.add_node("save_data", save_data_node)
    graph.add_node("error", error_node)
    graph.add_edge(START, "fetch_html")
    graph.add_edge("fetch_html", "analyze_html")
    graph.add_edge("analyze_html", "configure_selectors")
    graph.add_edge("configure_selectors", "create_scraper")
    graph.add_edge("create_scraper", "extract_products")
    graph.add_edge("extract_products", "analyze_performance")
    graph.add_edge("analyze_performance", "generate_report")
    graph.add_edge("generate_report", "save_data")
    graph.add_edge("save_data", END)
    graph.add_edge("error", END)
    return graph.compile()


def run_scraping_agent(url: str, platform_name: str = "unknown_platform") -> Dict[str, Any]:
    agent = build_scraping_agent()
    initial_state: ScrapingAgentState = {
        "url": url,
        "platform_name": platform_name,
        "target_fields": [],
        "current_step": "fetch_html",
        "completed_steps": [],
        "html_content": None,
        "summary": None,
        "selector_template": {},
        "scraper_created": False,
        "products_extracted": [],
        "performance_analysis": None,
        "validation_results": {},
        "improvement_suggestions": None,
        "final_results": None,
        "errors": [],
        "success": True
    }
    return agent.invoke(initial_state)


def run_agent(tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
    from AgentModule.app import (
        get_html as _gh,
        readsummary as _rs,
        readHTML as _rh,
        scrape as _sc,
        set_selector as _ss,
        get_available_fields as _gaf,
        save_to_DB as _sdb
    )
    tool_map = {
        "get_html": _gh,
        "readsummary": _rs,
        "readHTML": _rh,
        "scrape": _sc,
        "set_selector": _ss,
        "get_available_fields": _gaf,
        "save_to_DB": _sdb,
    }
    if tool not in tool_map:
        return {"error": f"Unknown tool: {tool}", "available_tools": list(tool_map.keys())}
    fn = tool_map[tool]
    try:
        result = fn(**args) if isinstance(args, dict) else fn(args)
        return {"tool": tool, "result": result}
    except Exception as e:
        return {"tool": tool, "error": str(e)}


__all__ = [
    "run_scraping_agent",
    "build_scraping_agent",
    "run_agent",
    "ScrapingAgentState",
]



