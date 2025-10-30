#!/usr/bin/env python3
"""
Generic Platform Scraper
A flexible scraper that can work with any e-commerce platform by accepting URL and selector configurations.
"""

import csv
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GenericPlatformScraper:
    def __init__(self, html_content: str, selector_config: Dict, site_name: str = "unknown", url: str = None):
        """
        Initialize the generic platform scraper.
        
        Args:
            html_content: HTML content as string (fetched externally)
            selector_config: Dictionary containing selector configurations for each field
            site_name: Name of the site/platform for identification
            url: Optional URL for reference (not used for fetching)
        """
        self.html_content = html_content
        self.selector_config = selector_config
        self.site_name = site_name
        self.url = url
        self.products = []
        self.soup = None
        
        # Fixed CSV columns as per requirements
        self.csv_columns = [
            'index', 'name', 'current_price', 'original_price', 'rating', 
            'reviews', 'discount', 'offers', 'delivery', 'availability', 
            'site', 'scraped_at'
        ]
        
        # Parse HTML immediately
        self._parse_html()
    
    def _parse_html(self):
        """Parse HTML content into BeautifulSoup object"""
        try:
            self.soup = BeautifulSoup(self.html_content, 'html.parser')
            logger.info(f"Successfully parsed HTML for {self.site_name}")
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            self.soup = None
    
    def scrape(self) -> List[Dict]:
        """
        Main scraping method - extracts products from HTML.
        
        Returns:
            List of extracted product dictionaries
        """
        logger.info(f"Starting scrape for {self.site_name}")
        
        try:
            if not self.html_content or not self.soup:
                logger.error("No HTML content to parse")
                return []
            
            # Parse products
            self.products = self.parse_products()
            
            logger.info(f"Successfully scraped {len(self.products)} products from {self.site_name}")
            return self.products
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return []
    
    def parse_products(self) -> List[Dict]:
        """Parse products from HTML using selector configuration"""
        if not self.soup:
            logger.error("No HTML content to parse")
            return []
        
        # Find product containers
        product_containers = self.find_product_containers()
        logger.info(f"Found {len(product_containers)} product containers")
        
        products = []
        for i, container in enumerate(product_containers):
            try:
                product_data = self.extract_product_data(container, i + 1)
                if product_data and self.validate_product_data(product_data):
                    products.append(product_data)
                    logger.info(f"Extracted product {i+1}: {product_data.get('name', 'Unknown')[:50]}...")
                else:
                    logger.warning(f"Product {i+1}: Skipped (validation failed)")
            except Exception as e:
                logger.error(f"Error processing product {i+1}: {e}")
                continue
        
        return products
    
    def find_product_containers(self) -> List[BeautifulSoup]:
        """Find all product containers using the configured selector"""
        containers = []
        
        # Get product container configuration
        container_config = self.selector_config.get('product_container', {})
        selectors = container_config.get('selectors', ['div'])
        
        for selector in selectors:
            try:
                if container_config.get('type') == 'xpath':
                    # Handle XPath selectors using lxml
                    try:
                        from lxml import html
                        lxml_doc = html.fromstring(str(self.soup))
                        elements = lxml_doc.xpath(selector)
                        if elements:
                            # Convert lxml elements back to BeautifulSoup for consistency
                            from bs4 import BeautifulSoup
                            element_strs = [html.tostring(elem, encoding='unicode') for elem in elements]
                            soup_elements = [BeautifulSoup(elem_str, 'html.parser') for elem_str in element_strs]
                            containers.extend(soup_elements)
                            logger.info(f"Found {len(soup_elements)} products using XPath selector: {selector}")
                            break
                    except ImportError:
                        logger.warning("lxml not available for XPath support. Install with: pip install lxml")
                        continue
                else:
                    # CSS selectors
                    elements = self.soup.select(selector)
                    if elements:
                        containers.extend(elements)
                        logger.info(f"Found {len(elements)} products using CSS selector: {selector}")
                        break
            except Exception as e:
                logger.warning(f"Error with selector {selector}: {e}")
                continue
        
        return containers
    
    def extract_product_data(self, container: BeautifulSoup, index: int) -> Dict:
        """Extract product data from a single container"""
        product_data = {
            'index': index,
            'name': 'N/A',
            'current_price': 'N/A',
            'original_price': 'N/A',
            'rating': 'N/A',
            'reviews': 'N/A',
            'discount': 'N/A',
            'offers': 'N/A',
            'delivery': 'N/A',
            'availability': 'N/A',
            'site': self.site_name,
            'scraped_at': datetime.now().isoformat()
        }
        
        # Extract each field using the configured selectors
        for field in ['name', 'current_price', 'original_price', 'rating', 'reviews', 'discount', 'offers', 'delivery', 'availability']:
            if field in self.selector_config:
                value = self.extract_field(container, field)
                if value:
                    product_data[field] = value
        
        return product_data
    
    def extract_field(self, container: BeautifulSoup, field_name: str) -> str:
        """Extract a specific field using the configured selectors"""
        field_config = self.selector_config.get(field_name, {})
        if not field_config:
            return 'N/A'
        
        selectors = field_config.get('selectors', [])
        field_type = field_config.get('type', 'css')
        attribute = field_config.get('attribute', None)
        regex_pattern = field_config.get('regex', None)
        
        for selector in selectors:
            try:
                if field_type == 'css':
                    value = self.extract_with_css(container, selector, attribute)
                elif field_type == 'xpath':
                    value = self.extract_with_xpath(container, selector, attribute)
                elif field_type == 'regex':
                    value = self.extract_with_regex(container, selector, regex_pattern)
                else:
                    value = self.extract_with_css(container, selector, attribute)
                
                if value and value != 'N/A':
                    # Apply regex cleanup if specified
                    if regex_pattern and field_type != 'regex':
                        cleaned_value = self.clean_with_regex(value, regex_pattern)
                        if cleaned_value:
                            return cleaned_value
                    return self.clean_text(value)
                    
            except Exception as e:
                logger.warning(f"Error extracting {field_name} with selector {selector}: {e}")
                continue
        
        return 'N/A'
    
    def extract_with_css(self, container: BeautifulSoup, selector: str, attribute: str = None) -> str:
        """Extract data using CSS selector"""
        try:
            if ':contains(' in selector:
                # Handle :contains() pseudo-selector manually
                text_to_find = selector.split(':contains("')[1].split('")')[0]
                elements = container.find_all(string=re.compile(text_to_find, re.IGNORECASE))
                if elements:
                    parent = elements[0].parent
                    if parent:
                        if attribute:
                            return parent.get(attribute, '').strip()
                        return parent.get_text(strip=True)
                    return elements[0].strip()
            else:
                element = container.select_one(selector)
                if element:
                    if attribute:
                        return element.get(attribute, '').strip()
                    return element.get_text(strip=True)
        except Exception as e:
            logger.warning(f"CSS extraction error: {e}")
        
        return 'N/A'
    
    def extract_with_xpath(self, container: BeautifulSoup, selector: str, attribute: str = None) -> str:
        """Extract data using XPath selector"""
        try:
            # Convert BeautifulSoup to lxml for XPath support
            from lxml import etree, html
            
            # Convert BeautifulSoup element to string and parse with lxml
            element_str = str(container)
            lxml_doc = html.fromstring(element_str)
            
            # Execute XPath query
            results = lxml_doc.xpath(selector)
            
            if results:
                if attribute:
                    # If attribute is specified, get attribute value
                    if hasattr(results[0], 'get'):
                        return results[0].get(attribute, '').strip()
                    else:
                        return str(results[0]).strip()
                else:
                    # Get text content or string representation
                    if hasattr(results[0], 'text_content'):
                        return results[0].text_content().strip()
                    else:
                        return str(results[0]).strip()
            
        except ImportError:
            logger.warning("lxml not available for XPath support. Install with: pip install lxml")
            return 'N/A'
        except Exception as e:
            logger.warning(f"XPath extraction error: {e}")
            return 'N/A'
        
        return 'N/A'
    
    def extract_with_regex(self, container: BeautifulSoup, selector: str, pattern: str = None) -> str:
        """Extract data using regex pattern"""
        try:
            if pattern:
                text_content = container.get_text()
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    return match.group(1) if match.groups() else match.group(0)
        except Exception as e:
            logger.warning(f"Regex extraction error: {e}")
        
        return 'N/A'
    
    def clean_with_regex(self, text: str, pattern: str) -> str:
        """Clean extracted text using regex pattern"""
        try:
            match = re.search(pattern, text)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        except Exception as e:
            logger.warning(f"Regex cleaning error: {e}")
        
        return text
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return 'N/A'
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters
        text = text.replace('\n', ' ').replace('\t', ' ')
        
        return text if text else 'N/A'
    
    def validate_product_data(self, product_data: Dict) -> bool:
        """Validate that product data meets minimum requirements"""
        # Must have at least a name or price
        name = product_data.get('name', '')
        price = product_data.get('current_price', '')
        
        if not name or name == 'N/A':
            if not price or price == 'N/A':
                return False
        
        # Basic length checks
        if name and len(name) < 2:
            return False
        
        return True
    
    def save_to_csv(self, filename: str = None) -> str:
        """Save products to CSV file with fixed column format"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generic_products_{timestamp}.csv"
        
        if not self.products:
            logger.warning("No products to save")
            return filename
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_columns)
                writer.writeheader()
                
                # Flatten offers list for CSV
                for product in self.products:
                    row = product.copy()
                    if isinstance(row.get('offers'), list):
                        row['offers'] = '; '.join(row['offers'])
                    writer.writerow(row)
            
            logger.info(f"Products saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return filename
    
    def save_to_json(self, filename: str = None) -> str:
        """Save products to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generic_products_{timestamp}.json"
        
        if not self.products:
            logger.warning("No products to save")
            return filename
        
        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.products, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"Products saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return filename
    
    def save_to_supabase(self, supabase_url: str, supabase_key: str, table_name: str = "scraped_products") -> Dict[str, Any]:
        """
        Save products to Supabase table
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            table_name: Name of the table to save data to (default: 'scraped_products')
        
        Returns:
            Dictionary with save results and statistics
        """
        if not self.products:
            logger.warning("No products to save to Supabase")
            return {"error": "No products to save", "saved_count": 0}
        
        try:
            # Import supabase client
            from supabase import create_client, Client
            
            # Create Supabase client
            supabase: Client = create_client(supabase_url, supabase_key)
            
            # Prepare data for Supabase (ensure all required fields are present)
            supabase_data = []
            for product in self.products:
                # Create a clean record with all CSV columns
                record = {}
                for column in self.csv_columns:
                    if column in product:
                        # Handle offers list conversion
                        if column == 'offers' and isinstance(product[column], list):
                            record[column] = '; '.join(product[column])
                        else:
                            record[column] = product[column]
                    else:
                        record[column] = 'N/A'
                
                supabase_data.append(record)
            
            # Insert data into Supabase table
            result = supabase.table(table_name).insert(supabase_data).execute()
            
            # Check if insertion was successful
            if hasattr(result, 'data') and result.data:
                saved_count = len(result.data)
                logger.info(f"Successfully saved {saved_count} products to Supabase table '{table_name}'")
                
                return {
                    "success": True,
                    "saved_count": saved_count,
                    "table_name": table_name,
                    "site": self.site_name,
                    "scraped_at": datetime.now().isoformat(),
                    "message": f"Successfully saved {saved_count} products to Supabase"
                }
            else:
                logger.error("Failed to save to Supabase - no data returned")
                return {
                    "success": False,
                    "saved_count": 0,
                    "error": "No data returned from Supabase insertion",
                    "table_name": table_name
                }
                
        except ImportError:
            logger.error("Supabase client not installed. Install with: pip install supabase")
            return {
                "success": False,
                "saved_count": 0,
                "error": "Supabase client not installed. Install with: pip install supabase"
            }
        except Exception as e:
            logger.error(f"Error saving to Supabase: {e}")
            return {
                "success": False,
                "saved_count": 0,
                "error": str(e),
                "table_name": table_name
            }
    
    def get_summary(self) -> str:
        """Get scraping summary"""
        if not self.products:
            return "No products scraped"
        
        total_products = len(self.products)
        products_with_names = len([p for p in self.products if p.get('name') != 'N/A'])
        products_with_prices = len([p for p in self.products if p.get('current_price') != 'N/A'])
        products_with_ratings = len([p for p in self.products if p.get('rating') != 'N/A'])
        
        summary = f"""
        Scraping Summary for {self.site_name}:
        - Total products found: {total_products}
        - Products with names: {products_with_names}
        - Products with prices: {products_with_prices}
        - Products with ratings: {products_with_ratings}
        - URL: {self.url}
        """
        
        return summary.strip()


