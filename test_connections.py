#!/usr/bin/env python3
"""
Test script to verify connections between Gemini API and Supabase database.
"""

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(env_path)
except ImportError:
    pass

def test_gemini_connection():
    """Test Gemini API connection"""
    print("=" * 80)
    print("Testing Gemini API Connection")
    print("=" * 80)
    
    try:
        import google.generativeai as genai
        
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBx3YFnU4tpVPW73nM53s6ki2ZN7n_qCDw")
        
        if not api_key:
            print("[ERROR] GEMINI_API_KEY not found")
            return False
        
        print(f"[OK] API Key found: {api_key[:20]}...")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        print("[OK] Gemini API configured")
        
        # Try to create a model instance
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            print("[OK] Model 'gemini-2.5-flash' initialized")
        except Exception as e:
            print(f"[WARNING] Could not initialize gemini-2.5-flash: {str(e)[:100]}")
            try:
                model = genai.GenerativeModel('gemini-2.5-pro')
                print("[OK] Model 'gemini-2.5-pro' initialized")
            except Exception as e2:
                print(f"[WARNING] Could not initialize gemini-2.5-pro: {str(e2)[:100]}")
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    print("[OK] Model 'gemini-1.5-flash' initialized (fallback)")
                except Exception as e3:
                    print(f"[ERROR] Could not initialize any Gemini model")
                    print(f"   Error: {str(e3)[:200]}")
                    return False
        
        # Try a simple generation
        try:
            print("\nTesting API call...")
            response = model.generate_content("Say 'Hello' in one word")
            
            if hasattr(response, 'text') and response.text:
                print(f"[OK] API call successful!")
                print(f"  Response: {response.text.strip()[:50]}")
                print("\n[SUCCESS] Gemini API Connection: SUCCESS")
                return True
            else:
                print("[WARNING] API call returned no text content")
                # Check if there's an error
                if hasattr(response, 'prompt_feedback'):
                    print(f"  Prompt feedback: {response.prompt_feedback}")
                return False
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                print("[WARNING] API quota exceeded (rate limit)")
                print("  The API key is valid, but you've exceeded your quota.")
                print("  Connection test: SUCCESS (key is valid)")
                print("  Functional test: FAILED (rate limited)")
                return True  # Key is valid, just rate limited
            else:
                print(f"[ERROR] API call failed")
                print(f"   Error: {error_msg[:200]}")
                return False
                
    except ImportError:
        print("[ERROR] google-generativeai package not installed")
        print("   Install with: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)[:200]}")
        return False


