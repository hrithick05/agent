from typing import TypedDict, Dict, Any, List, Optional, Literal
import json

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

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
	# Input parameters
	url: str
	platform_name: str
	target_fields: List[str]
	
	# Workflow state
	current_step: str
	completed_steps: List[str]
	
	# Data state
	html_content: Optional[str]
	summary: Optional[Dict[str, Any]]
	selector_template: Dict[str, Any]
	scraper_created: bool
	products_extracted: List[Dict[str, Any]]
	
	# Analysis results
	performance_analysis: Optional[Dict[str, Any]]
	validation_results: Dict[str, Any]
	improvement_suggestions: Optional[Dict[str, Any]]
	
	# Output
	final_results: Optional[Dict[str, Any]]
	errors: List[str]
	success: bool


# Map tool names to direct callables from app.py
TOOLS: Dict[str, Any] = {
	"get_html": get_html,
	"readsummary": readsummary,
	"readHTML": readHTML,
	"scrape": scrape,
	"set_selector": set_selector,
	"get_available_fields": get_available_fields,
	"save_to_DB": save_to_DB,
	"get_selector_performance_tool": get_selector_performance_tool,
	"validate_price_selectors_tool": validate_price_selectors_tool,
	"validate_rating_selectors_tool": validate_rating_selectors_tool,
	"validate_review_selectors_tool": validate_review_selectors_tool,
	"validate_name_selectors_tool": validate_name_selectors_tool,
	"get_selector_validation_report_tool": get_selector_validation_report_tool,
	"get_selector_improvement_suggestions_tool": get_selector_improvement_suggestions_tool,
	"get_comprehensive_selector_analysis_tool": get_comprehensive_selector_analysis_tool,
	"export_selector_analysis_to_json_tool": export_selector_analysis_to_json_tool,
	"print_selector_validation_summary_tool": print_selector_validation_summary_tool,
}