# Helper functions for configuration management

def create_selector_config(
    product_container: List[str],
    name_selectors: List[str],
    price_selectors: List[str],
    original_price_selectors: List[str] = None,
    rating_selectors: List[str] = None,
    reviews_selectors: List[str] = None,
    discount_selectors: List[str] = None,
    offers_selectors: List[str] = None,
    delivery_selectors: List[str] = None,
    availability_selectors: List[str] = None
) -> Dict:
    """
    Create a selector configuration dictionary from simple lists.
    
    Args:
        product_container: List of CSS selectors for product containers
        name_selectors: List of CSS selectors for product names
        price_selectors: List of CSS selectors for current prices
        original_price_selectors: List of CSS selectors for original prices
        rating_selectors: List of CSS selectors for ratings
        reviews_selectors: List of CSS selectors for review counts
        discount_selectors: List of CSS selectors for discounts
        offers_selectors: List of CSS selectors for offers
        delivery_selectors: List of CSS selectors for delivery info
        availability_selectors: List of CSS selectors for availability
    
    Returns:
        Dictionary with selector configuration
    """
    config = {
        'product_container': {
            'type': 'css',
            'selectors': product_container
        },
        'name': {
            'type': 'css',
            'selectors': name_selectors
        },
        'current_price': {
            'type': 'css',
            'selectors': price_selectors
        }
    }
    
    if original_price_selectors:
        config['original_price'] = {
            'type': 'css',
            'selectors': original_price_selectors
        }
    
    if rating_selectors:
        config['rating'] = {
            'type': 'css',
            'selectors': rating_selectors
        }
    
    if reviews_selectors:
        config['reviews'] = {
            'type': 'css',
            'selectors': reviews_selectors
        }
    
    if discount_selectors:
        config['discount'] = {
            'type': 'css',
            'selectors': discount_selectors
        }
    
    if offers_selectors:
        config['offers'] = {
            'type': 'css',
            'selectors': offers_selectors
        }
    
    if delivery_selectors:
        config['delivery'] = {
            'type': 'css',
            'selectors': delivery_selectors
        }
    
    if availability_selectors:
        config['availability'] = {
            'type': 'css',
            'selectors': availability_selectors
        }
    
    return config


