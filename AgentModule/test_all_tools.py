"""
Comprehensive test client for all MCP tools
This script tests all tools systematically to identify working and failing tools
"""

import asyncio
from fastmcp import Client

async def test_all_tools():
    """Test all MCP tools systematically"""
    
    # Connect to the MCP server
    client = Client("http://127.0.0.1:8000/mcp")
    
    test_results = {
        "working": [],
        "failed": [],
        "errors": []
    }
    
    try:
        async with client:
            print("🔗 Connected to MCP server successfully!")
            print("=" * 60)
            
            # Test 1: Get current state
            print("\n📊 Test 1: get_current_state")
            try:
                result = await client.call_tool("get_current_state", {})
                print(f"✅ SUCCESS: {result}")
                test_results["working"].append("get_current_state")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("get_current_state")
                test_results["errors"].append(f"get_current_state: {e}")
            
            # Test 2: Get HTML
            print("\n🌐 Test 2: get_html")
            try:
                result = await client.call_tool("get_html", {
                    "url": "https://www.rapiddeliveryservices.in/list-of-water-bottle.html"
                })
                print(f"✅ SUCCESS: {result}")
                test_results["working"].append("get_html")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("get_html")
                test_results["errors"].append(f"get_html: {e}")
            
            # Test 3: Read HTML
            print("\n📖 Test 3: readHTML")
            try:
                result = await client.call_tool("readHTML", {
                    "start_line": 1,
                    "end_line": 20
                })
                # Extract data from CallToolResult
                if hasattr(result, 'data') and result.data:
                    lines_retrieved = result.data.get('lines_retrieved', 0)
                    print(f"✅ SUCCESS: Retrieved {lines_retrieved} lines")
                else:
                    print(f"✅ SUCCESS: HTML read completed")
                test_results["working"].append("readHTML")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("readHTML")
                test_results["errors"].append(f"readHTML: {e}")
            
            # Test 4: Read summary
            print("\n📋 Test 4: readsummary")
            try:
                result = await client.call_tool("readsummary", {"field": None})
                # Extract data from CallToolResult
                if hasattr(result, 'data') and result.data:
                    fields_count = len(result.data.get('data', []))
                    print(f"✅ SUCCESS: {fields_count} fields available")
                else:
                    print(f"✅ SUCCESS: Summary read completed")
                test_results["working"].append("readsummary")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("readsummary")
                test_results["errors"].append(f"readsummary: {e}")
            
            # Test 5: Get available fields
            print("\n🔧 Test 5: get_available_fields")
            try:
                result = await client.call_tool("get_available_fields", {})
                print(f"✅ SUCCESS: {result}")
                test_results["working"].append("get_available_fields")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("get_available_fields")
                test_results["errors"].append(f"get_available_fields: {e}")
            
            # Test 6: Set selector
            print("\n⚙️ Test 6: set_selector")
            try:
                result = await client.call_tool("set_selector", {
                    "field": "product_container",
                    "selector_type": "css",
                    "selectors": ["div.col-md-3.col-sm-6"]
                })
                print(f"✅ SUCCESS: Set product_container selector")
                test_results["working"].append("set_selector")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("set_selector")
                test_results["errors"].append(f"set_selector: {e}")
            
            # Test 7: Create scraper
            print("\n🏗️ Test 7: create_scraper")
            try:
                result = await client.call_tool("create_scraper", {
                    "platform_name": "Test Platform"
                })
                print(f"✅ SUCCESS: {result}")
                test_results["working"].append("create_scraper")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("create_scraper")
                test_results["errors"].append(f"create_scraper: {e}")
            
            # Test 8: Extract products
            print("\n📦 Test 8: extract_products")
            try:
                result = await client.call_tool("extract_products", {})
                # Extract data from CallToolResult
                if hasattr(result, 'data') and result.data:
                    product_count = result.data.get('product_count', 0)
                    print(f"✅ SUCCESS: Extracted {product_count} products")
                else:
                    print(f"✅ SUCCESS: Product extraction completed")
                test_results["working"].append("extract_products")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("extract_products")
                test_results["errors"].append(f"extract_products: {e}")
            
            # Test 9: Get selector performance
            print("\n📊 Test 9: get_selector_performance")
            try:
                result = await client.call_tool("get_selector_performance", {})
                print(f"✅ SUCCESS: Performance analysis completed")
                test_results["working"].append("get_selector_performance")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("get_selector_performance")
                test_results["errors"].append(f"get_selector_performance: {e}")
            
            # Test 10: Validate price selectors
            print("\n💰 Test 10: validate_price_selectors")
            try:
                result = await client.call_tool("validate_price_selectors", {})
                print(f"✅ SUCCESS: Price validation completed")
                test_results["working"].append("validate_price_selectors")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("validate_price_selectors")
                test_results["errors"].append(f"validate_price_selectors: {e}")
            
            # Test 11: Validate rating selectors
            print("\n⭐ Test 11: validate_rating_selectors")
            try:
                result = await client.call_tool("validate_rating_selectors", {})
                print(f"✅ SUCCESS: Rating validation completed")
                test_results["working"].append("validate_rating_selectors")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("validate_rating_selectors")
                test_results["errors"].append(f"validate_rating_selectors: {e}")
            
            # Test 12: Validate review selectors
            print("\n💬 Test 12: validate_review_selectors")
            try:
                result = await client.call_tool("validate_review_selectors", {})
                print(f"✅ SUCCESS: Review validation completed")
                test_results["working"].append("validate_review_selectors")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("validate_review_selectors")
                test_results["errors"].append(f"validate_review_selectors: {e}")
            
            # Test 13: Validate name selectors
            print("\n📝 Test 13: validate_name_selectors")
            try:
                result = await client.call_tool("validate_name_selectors", {})
                print(f"✅ SUCCESS: Name validation completed")
                test_results["working"].append("validate_name_selectors")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("validate_name_selectors")
                test_results["errors"].append(f"validate_name_selectors: {e}")
            
            # Test 14: Get selector validation report
            print("\n📋 Test 14: get_selector_validation_report")
            try:
                result = await client.call_tool("get_selector_validation_report", {})
                print(f"✅ SUCCESS: Validation report completed")
                test_results["working"].append("get_selector_validation_report")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("get_selector_validation_report")
                test_results["errors"].append(f"get_selector_validation_report: {e}")
            
            # Test 15: Get selector improvement suggestions
            print("\n💡 Test 15: get_selector_improvement_suggestions")
            try:
                result = await client.call_tool("get_selector_improvement_suggestions", {})
                print(f"✅ SUCCESS: Improvement suggestions completed")
                test_results["working"].append("get_selector_improvement_suggestions")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("get_selector_improvement_suggestions")
                test_results["errors"].append(f"get_selector_improvement_suggestions: {e}")
            
            # Test 16: Get comprehensive selector analysis
            print("\n🔍 Test 16: get_comprehensive_selector_analysis")
            try:
                result = await client.call_tool("get_comprehensive_selector_analysis", {})
                print(f"✅ SUCCESS: Comprehensive analysis completed")
                test_results["working"].append("get_comprehensive_selector_analysis")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("get_comprehensive_selector_analysis")
                test_results["errors"].append(f"get_comprehensive_selector_analysis: {e}")
            
            # Test 17: Export selector analysis to JSON
            print("\n💾 Test 17: export_selector_analysis_to_json")
            try:
                result = await client.call_tool("export_selector_analysis_to_json", {})
                print(f"✅ SUCCESS: Export completed")
                test_results["working"].append("export_selector_analysis_to_json")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("export_selector_analysis_to_json")
                test_results["errors"].append(f"export_selector_analysis_to_json: {e}")
            
            # Test 18: Save to database
            print("\n💾 Test 18: save_to_database")
            try:
                result = await client.call_tool("save_to_database", {})
                print(f"✅ SUCCESS: Database save completed")
                test_results["working"].append("save_to_database")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("save_to_database")
                test_results["errors"].append(f"save_to_database: {e}")
            
            # Test 19: Reset state
            print("\n🔄 Test 19: reset_state")
            try:
                result = await client.call_tool("reset_state", {})
                print(f"✅ SUCCESS: State reset completed")
                test_results["working"].append("reset_state")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                test_results["failed"].append("reset_state")
                test_results["errors"].append(f"reset_state: {e}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        test_results["errors"].append(f"Connection: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Working Tools: {len(test_results['working'])}")
    for tool in test_results["working"]:
        print(f"   - {tool}")
    
    print(f"\n❌ Failed Tools: {len(test_results['failed'])}")
    for tool in test_results["failed"]:
        print(f"   - {tool}")
    
    print(f"\n🔍 Detailed Errors:")
    for error in test_results["errors"]:
        print(f"   - {error}")
    
    print(f"\n📈 Success Rate: {len(test_results['working'])}/{len(test_results['working']) + len(test_results['failed'])} ({len(test_results['working'])/(len(test_results['working']) + len(test_results['failed']))*100:.1f}%)")

if __name__ == "__main__":
    print("🧪 Testing All MCP Tools...")
    asyncio.run(test_all_tools())