def _build_fallback_selectors(platform_name: str) -> Dict[str, Dict[str, Any]]:
	"""Platform-aware fallback selectors for core e-commerce fields."""
	platform = (platform_name or "generic").lower()
	# Flipkart
	if "flipkart" in platform:
		return {
			"product_container": {"field": "product_container", "selector_type": "css", "selectors": ["div[data-id]"]},
			"name": {"field": "name", "selector_type": "css", "selectors": ["a.s1Q9rs", "div._4rR01T", "a.IRpwTa", "div.KzDlHZ", "a[title]"]},
			"current_price": {"field": "current_price", "selector_type": "css", "selectors": ["div._30jeq3._16Jk6d", "div._30jeq3", "div.Nx9bqj"]},
			"original_price": {"field": "original_price", "selector_type": "css", "selectors": ["div._3I9_wc._27UcVY", "div.yRaY8j", "div._3I9_wc", "span[aria-hidden='true'] span._3I9_wc"]},
			"rating": {"field": "rating", "selector_type": "css", "selectors": ["div._3LWZlK", "span._1lRcqv", "div.XQDdHH"]},
			"reviews": {"field": "reviews", "selector_type": "css", "selectors": ["span._2_R_DZ", "span._2_R_DZ span", "span.Wphh3N"]},
			"discount": {"field": "discount", "selector_type": "css", "selectors": ["div._3Ay6Sb span", "div.UkUFwK span", "span[class*='discount']"]},
			"offers": {"field": "offers", "selector_type": "css", "selectors": ["div[class*='offer']", "span[class*='offer']", "span[class*='coupon']"]},
		}

	# Ajio
	if "ajio" in platform:
		return {
			"product_container": {"field": "product_container", "selector_type": "css", "selectors": ["div[class*='product']", "li[class*='product']", "div[itemprop='itemListElement']", "li[id^='pid_']", "article"]},
			"name": {"field": "name", "selector_type": "css", "selectors": ["a[title]", "div[class*='name']", "h2", "h3"]},
			"current_price": {"field": "current_price", "selector_type": "css", "selectors": ["span[class*='price']", "div[class*='price'] span", "[data-price]"]},
			"original_price": {"field": "original_price", "selector_type": "css", "selectors": ["span[class*='mrp']", "span.strike", "div[class*='price'] s"]},
			"rating": {"field": "rating", "selector_type": "css", "selectors": ["span[class*='rating']", "[aria-label*='out of']"]},
			"reviews": {"field": "reviews", "selector_type": "css", "selectors": ["span[class*='ratings']"]},
			"discount": {"field": "discount", "selector_type": "css", "selectors": ["span[class*='discount']", "span:contains(% off)"]},
			"offers": {"field": "offers", "selector_type": "css", "selectors": ["div[class*='offer']", "span[class*='coupon']"]},
		}

	# Myntra
	if "myntra" in platform:
		return {
			"product_container": {"field": "product_container", "selector_type": "css", "selectors": ["li.product-base", "li[data-id]"]},
			"name": {"field": "name", "selector_type": "css", "selectors": ["h3.product-brand", "h4.product-product", "div.product-product"]},
			"current_price": {"field": "current_price", "selector_type": "css", "selectors": ["span.product-discountedPrice", "span.product-price"]},
			"original_price": {"field": "original_price", "selector_type": "css", "selectors": ["span.product-strike", "span.product-mrp"]},
			"rating": {"field": "rating", "selector_type": "css", "selectors": ["div.ratings", "div.ratings-container span", "[aria-label*='out of']"]},
			"reviews": {"field": "reviews", "selector_type": "css", "selectors": ["span.product-ratingsCount"]},
			"discount": {"field": "discount", "selector_type": "css", "selectors": ["span.product-discountPercentage"]},
			"offers": {"field": "offers", "selector_type": "css", "selectors": ["div[class*='offer']", "span[class*='coupon']"]},
		}

	# Amazon
	if "amazon" in platform:
		return {
			"product_container": {"field": "product_container", "selector_type": "css", "selectors": ["div.s-result-item[data-asin]", "div[data-component-type='s-search-result']"]},
			"name": {"field": "name", "selector_type": "css", "selectors": ["h2 a.a-link-normal.a-text-normal span", "h2 a span", "h2 span"]},
			"current_price": {"field": "current_price", "selector_type": "css", "selectors": ["span.a-price span.a-offscreen", "span.a-price-whole", "span.a-offscreen"]},
			"original_price": {"field": "original_price", "selector_type": "css", "selectors": ["span.a-text-price span.a-offscreen", "span.a-price.a-text-price span"]},
			"rating": {"field": "rating", "selector_type": "css", "selectors": ["span.a-icon-alt"]},
			"reviews": {"field": "reviews", "selector_type": "css", "selectors": ["span.a-size-base.s-underline-text", "span[aria-label$='ratings']"]},
			"discount": {"field": "discount", "selector_type": "css", "selectors": ["span.savingsPercentage", "span.a-letter-space+span"]},
			"offers": {"field": "offers", "selector_type": "css", "selectors": ["span.coupon", "span.promo"]},
		}

	# Generic fallback
	return {
		"product_container": {"field": "product_container", "selector_type": "css", "selectors": ["[data-id]", "li", "article", "div"]},
		"name": {"field": "name", "selector_type": "css", "selectors": ["h1", "h2", "h3", "a[title]"]},
		"current_price": {"field": "current_price", "selector_type": "css", "selectors": ["[class*='price']", "[data-price]"]},
		"original_price": {"field": "original_price", "selector_type": "css", "selectors": ["s", ".strike", "[class*='mrp']"]},
		"rating": {"field": "rating", "selector_type": "css", "selectors": ["[aria-label*='out of']"]},
		"reviews": {"field": "reviews", "selector_type": "css", "selectors": ["span:contains(reviews)", "span:contains(ratings)"]},
		"discount": {"field": "discount", "selector_type": "css", "selectors": ["span:contains(% off)", "[class*='discount']"]},
	}


