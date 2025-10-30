"""
Test script to check if Gemini 2.5 models are available with the provided API key
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import google.generativeai as genai

# Get API key from environment or use the one in langgraph_agent
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyD7prm-HMOvzhFlRGHWc8QxxqQIh66JOGQ")
genai.configure(api_key=GEMINI_API_KEY)

def test_model(model_name: str, test_function_calling: bool = False):
    """Test if a specific model is available and working"""
    print(f"\n{'='*80}")
    print(f"🧪 Testing: {model_name}")
    print(f"{'='*80}")
    
    try:
        # Test 1: Create model instance
        print(f"Step 1: Creating model instance...", end=" ")
        model = genai.GenerativeModel(model_name=model_name)
        print("✅ SUCCESS")
        
        # Test 2: Simple text generation
        print(f"Step 2: Testing text generation...", end=" ")
        response = model.generate_content("Say 'Hello' in one word.")
        
        if response and hasattr(response, 'text') and response.text:
            print(f"✅ SUCCESS")
            print(f"   Response: {response.text.strip()}")
        else:
            print(f"⚠️  WARNING: No text in response")
            return False
        
        # Test 3: Function calling (if requested)
        if test_function_calling:
            print(f"Step 3: Testing function calling...", end=" ")
            try:
                tools = [
                    {
                        "name": "test_function",
                        "description": "A test function",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string", "description": "Test message"}
                            },
                            "required": ["message"]
                        }
                    }
                ]
                
                model_with_tools = genai.GenerativeModel(model_name=model_name, tools=tools)
                response = model_with_tools.generate_content("Call test_function with message 'Hello from Gemini 2.5'")
                
                # Check for function calls
                has_function_call = False
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'function_call'):
                                    has_function_call = True
                                    print(f"✅ SUCCESS")
                                    print(f"   Function called: {part.function_call.name}")
                                    if hasattr(part.function_call, 'args'):
                                        print(f"   Args: {part.function_call.args}")
                                    break
                
                if not has_function_call:
                    print(f"⚠️  No function call detected (may still work)")
                    print(f"   Response text: {response.text[:100] if hasattr(response, 'text') else 'N/A'}")
                    
            except Exception as e:
                print(f"⚠️  Function calling test error: {str(e)[:100]}")
        
        print(f"\n✅ {model_name} is AVAILABLE and WORKING")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ FAILED")
        
        # Provide helpful error messages
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            print(f"   Reason: Model not found in your API account")
            print(f"   This model may not be available for your API key")
        elif "permission" in error_msg.lower() or "quota" in error_msg.lower():
            print(f"   Reason: Permission or quota issue")
        elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
            print(f"   Reason: API key issue")
        else:
            print(f"   Error: {error_msg[:200]}")
        
        return False

def main():
    """Main test function"""
    print("\n" + "="*80)
    print("🚀 Gemini API Model Checker - Testing Gemini 2.5 Access")
    print("="*80)
    print(f"\nAPI Key (first 20 chars): {GEMINI_API_KEY[:20]}...")
    print(f"Full API Key length: {len(GEMINI_API_KEY)} characters")
    print()
    
    # Test models in priority order (Gemini 2.5 first)
    test_models = [
        # Gemini 2.5 models
        ("gemini-2.5-pro", True),
        ("gemini-2.5-flash", True),
        ("gemini-2.5-flash-002", True),
        ("gemini-2.5-pro-latest", True),
        ("gemini-exp-1206", True),  # Gemini 2.5 experimental
        
        # Gemini 2.0 models (fallback)
        ("gemini-2.0-flash-exp", True),
        ("gemini-2.0-flash-thinking-exp-1219", True),
        
        # Gemini 1.5 models (fallback)
        ("gemini-1.5-pro", True),
        ("gemini-1.5-flash", True),
        
        # Legacy models
        ("gemini-pro", False),
        ("gemini-pro-vision", False),
    ]
    
    available_models = []
    gemini_25_models = []
    
    print("Testing models...")
    print("="*80)
    
    for model_name, test_fc in test_models:
        is_gemini_25 = "2.5" in model_name
        success = test_model(model_name, test_function_calling=test_fc)
        
        if success:
            available_models.append(model_name)
            if is_gemini_25:
                gemini_25_models.append(model_name)
            
            # If we found Gemini 2.5, we can stop (optional)
            # But let's test a few more to see what's available
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"\n✅ Available Models: {len(available_models)}")
    print(f"🌟 Gemini 2.5 Models: {len(gemini_25_models)}")
    
    if gemini_25_models:
        print(f"\n🎉 GEMINI 2.5 IS AVAILABLE!")
        print(f"\nAvailable Gemini 2.5 models:")
        for model in gemini_25_models:
            print(f"   ✅ {model}")
        
        print(f"\n💡 Recommended for langgraph_agent.py:")
        print(f"   → Use: '{gemini_25_models[0]}'")
        print(f"   → Best: '{gemini_25_models[-1]}' (likely newest)")
    else:
        print(f"\n⚠️  No Gemini 2.5 models found")
        if available_models:
            print(f"\nAvailable models (fallback options):")
            for model in available_models:
                print(f"   ✓ {model}")
            print(f"\n💡 Recommended: '{available_models[0]}'")
        else:
            print(f"\n❌ No working models found")
            print(f"   Please check your API key and ensure you have access to Gemini models")
    
    print("\n" + "="*80)
    
    # Return results for script usage
    return gemini_25_models if gemini_25_models else available_models

if __name__ == "__main__":
    try:
        results = main()
        sys.exit(0 if results else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