def convert_main_config(main_config: Dict) -> Dict:
    """
    Convert main.py site configuration to generic scraper format.
    
    Args:
        main_config: Configuration from main.py site_configs
    
    Returns:
        Converted configuration for generic scraper
    """
    return {
        'product_container': {
            'type': 'css',
            'selectors': [main_config.get('product_selector', 'div')]
        },
        'name': {
            'type': 'css',
            'selectors': main_config.get('name_selectors', [])
        },
        'current_price': {
            'type': 'css',
            'selectors': main_config.get('price_selectors', [])
        },
        'original_price': {
            'type': 'css',
            'selectors': main_config.get('original_price_selectors', [])
        },
        'rating': {
            'type': 'css',
            'selectors': main_config.get('rating_selectors', [])
        },
        'reviews': {
            'type': 'css',
            'selectors': main_config.get('reviews_selectors', [])
        },
        'discount': {
            'type': 'css',
            'selectors': main_config.get('discount_selectors', [])
        },
        'offers': {
            'type': 'css',
            'selectors': main_config.get('offers_selectors', [])
        }
    }


# Example usage function
def scrape_platform(html_content: str, selector_config: Dict, site_name: str = "unknown") -> str:
    """
    Convenience function to scrape a platform and return CSV filename.
    
    Args:
        html_content: HTML content as string
        selector_config: Selector configuration dictionary
        site_name: Name of the site
    
    Returns:
        Path to saved CSV file
    """
    scraper = GenericPlatformScraper(html_content, selector_config, site_name)
    scraper.scrape()
    csv_file = scraper.save_to_csv()
    print(scraper.get_summary())
    return csv_file

def scrape_and_save_to_supabase(html_content: str, selector_config: Dict, supabase_url: str, supabase_key: str, site_name: str = "unknown", table_name: str = "scraped_products") -> Dict[str, Any]:
    """
    Convenience function to scrape a platform and save to Supabase.
    
    Args:
        html_content: HTML content as string
        selector_config: Selector configuration dictionary
        supabase_url: Supabase project URL
        supabase_key: Supabase API key
        site_name: Name of the site
        table_name: Name of the Supabase table
    
    Returns:
        Dictionary with save results
    """
    scraper = GenericPlatformScraper(html_content, selector_config, site_name)
    scraper.scrape()
    result = scraper.save_to_supabase(supabase_url, supabase_key, table_name)
    print(scraper.get_summary())
    return result