def fetch_html_node(state: ScrapingAgentState) -> ScrapingAgentState:
	"""Step 1: Fetch and analyze HTML content."""
	print(f"🌐 Step 1: Fetching HTML from {state['url']}")
	
	try:
		result = get_html(state['url'])
		if 'error' in result:
			return {
				**state,
				"current_step": "error",
				"errors": state.get("errors", []) + [f"HTML fetch failed: {result['error']}"] ,
				"success": False
			}
		
		# Probe for actual HTML presence (avoid proceeding with empty content)
		probe = readHTML(1, 1)
		if isinstance(probe, str) and probe.strip().lower().startswith("no html content available"):
			return {
				**state,
				"current_step": "error",
				"errors": state.get("errors", []) + [
					"HTML fetch error: No HTML content available. If Playwright was just installed/updated, run 'playwright install' to download browsers or disable JS rendering."
				],
				"success": False
			}
		
		# Get summary data
		summary_result = readsummary()
		summary_data = summary_result if isinstance(summary_result, dict) else {}
		
		new_state = {
			**state,
			"current_step": "analyze_html",
			"completed_steps": state.get("completed_steps", []) + ["fetch_html"],
			"html_content": "HTML content fetched successfully",
			"summary": summary_data,
			"success": True
		}
		print(f"🔍 New state after fetch_html: {new_state}")
		return new_state
	except Exception as e:
		return {
			**state,
			"current_step": "error",
			"errors": state.get("errors", []) + [f"HTML fetch error: {str(e)}"],
			"success": False
		}


def analyze_html_node(state: ScrapingAgentState) -> ScrapingAgentState:
	"""Step 2: Analyze HTML structure and get field hints."""
	print("📊 Step 2: Analyzing HTML structure")
	
	try:
		# Get available fields for selector configuration
		fields_result = get_available_fields()
		available_fields = fields_result.get("available_fields", [])
		print(f"🔍 Raw fields result: {fields_result}")
		
		# Read summary for field hints
		summary_data = readsummary("field_hint_map")
		print(f"🔍 Summary data: {summary_data}")
		
		# Ensure we have fields to work with
		if not available_fields:
			# Fallback to common e-commerce fields if none are detected
			available_fields = [
				"product_container", "name", "current_price", 
				"original_price", "rating", "reviews", "discount", "offers"
			]
			print(f"⚠️ No fields detected from analysis, using default fields: {available_fields}")
		else:
			print(f"✅ Detected {len(available_fields)} fields: {available_fields}")
		
		new_state = {
			**state,
			"current_step": "configure_selectors",
			"completed_steps": state.get("completed_steps", []) + ["analyze_html"],
			"target_fields": available_fields,
			"success": True
		}
		print(f"🔍 New state after analyze_html: {new_state}")
		return new_state
	except Exception as e:
		print(f"❌ Error in analyze_html_node: {e}")
		return {
			**state,
			"current_step": "error",
			"errors": state.get("errors", []) + [f"HTML analysis error: {str(e)}"],
			"success": False
		}


