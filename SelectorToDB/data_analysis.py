#!/usr/bin/env python3
"""
Selector Validation and Data Extraction Analysis
Focus on evaluating whether selectors are working correctly and extracting the right data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import re
from datetime import datetime
import json

class SelectorAnalyzer:
    """Selector validation and data extraction analysis utilities"""
    
    def __init__(self, scraper):
        """
        Initialize with a scraper object
        
        Args:
            scraper: GenericPlatformScraper object with scraped products
        """
        self.scraper = scraper
        self.df = None
        self._prepare_dataframe()
    
    def _prepare_dataframe(self):
        """Convert scraper products to pandas DataFrame"""
        if not self.scraper.products:
            self.df = pd.DataFrame()
            return
        
        self.df = pd.DataFrame(self.scraper.products)
    
    def _is_valid_data(self, value):
        """Check if extracted data is valid (not N/A, not empty)"""
        if pd.isna(value) or value == 'N/A' or value == '' or str(value).strip() == '':
            return False
        return True
    
    def _extract_numeric_value(self, text):
        """Extract numeric value from text for validation"""
        if not self._is_valid_data(text):
            return None
        
        # Extract first number found
        numbers = re.findall(r'\d+\.?\d*', str(text))
        if numbers:
            return float(numbers[0])
        return None

# ============================================================================
# SELECTOR VALIDATION FUNCTIONS
# ============================================================================

def get_selector_performance(scraper) -> Dict[str, Any]:
    """
    Analyze selector performance and data extraction success rates
    
    Args:
        scraper: GenericPlatformScraper object
        
    Returns:
        Dictionary with selector performance metrics
    """
    analyzer = SelectorAnalyzer(scraper)
    
    if analyzer.df.empty:
        return {"error": "No data available for analysis"}
    
    total_products = len(analyzer.df)
    
    # Calculate success rates for each field
    field_performance = {}
    
    for field in ['name', 'current_price', 'original_price', 'rating', 'reviews', 'discount', 'offers', 'delivery', 'availability']:
        if field in analyzer.df.columns:
            valid_count = analyzer.df[field].apply(analyzer._is_valid_data).sum()
            success_rate = (valid_count / total_products) * 100 if total_products > 0 else 0
            
            field_performance[field] = {
                "success_rate": f"{success_rate:.1f}%",
                "valid_extractions": valid_count,
                "total_attempts": total_products,
                "failed_extractions": total_products - valid_count,
                "status": "GOOD" if success_rate >= 80 else "NEEDS_IMPROVEMENT" if success_rate >= 50 else "POOR"
            }
    
    return {
        "total_products": total_products,
        "site": analyzer.df['site'].iloc[0] if not analyzer.df.empty else "unknown",
        "scraped_at": analyzer.df['scraped_at'].iloc[0] if not analyzer.df.empty else None,
        "field_performance": field_performance,
        "overall_success_rate": f"{(sum(field_performance[f]['valid_extractions'] for f in field_performance) / (len(field_performance) * total_products) * 100):.1f}%" if total_products > 0 else "0%"
    }

def validate_price_selectors(scraper) -> Dict[str, Any]:
    """
    Validate price selector performance and data quality
    
    Args:
        scraper: GenericPlatformScraper object
        
    Returns:
        Dictionary with price selector validation results
    """
    analyzer = SelectorAnalyzer(scraper)
    
    if analyzer.df.empty:
        return {"error": "No data available for analysis"}
    
    total_products = len(analyzer.df)
    
    # Current price validation
    current_price_valid = analyzer.df['current_price'].apply(analyzer._is_valid_data).sum()
    current_price_numeric = analyzer.df['current_price'].apply(analyzer._extract_numeric_value).notna().sum()
    
    # Original price validation
    original_price_valid = analyzer.df['original_price'].apply(analyzer._is_valid_data).sum()
    original_price_numeric = analyzer.df['original_price'].apply(analyzer._extract_numeric_value).notna().sum()
    
    # Sample extracted prices for validation
    current_price_samples = analyzer.df[analyzer.df['current_price'].apply(analyzer._is_valid_data)]['current_price'].head(5).tolist()
    original_price_samples = analyzer.df[analyzer.df['original_price'].apply(analyzer._is_valid_data)]['original_price'].head(5).tolist()
    
    return {
        "current_price_selector": {
            "success_rate": f"{(current_price_valid / total_products) * 100:.1f}%",
            "valid_extractions": current_price_valid,
            "numeric_extractions": current_price_numeric,
            "status": "GOOD" if current_price_valid >= total_products * 0.8 else "NEEDS_IMPROVEMENT" if current_price_valid >= total_products * 0.5 else "POOR",
            "sample_data": current_price_samples,
            "recommendation": "Selector working well" if current_price_valid >= total_products * 0.8 else "Consider improving current_price selectors"
        },
        "original_price_selector": {
            "success_rate": f"{(original_price_valid / total_products) * 100:.1f}%",
            "valid_extractions": original_price_valid,
            "numeric_extractions": original_price_numeric,
            "status": "GOOD" if original_price_valid >= total_products * 0.8 else "NEEDS_IMPROVEMENT" if original_price_valid >= total_products * 0.5 else "POOR",
            "sample_data": original_price_samples,
            "recommendation": "Selector working well" if original_price_valid >= total_products * 0.8 else "Consider improving original_price selectors"
        }
    }

def validate_rating_selectors(scraper) -> Dict[str, Any]:
    """
    Validate rating selector performance and data quality
    
    Args:
        scraper: GenericPlatformScraper object
        
    Returns:
        Dictionary with rating selector validation results
    """
    analyzer = SelectorAnalyzer(scraper)
    
    if analyzer.df.empty:
        return {"error": "No data available for analysis"}
    
    total_products = len(analyzer.df)
    
    # Rating validation
    rating_valid = analyzer.df['rating'].apply(analyzer._is_valid_data).sum()
    rating_numeric = analyzer.df['rating'].apply(analyzer._extract_numeric_value).notna().sum()
    
    # Sample extracted ratings for validation
    rating_samples = analyzer.df[analyzer.df['rating'].apply(analyzer._is_valid_data)]['rating'].head(5).tolist()
    
    # Check if ratings are in valid range (0-5)
    valid_ratings = 0
    if rating_numeric > 0:
        numeric_ratings = analyzer.df['rating'].apply(analyzer._extract_numeric_value).dropna()
        valid_ratings = len(numeric_ratings[(numeric_ratings >= 0) & (numeric_ratings <= 5)])
    
    return {
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

def validate_review_selectors(scraper) -> Dict[str, Any]:
    """
    Validate review selector performance and data quality
    
    Args:
        scraper: GenericPlatformScraper object
        
    Returns:
        Dictionary with review selector validation results
    """
    analyzer = SelectorAnalyzer(scraper)
    
    if analyzer.df.empty:
        return {"error": "No data available for analysis"}
    
    total_products = len(analyzer.df)
    
    # Review validation
    review_valid = analyzer.df['reviews'].apply(analyzer._is_valid_data).sum()
    review_numeric = analyzer.df['reviews'].apply(analyzer._extract_numeric_value).notna().sum()
    
    # Sample extracted reviews for validation
    review_samples = analyzer.df[analyzer.df['reviews'].apply(analyzer._is_valid_data)]['reviews'].head(5).tolist()
    
    return {
        "review_selector": {
            "success_rate": f"{(review_valid / total_products) * 100:.1f}%",
            "valid_extractions": review_valid,
            "numeric_extractions": review_numeric,
            "status": "GOOD" if review_valid >= total_products * 0.8 else "NEEDS_IMPROVEMENT" if review_valid >= total_products * 0.5 else "POOR",
            "sample_data": review_samples,
            "recommendation": "Selector working well" if review_valid >= total_products * 0.8 else "Consider improving review selectors"
        }
    }

def validate_name_selectors(scraper) -> Dict[str, Any]:
    """
    Validate name selector performance and data quality
    
    Args:
        scraper: GenericPlatformScraper object
        
    Returns:
        Dictionary with name selector validation results
    """
    analyzer = SelectorAnalyzer(scraper)
    
    if analyzer.df.empty:
        return {"error": "No data available for analysis"}
    
    total_products = len(analyzer.df)
    
    # Name validation
    name_valid = analyzer.df['name'].apply(analyzer._is_valid_data).sum()
    
    # Sample extracted names for validation
    name_samples = analyzer.df[analyzer.df['name'].apply(analyzer._is_valid_data)]['name'].head(5).tolist()
    
    # Check name length (should be reasonable)
    valid_length_names = 0
    if name_valid > 0:
        valid_names = analyzer.df[analyzer.df['name'].apply(analyzer._is_valid_data)]['name']
        valid_length_names = len(valid_names[(valid_names.str.len() >= 5) & (valid_names.str.len() <= 200)])
    
    return {
        "name_selector": {
            "success_rate": f"{(name_valid / total_products) * 100:.1f}%",
            "valid_extractions": name_valid,
            "reasonable_length_extractions": valid_length_names,
            "status": "GOOD" if name_valid >= total_products * 0.8 else "NEEDS_IMPROVEMENT" if name_valid >= total_products * 0.5 else "POOR",
            "sample_data": name_samples,
            "recommendation": "Selector working well" if name_valid >= total_products * 0.8 else "Consider improving name selectors"
        }
    }

# ============================================================================
# COMPREHENSIVE SELECTOR VALIDATION FUNCTIONS
# ============================================================================

def get_selector_validation_report(scraper) -> Dict[str, Any]:
    """
    Get comprehensive selector validation report
    
    Args:
        scraper: GenericPlatformScraper object
        
    Returns:
        Dictionary with complete selector validation results
    """
    analyzer = SelectorAnalyzer(scraper)
    
    if analyzer.df.empty:
        return {"error": "No data available for analysis"}
    
    total_products = len(analyzer.df)
    
    # Get all validation results
    performance = get_selector_performance(scraper)
    price_validation = validate_price_selectors(scraper)
    rating_validation = validate_rating_selectors(scraper)
    review_validation = validate_review_selectors(scraper)
    name_validation = validate_name_selectors(scraper)
    
    # Calculate overall selector health
    field_scores = []
    for field, data in performance.get('field_performance', {}).items():
        success_rate = float(data['success_rate'].replace('%', ''))
        field_scores.append(success_rate)
    
    overall_score = sum(field_scores) / len(field_scores) if field_scores else 0
    
    # Generate recommendations
    recommendations = []
    critical_issues = []
    
    for field, data in performance.get('field_performance', {}).items():
        success_rate = float(data['success_rate'].replace('%', ''))
        if success_rate < 50:
            critical_issues.append(f"{field} selector is failing ({success_rate:.1f}% success rate)")
        elif success_rate < 80:
            recommendations.append(f"Consider improving {field} selectors ({success_rate:.1f}% success rate)")
    
    return {
        "overall_selector_health": {
            "score": f"{overall_score:.1f}%",
            "status": "EXCELLENT" if overall_score >= 90 else "GOOD" if overall_score >= 80 else "NEEDS_IMPROVEMENT" if overall_score >= 60 else "POOR",
            "total_products": total_products,
            "site": analyzer.df['site'].iloc[0] if not analyzer.df.empty else "unknown"
        },
        "field_performance": performance.get('field_performance', {}),
        "detailed_validations": {
            "price_selectors": price_validation,
            "rating_selectors": rating_validation,
            "review_selectors": review_validation,
            "name_selectors": name_validation
        },
        "critical_issues": critical_issues,
        "recommendations": recommendations,
        "analysis_timestamp": datetime.now().isoformat()
    }

def get_selector_improvement_suggestions(scraper) -> Dict[str, Any]:
    """
    Get specific suggestions for improving selectors
    
    Args:
        scraper: GenericPlatformScraper object
        
    Returns:
        Dictionary with improvement suggestions
    """
    analyzer = SelectorAnalyzer(scraper)
    
    if analyzer.df.empty:
        return {"error": "No data available for analysis"}
    
    suggestions = {
        "high_priority": [],
        "medium_priority": [],
        "low_priority": [],
        "sample_failures": {}
    }
    
    # Analyze each field and provide specific suggestions
    for field in ['name', 'current_price', 'original_price', 'rating', 'reviews', 'discount', 'offers']:
        if field in analyzer.df.columns:
            valid_count = analyzer.df[field].apply(analyzer._is_valid_data).sum()
            total_count = len(analyzer.df)
            success_rate = (valid_count / total_count) * 100
            
            # Get sample failures
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
    
    return suggestions

# ============================================================================
# MAIN SELECTOR VALIDATION FUNCTIONS
# ============================================================================

def get_comprehensive_selector_analysis(scraper) -> Dict[str, Any]:
    """
    Get comprehensive selector validation analysis
    
    Args:
        scraper: GenericPlatformScraper object
        
    Returns:
        Dictionary with complete selector analysis
    """
    analysis = {
        "selector_performance": get_selector_performance(scraper),
        "price_validation": validate_price_selectors(scraper),
        "rating_validation": validate_rating_selectors(scraper),
        "review_validation": validate_review_selectors(scraper),
        "name_validation": validate_name_selectors(scraper),
        "validation_report": get_selector_validation_report(scraper),
        "improvement_suggestions": get_selector_improvement_suggestions(scraper),
        "analysis_timestamp": datetime.now().isoformat()
    }
    
    return analysis

def export_selector_analysis_to_json(scraper, filename: str = None) -> str:
    """
    Export comprehensive selector analysis to JSON file
    
    Args:
        scraper: GenericPlatformScraper object
        filename: Optional filename (auto-generated if not provided)
        
    Returns:
        Path to exported JSON file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        site_name = scraper.site_name if hasattr(scraper, 'site_name') else 'unknown'
        filename = f"selector_analysis_{site_name}_{timestamp}.json"
    
    analysis = get_comprehensive_selector_analysis(scraper)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
    
    return filename