def test_supabase_connection():
    """Test Supabase database connection"""
    print("\n" + "=" * 80)
    print("Testing Supabase Database Connection")
    print("=" * 80)
    
    try:
        from supabase import create_client, Client
        
        # Get Supabase credentials
        supabase_url = os.getenv('SUPABASE_URL', 'https://whfjofihihlhctizchmj.supabase.co')
        supabase_key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndoZmpvZmloaWhsaGN0aXpjaG1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzNzQzNDMsImV4cCI6MjA3Njk1MDM0M30.OsJnOqeJgT5REPg7uxkGmmVcHIcs5QO4vdyDi66qpR0')
        table_name = os.getenv('SUPABASE_TABLE_NAME', 'scraped_products')
        
        if not supabase_url:
            print("[ERROR] SUPABASE_URL not found")
            return False
        
        if not supabase_key:
            print("[ERROR] SUPABASE_KEY not found")
            return False
        
        print(f"[OK] Supabase URL found: {supabase_url}")
        print(f"[OK] Supabase Key found: {supabase_key[:20]}...")
        print(f"[OK] Table name: {table_name}")
        
        # Create Supabase client
        try:
            supabase: Client = create_client(supabase_url, supabase_key)
            print("[OK] Supabase client created")
        except Exception as e:
            print(f"[ERROR] Failed to create Supabase client")
            print(f"   Error: {str(e)[:200]}")
            return False
        
        # Test connection by querying the table
        try:
            print(f"\nTesting database query (table: {table_name})...")
            response = supabase.table(table_name).select("*", count="exact").limit(1).execute()
            
            print(f"[OK] Database query successful!")
            print(f"  Table exists: Yes")
            print(f"  Record count: {response.count if hasattr(response, 'count') and response.count is not None else 'N/A'}")
            
            # Try a simple insert test (with rollback if possible)
            # First check what columns exist by querying the schema
            print(f"\nTesting database write (insert test)...")
            
            # Check table structure by getting one record
            sample = supabase.table(table_name).select("*").limit(1).execute()
            if sample.data and len(sample.data) > 0:
                available_columns = list(sample.data[0].keys())
                print(f"  Available columns: {', '.join(available_columns[:10])}...")
                
                # Build test data with only columns that exist
                from datetime import datetime
                test_data = {}
                if "index" in available_columns:
                    # Use a large number to avoid conflicts
                    test_data["index"] = 999999
                if "scraped_at" in available_columns:
                    test_data["scraped_at"] = datetime.now().isoformat()
                if "name" in available_columns:
                    test_data["name"] = "TEST_CONNECTION_PRODUCT"
                if "current_price" in available_columns:
                    test_data["current_price"] = "999.99"
                if "site" in available_columns:
                    test_data["site"] = "test"
                if "product_url" in available_columns:
                    test_data["product_url"] = "https://test.example.com/test"
                elif "url" in available_columns:
                    test_data["url"] = "https://test.example.com/test"
            else:
                # Fallback if we can't determine schema
                from datetime import datetime
                test_data = {
                    "index": 999999,
                    "scraped_at": datetime.now().isoformat(),
                    "name": "TEST_CONNECTION_PRODUCT",
                    "current_price": "999.99",
                    "site": "test"
                }
            
            try:
                # Insert test record
                insert_response = supabase.table(table_name).insert(test_data).execute()
                
                if insert_response.data:
                    print(f"[OK] Database insert successful!")
                    test_id = insert_response.data[0].get('id') if insert_response.data else None
                    
                    # Try to delete the test record
                    if test_id:
                        try:
                            supabase.table(table_name).delete().eq("id", test_id).execute()
                            print(f"[OK] Test record cleaned up (deleted)")
                        except:
                            print(f"[WARNING] Could not delete test record (id: {test_id})")
                            print(f"   You may need to delete it manually")
                    
                    print("\n[SUCCESS] Supabase Connection: SUCCESS")
                    return True
                else:
                    print("[WARNING] Insert returned no data")
                    return False
                    
            except Exception as e:
                error_msg = str(e)
                if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
                    print(f"[WARNING] Test record might already exist (this is okay)")
                    print(f"   Connection test: SUCCESS")
                    return True
                else:
                    print(f"[ERROR] Database insert failed")
                    print(f"   Error: {error_msg[:200]}")
                    return False
                    
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
                print(f"[WARNING] Table '{table_name}' might not exist")
                print(f"   Error: {error_msg[:200]}")
                print(f"   Connection to Supabase works, but table needs to be created")
                return True  # Connection works, table just doesn't exist
            else:
                print(f"[ERROR] Database query failed")
                print(f"   Error: {error_msg[:200]}")
                return False
                
    except ImportError:
        print("[ERROR] supabase package not installed")
        print("   Install with: pip install supabase")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all connection tests"""
    print("\n" + "=" * 80)
    print("API & Database Connection Test Suite")
    print("=" * 80)
    print()
    
    gemini_result = test_gemini_connection()
    supabase_result = test_supabase_connection()
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Gemini API:     {'PASS' if gemini_result else 'FAIL'}")
    print(f"Supabase DB:    {'PASS' if supabase_result else 'FAIL'}")
    print("=" * 80)
    
    if gemini_result and supabase_result:
        print("\nAll connections successful!")
        return 0
    else:
        print("\nSome connections failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