def configure_selectors_node(state: ScrapingAgentState) -> ScrapingAgentState:
	"""Step 3: Configure selectors for target fields."""
	print("⚙️ Step 3: Configuring selectors")
	
	try:
		print("🤖 Generating selectors with model and merging fallbacks...")
		# Guard model generation; on any failure, fall back to platform templates only
		try:
			selector_configs = generate_selectors_with_model(state.get("url", "")) or {}
		except Exception as _e:
			print(f"[WARN] Model selector generation failed: {_e}. Falling back to templates only.")
			selector_configs = {}
		if selector_configs:
			print("🔧 Model returned selectors for fields:", list(selector_configs.keys()))
		else:
			print("⚠️ Model did not return selectors; starting with empty config.")
			selector_configs = {}

		fallbacks = _build_fallback_selectors(state.get("platform_name", "generic"))
		required = ["product_container","name","current_price","original_price","rating","reviews","discount"]
		for rf in required:
			cfg = selector_configs.get(rf)
			if not isinstance(cfg, dict) or not cfg.get("selectors"):
				selector_configs[rf] = fallbacks.get(rf, {})

		# Final must-have
		pcfg = selector_configs.get("product_container", {})
		if not isinstance(pcfg, dict) or not pcfg.get("selectors"):
			return {**state, "current_step":"error", "errors": state.get("errors", []) + ["No product_container selectors available"], "success": False}
		
		# Set selectors for each field
		selector_template = {}
		target_fields = state.get("target_fields", [])
		
		# If target_fields is empty, use all available fields from selector_configs
		if not target_fields:
			target_fields = list(selector_configs.keys())
			print(f"⚠️ No target fields found, using all available fields: {target_fields}")
		
		for field, config in selector_configs.items():
			if field in target_fields:
				print(f"🔧 Configuring selectors for field: {field}")
				stype = (config.get("selector_type") or config.get("type") or "css").lower()
				selectors_list = config.get("selectors", [])
				if stype == "css" and any(str(s).strip().startswith(("//", ".//")) for s in selectors_list):
					stype = "xpath"
				result = set_selector(
					config.get("field", field),
					stype,
					selectors_list
				)
				if "error" not in result:
					selector_template[field] = result.get("template", {}).get(field, {})
					print(f"✅ Successfully configured {field} selectors")
				else:
					print(f"❌ Failed to configure {field} selectors: {result.get('error', 'Unknown error')}")
			else:
				print(f"⏭️ Skipping {field} - not in target fields")
		
		return {
			**state,
			"current_step": "create_scraper",
			"completed_steps": state.get("completed_steps", []) + ["configure_selectors"],
			"selector_template": selector_template,
			"success": True
		}
	except Exception as e:
		return {
			**state,
			"current_step": "error",
			"errors": state.get("errors", []) + [f"Selector configuration error: {str(e)}"],
			"success": False
		}


def create_scraper_node(state: ScrapingAgentState) -> ScrapingAgentState:
	"""Step 4: Create scraper instance."""
	print("🏗️ Step 4: Creating scraper")
	
	try:
		result = scrape(state["selector_template"], state["platform_name"])
		if "error" in result:
			return {
				**state,
				"current_step": "error",
				"errors": state.get("errors", []) + [f"Scraper creation failed: {result['error']}"],
				"success": False
			}
		
		return {
			**state,
			"current_step": "extract_products",
			"completed_steps": state.get("completed_steps", []) + ["create_scraper"],
			"scraper_created": True,
			"success": True
		}
	except Exception as e:
		return {
			**state,
			"current_step": "error",
			"errors": state.get("errors", []) + [f"Scraper creation error: {str(e)}"],
			"success": False
		}


def extract_products_node(state: ScrapingAgentState) -> ScrapingAgentState:
	"""Step 5: Extract product data."""
	print("📦 Step 5: Extracting products")
	
	try:
		# Import the global scraper object from app.py
		from AgentModule.app import GenericPlatformScraperObj
		
		products = []
		if GenericPlatformScraperObj is not None:
			print("🔍 Extracting products using the scraper...")
			products = GenericPlatformScraperObj.scrape()
			print(f"✅ Successfully extracted {len(products)} products")
			
			# Show sample products
			if products:
				print("📦 Sample products:")
				for i, product in enumerate(products[:3]):  # Show first 3 products
					print(f"   {i+1}. {product.get('name', 'N/A')[:50]}...")
					print(f"      Price: {product.get('current_price', 'N/A')}")
					print(f"      Rating: {product.get('rating', 'N/A')}")
		else:
			print("⚠️ No scraper object available for product extraction")
		
		return {
			**state,
			"current_step": "analyze_performance",
			"completed_steps": state.get("completed_steps", []) + ["extract_products"],
			"products_extracted": products,
			"success": True
		}
	except Exception as e:
		print(f"❌ Error extracting products: {e}")
		return {
			**state,
			"current_step": "error",
			"errors": state.get("errors", []) + [f"Product extraction error: {str(e)}"],
			"success": False
		}