def print_selector_validation_summary(scraper):
    """
    Print a summary of the selector validation to console
    
    Args:
        scraper: GenericPlatformScraper object
    """
    analysis = get_comprehensive_selector_analysis(scraper)
    
    print("=" * 80)
    print(f"🔍 SELECTOR VALIDATION SUMMARY - {analysis['selector_performance'].get('site', 'Unknown Site').upper()}")
    print("=" * 80)
    
    # Overall health
    health = analysis['validation_report']['overall_selector_health']
    print(f"\n📊 OVERALL SELECTOR HEALTH:")
    print(f"   Score: {health['score']}")
    print(f"   Status: {health['status']}")
    print(f"   Total Products: {health['total_products']}")
    
    # Field performance
    print(f"\n🎯 FIELD PERFORMANCE:")
    for field, data in analysis['selector_performance']['field_performance'].items():
        status_emoji = "✅" if data['status'] == "GOOD" else "⚠️" if data['status'] == "NEEDS_IMPROVEMENT" else "❌"
        print(f"   {status_emoji} {field.upper()}: {data['success_rate']} ({data['status']})")
    
    # Critical issues
    if analysis['validation_report']['critical_issues']:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in analysis['validation_report']['critical_issues']:
            print(f"   ❌ {issue}")
    
    # Recommendations
    if analysis['validation_report']['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in analysis['validation_report']['recommendations']:
            print(f"   🔧 {rec}")
    
    # High priority improvements
    if analysis['improvement_suggestions']['high_priority']:
        print(f"\n🔥 HIGH PRIORITY IMPROVEMENTS:")
        for improvement in analysis['improvement_suggestions']['high_priority']:
            print(f"   🚨 {improvement['field'].upper()}: {improvement['suggestion']}")
    
    print("\n" + "=" * 80)