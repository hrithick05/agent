#!/usr/bin/env python3
"""
Simple HTML Analysis Function
Usage example for the analyze_html_file function.
"""

import sys
import os
from summarzer.main import analyze_html_file

def main():
    """Example usage of the analyze_html_file function"""
    
    # Example 1: Basic usage
    print("🔍 Example 1: Basic HTML Analysis")
    print("=" * 50)
    
    html_file = r"D:\crawlBot\pages\amazon_fridge_search.html"
    
    if os.path.exists(html_file):
        try:
            # Simple function call - just like your command line usage
            output_file = analyze_html_file(html_file)
            print(f"✅ Analysis saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print(f"❌ HTML file not found: {html_file}")
    
    print()
    
    # Example 2: Custom output file
    print("🔍 Example 2: Custom Output File")
    print("=" * 50)
    
    if os.path.exists(html_file):
        try:
            # Custom output file
            output_file = analyze_html_file(
                html_file_path=html_file,
                output_file="custom_analysis.json",
                top_n=30
            )
            print(f"✅ Custom analysis saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print(f"❌ HTML file not found: {html_file}")
    
    print()
    
    # Example 3: Function usage in your code
    print("🔍 Example 3: Using in Your Code")
    print("=" * 50)
    
    def analyze_any_html(html_path: str) -> str:
        """Helper function to analyze any HTML file"""
        return analyze_html_file(html_path, f"analysis_{os.path.basename(html_path)}.json")
    
    if os.path.exists(html_file):
        try:
            result = analyze_any_html(html_file)
            print(f"✅ Helper function result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print(f"❌ HTML file not found: {html_file}")

if __name__ == "__main__":
    main()