def analyze_performance_node(state: ScrapingAgentState) -> ScrapingAgentState:
	"""Step 6: Analyze selector performance."""
	print("📊 Step 6: Analyzing performance")
	
	try:
		performance_result = get_selector_performance_tool()
		validation_results = {}
		
		# Run field-specific validations
		validation_results["price"] = validate_price_selectors_tool()
		validation_results["rating"] = validate_rating_selectors_tool()
		validation_results["review"] = validate_review_selectors_tool()
		validation_results["name"] = validate_name_selectors_tool()
		
		# Get improvement suggestions
		improvement_result = get_selector_improvement_suggestions_tool()
		
		return {
			**state,
			"current_step": "generate_report",
			"completed_steps": state.get("completed_steps", []) + ["analyze_performance"],
			"performance_analysis": performance_result,
			"validation_results": validation_results,
			"improvement_suggestions": improvement_result,
			"success": True
		}
	except Exception as e:
		return {
			**state,
			"current_step": "error",
			"errors": state.get("errors", []) + [f"Performance analysis error: {str(e)}"],
			"success": False
		}


def generate_report_node(state: ScrapingAgentState) -> ScrapingAgentState:
	"""Step 7: Generate comprehensive report."""
	print("📋 Step 7: Generating report")
	
	try:
		# Get comprehensive analysis
		comprehensive_analysis = get_comprehensive_selector_analysis_tool()
		
		# Export to JSON
		json_file = export_selector_analysis_to_json_tool("scraping_analysis.json")
		
		# Print summary
		print_selector_validation_summary_tool()
		
		# Safely extract data from comprehensive analysis
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
		
		return {
			**state,
			"current_step": "save_data",
			"completed_steps": state.get("completed_steps", []) + ["generate_report"],
			"final_results": final_results,
			"success": True
		}
	except Exception as e:
		print(f"❌ Error in report generation: {e}")
		# Create a basic report even if comprehensive analysis fails
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
		
		return {
			**state,
			"current_step": "save_data",
			"completed_steps": state.get("completed_steps", []) + ["generate_report"],
			"final_results": final_results,
			"success": True  # Don't fail the entire workflow for report issues
		}


def save_data_node(state: ScrapingAgentState) -> ScrapingAgentState:
	"""Step 8: Save data to database."""
	print("💾 Step 8: Saving data")
	
	try:
		db_result = save_to_DB()
		
		return {
			**state,
			"current_step": "complete",
			"completed_steps": state.get("completed_steps", []) + ["save_data"],
			"success": True
		}
	except Exception as e:
		return {
			**state,
			"current_step": "error",
			"errors": state.get("errors", []) + [f"Data save error: {str(e)}"],
			"success": False
		}


def error_node(state: ScrapingAgentState) -> ScrapingAgentState:
	"""Handle errors and provide summary."""
	print("❌ Error occurred in workflow")
	
	return {
		**state,
		"current_step": "error",
		"success": False
	}


def should_continue(state: ScrapingAgentState) -> Literal["analyze_html", "configure_selectors", "create_scraper", "extract_products", "analyze_performance", "generate_report", "save_data", "error", "complete"]:
	"""Determine next step based on current state."""
	if not state.get("success", True):
		print(f"❌ State indicates failure, returning error")
		return "error"
	
	step = state.get("current_step", "fetch_html")
	print(f"🔍 Current step: {step}, Success: {state.get('success', True)}")
	
	step_mapping = {
		"fetch_html": "analyze_html",
		"analyze_html": "configure_selectors", 
		"configure_selectors": "create_scraper",
		"create_scraper": "extract_products",
		"extract_products": "analyze_performance",
		"analyze_performance": "generate_report",
		"generate_report": "save_data",
		"save_data": "complete",
		"error": "error",
		"complete": "complete"
	}
	
	next_step = step_mapping.get(step, "error")
	print(f"➡️ Next step: {next_step}")
	return next_step


def build_scraping_agent():
	"""Build the complete LangGraph scraping agent."""
	graph = StateGraph(ScrapingAgentState)
	
	# Add nodes
	graph.add_node("fetch_html", fetch_html_node)
	graph.add_node("analyze_html", analyze_html_node)
	graph.add_node("configure_selectors", configure_selectors_node)
	graph.add_node("create_scraper", create_scraper_node)
	graph.add_node("extract_products", extract_products_node)
	graph.add_node("analyze_performance", analyze_performance_node)
	graph.add_node("generate_report", generate_report_node)
	graph.add_node("save_data", save_data_node)
	graph.add_node("error", error_node)
	
	# Add edges
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
	"""Run the complete scraping agent workflow."""
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
	
	print("🚀 Starting Web Scraping Agent")
	print("=" * 60)
	
	result = agent.invoke(initial_state)
	
	print("\n" + "=" * 60)
	print("🎉 Scraping Agent Complete!")
	print("=" * 60)
	
	return result


# Legacy single-tool runner for backward compatibility
def run_agent(tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
	"""Legacy function for single tool execution."""
	if tool not in TOOLS:
		return {"error": f"Unknown tool: {tool}", "available_tools": list(TOOLS.keys())}
	
	tool_fn = TOOLS[tool]
	try:
		result = tool_fn(**args) if isinstance(args, dict) else tool_fn(args)
		return {"tool": tool, "result": result}
	except Exception as e:
		return {"tool": tool, "error": str(e)}


__all__ = [
	"run_scraping_agent",
	"build_scraping_agent", 
	"run_agent",
	"TOOLS",
	"ScrapingAgentState"
]


if __name__ == "__main__":
	import sys
	
	print("🤖 LangGraph Web Scraping Agent")
	print("=" * 50)
	
	# Check if URL and platform are provided as command line arguments
	if len(sys.argv) >= 3:
		url = sys.argv[1]
		platform_name = sys.argv[2]
		print(f"📋 Scraping: {url}")
		print(f"🏪 Platform: {platform_name}")
	elif len(sys.argv) == 2:
		url = sys.argv[1]
		# Try to detect platform from URL
		if "flipkart" in url.lower():
			platform_name = "flipkart"
		elif "amazon" in url.lower():
			platform_name = "amazon"
		elif "ebay" in url.lower():
			platform_name = "ebay"
		else:
			platform_name = "generic"
		print(f"📋 Scraping: {url}")
		print(f"🏪 Platform: {platform_name} (auto-detected)")
	else:
		# Interactive mode - ask user for input
		print("🔗 Enter the URL to scrape:")
		url = input("URL: ").strip()
		if not url:
			url = "https://www.flipkart.com/search?q=phone+case"
			print(f"Using default URL: {url}")
		
		print("\n🏪 Enter the platform name (or press Enter for auto-detection):")
		platform_input = input("Platform: ").strip()
		if platform_input:
			platform_name = platform_input
		else:
			# Auto-detect platform
			if "flipkart" in url.lower():
				platform_name = "flipkart"
			elif "amazon" in url.lower():
				platform_name = "amazon"
			elif "ebay" in url.lower():
				platform_name = "ebay"
			else:
				platform_name = "generic"
			print(f"Auto-detected platform: {platform_name}")
	
	print("\n" + "=" * 50)
	
	# Run the scraping agent
	try:
		print("🚀 Invoking LangGraph agent...")
		result = run_scraping_agent(url, platform_name)
		print(f"🔍 Raw result: {result}")
		print("\n📊 Final Results:")
		print(f"✅ Success: {result.get('success', False)}")
		print(f"📦 Products Found: {len(result.get('products_extracted', []))}")
		print(f"📋 Completed Steps: {', '.join(result.get('completed_steps', []))}")
		
		if result.get('errors'):
			print(f"❌ Errors: {result.get('errors')}")
			
	except Exception as e:
		print(f"❌ Error running agent: {e}")
		import traceback
		traceback.print_exc()
		print("Please check your internet connection and dependencies.")