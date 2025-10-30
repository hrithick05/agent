#!/usr/bin/env python3
"""
Flipkart Intelligent Parser V2
Based on HTML structure analysis from out.json
"""

import json
import csv
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlipkartIntelligentParser:
    def __init__(self, html_file_path):
        self.html_file_path = html_file_path
        self.soup = None
        self.products = []
        
        # CSS selectors identified from JSON analysis
        self.selectors = {
            'product_container': 'div[class*="_4WELSP"]',  # Product image container
            'product_link': 'a[class*="DMMoT0"]',  # Product link
            'product_title': 'a[class*="wjcEIp"]',  # Product title link
            'product_image': 'img[class*="DByuf4"]',  # Product image
            'current_price': 'div[class*="Nx9bqj"]',  # Current price
            'original_price': 'div[class*="yRaY8j"]',  # Original price
            'discount': 'div[class*="UkUFwK"] span',  # Discount percentage
            'rating': 'div[class*="XQDdHH"]',  # Rating container
            'rating_count': 'span[class*="Wphh3N"]',  # Rating count
            'wishlist': 'div[class*="+7E521"]',  # Wishlist button
        }
        
        # Alternative selectors for robustness
        self.alternative_selectors = {
            'product_container': [
                'div[class*="_4WELSP"]',
                'div[class*="slAVV4"]',
                'div[class*="hl05eU"]'
            ],
            'product_link': [
                'a[class*="DMMoT0"]',
                'a[class*="wjcEIp"]',
                'a[href*="/p/"]'
            ],
            'product_title': [
                'a[class*="wjcEIp"]',
                'a[title]',
                'a[href*="/p/"]'
            ],
            'product_image': [
                'img[class*="DByuf4"]',
                'img[alt*="Back Cover"]',
                'img[src*="rukminim2.flixcart.com"]'
            ],
            'current_price': [
                'div[class*="Nx9bqj"]',
                'div:contains("₹")',
                'span:contains("₹")'
            ],
            'original_price': [
                'div[class*="yRaY8j"]',
                'div[class*="slAVV4"]'
            ],
            'discount': [
                'div[class*="UkUFwK"] span',
                'span:contains("% off")',
                'div:contains("% off")'
            ],
            'rating': [
                'div[class*="XQDdHH"]',
                'span[class*="Y1HWO0"]',
                'div:contains("★")'
            ],
            'rating_count': [
                'span[class*="Wphh3N"]',
                'span:contains("(")',
                'div:contains("(")'
            ]
        }

    def load_html(self):
        """Load and parse the HTML file"""
        try:
            with open(self.html_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            self.soup = BeautifulSoup(content, 'html.parser')
            logger.info(f"Successfully loaded HTML file: {self.html_file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading HTML file: {e}")
            return False

    def extract_product_data(self, product_element):
        """Extract data from a single product element"""
        product_data = {
            'title': '',
            'current_price': '',
            'original_price': '',
            'discount': '',
            'rating': '',
            'rating_count': '',
            'image_url': '',
            'product_url': '',
            'wishlist_available': False
        }
        
        try:
            # Extract title
            title_element = product_element.find('a', class_=lambda x: x and 'wjcEIp' in x)
            if not title_element:
                title_element = product_element.find('a', href=lambda x: x and '/p/' in x)
            
            if title_element:
                product_data['title'] = title_element.get('title', '').strip()
                if not product_data['title']:
                    product_data['title'] = title_element.get_text(strip=True)
                product_data['product_url'] = title_element.get('href', '')

            # Extract image
            img_element = product_element.find('img', class_=lambda x: x and 'DByuf4' in x)
            if not img_element:
                img_element = product_element.find('img', src=lambda x: x and 'rukminim2.flixcart.com' in x)
            
            if img_element:
                product_data['image_url'] = img_element.get('src', '')
                if not product_data['title'] and img_element.get('alt'):
                    product_data['title'] = img_element.get('alt', '').strip()

            # Extract price information
            price_container = product_element.find('div', class_=lambda x: x and 'hl05eU' in x)
            if price_container:
                # Current price
                current_price = price_container.find('div', class_=lambda x: x and 'Nx9bqj' in x)
                if current_price:
                    product_data['current_price'] = current_price.get_text(strip=True)
                
                # Original price
                original_price = price_container.find('div', class_=lambda x: x and 'yRaY8j' in x)
                if original_price:
                    product_data['original_price'] = original_price.get_text(strip=True)
                
                # Discount
                discount = price_container.find('div', class_=lambda x: x and 'UkUFwK' in x)
                if discount:
                    discount_span = discount.find('span')
                    if discount_span:
                        product_data['discount'] = discount_span.get_text(strip=True)

            # Extract rating information
            rating_container = product_element.find('div', class_=lambda x: x and '_5OesEi' in x and 'afFzxY' in x)
            if rating_container:
                # Rating
                rating_span = rating_container.find('span', class_=lambda x: x and 'Y1HWO0' in x)
                if rating_span:
                    rating_div = rating_span.find('div', class_=lambda x: x and 'XQDdHH' in x)
                    if rating_div:
                        rating_text = rating_div.get_text(strip=True)
                        # Extract numeric rating
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            product_data['rating'] = rating_match.group(1)
                
                # Rating count
                rating_count = rating_container.find('span', class_=lambda x: x and 'Wphh3N' in x)
                if rating_count:
                    product_data['rating_count'] = rating_count.get_text(strip=True)

            # Check for wishlist button
            wishlist_button = product_element.find('div', class_=lambda x: x and '+7E521' in x)
            if wishlist_button:
                product_data['wishlist_available'] = True

        except Exception as e:
            logger.warning(f"Error extracting product data: {e}")
        
        return product_data

    def find_product_containers(self):
        """Find all product containers using multiple strategies"""
        containers = []
        
        # Strategy 1: Look for specific class patterns
        for selector in self.alternative_selectors['product_container']:
            elements = self.soup.select(selector)
            if elements:
                containers.extend(elements)
                logger.info(f"Found {len(elements)} products using selector: {selector}")
        
        # Strategy 2: Look for product links
        product_links = self.soup.find_all('a', href=lambda x: x and '/p/' in x)
        for link in product_links:
            # Find the parent container
            container = link.find_parent('div')
            if container and container not in containers:
                containers.append(container)
        
        # Strategy 3: Look for price containers
        price_containers = self.soup.find_all('div', class_=lambda x: x and 'hl05eU' in x)
        for price_container in price_containers:
            # Find the parent product container
            container = price_container.find_parent('div')
            if container and container not in containers:
                containers.append(container)
        
        # Remove duplicates
        unique_containers = []
        seen = set()
        for container in containers:
            container_id = id(container)
            if container_id not in seen:
                seen.add(container_id)
                unique_containers.append(container)
        
        logger.info(f"Total unique product containers found: {len(unique_containers)}")
        return unique_containers

    def parse_products(self):
        """Parse all products from the HTML"""
        if not self.soup:
            logger.error("HTML not loaded. Call load_html() first.")
            return []
        
        logger.info("Starting product parsing...")
        
        # Find all product containers
        product_containers = self.find_product_containers()
        
        if not product_containers:
            logger.warning("No product containers found. Trying alternative approach...")
            # Try to find any divs that might contain product information
            all_divs = self.soup.find_all('div')
            for div in all_divs:
                if self.is_product_container(div):
                    product_containers.append(div)
        
        logger.info(f"Found {len(product_containers)} product containers")
        
        # Extract data from each container
        for i, container in enumerate(product_containers):
            try:
                product_data = self.extract_product_data(container)
                
                # Only add if we have meaningful data
                if (product_data['title'] or product_data['current_price'] or 
                    product_data['image_url'] or product_data['product_url']):
                    product_data['product_id'] = f"product_{i+1}"
                    self.products.append(product_data)
                    logger.info(f"Extracted product {i+1}: {product_data['title'][:50]}...")
                else:
                    logger.warning(f"Product {i+1} has no meaningful data")
                    
            except Exception as e:
                logger.error(f"Error processing product {i+1}: {e}")
                continue
        
        logger.info(f"Successfully parsed {len(self.products)} products")
        return self.products

    def is_product_container(self, element):
        """Check if an element is likely a product container"""
        if not element:
            return False
        
        # Check for product-related classes
        class_attr = element.get('class', [])
        if isinstance(class_attr, str):
            class_attr = [class_attr]
        
        product_indicators = [
            '_4WELSP', 'slAVV4', 'hl05eU', 'DMMoT0', 'wjcEIp'
        ]
        
        for indicator in product_indicators:
            if any(indicator in cls for cls in class_attr):
                return True
        
        # Check for product links
        if element.find('a', href=lambda x: x and '/p/' in x):
            return True
        
        # Check for price information
        if element.find('div', class_=lambda x: x and 'Nx9bqj' in x):
            return True
        
        return False

    def save_to_csv(self, filename=None):
        """Save products to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flipkart_products_{timestamp}.csv"
        
        if not self.products:
            logger.warning("No products to save")
            return None
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'product_id', 'title', 'current_price', 'original_price', 
                    'discount', 'rating', 'rating_count', 'image_url', 
                    'product_url', 'wishlist_available'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.products)
            
            logger.info(f"Products saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return None

    def save_to_json(self, filename=None):
        """Save products to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flipkart_products_{timestamp}.json"
        
        if not self.products:
            logger.warning("No products to save")
            return None
        
        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.products, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"Products saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return None

    def get_summary(self):
        """Get parsing summary"""
        if not self.products:
            return "No products parsed"
        
        total_products = len(self.products)
        products_with_titles = len([p for p in self.products if p['title']])
        products_with_prices = len([p for p in self.products if p['current_price']])
        products_with_images = len([p for p in self.products if p['image_url']])
        products_with_ratings = len([p for p in self.products if p['rating']])
        
        summary = f"""
Parsing Summary:
- Total products found: {total_products}
- Products with titles: {products_with_titles}
- Products with prices: {products_with_prices}
- Products with images: {products_with_images}
- Products with ratings: {products_with_ratings}
        """
        
        return summary.strip()

def main():
    """Main function to run the parser"""
    html_file = "pages/flipkart_phoneCase_search.html"
    
    # Initialize parser
    parser = FlipkartIntelligentParser(html_file)
    
    # Load HTML
    if not parser.load_html():
        logger.error("Failed to load HTML file")
        return
    
    # Parse products
    products = parser.parse_products()
    
    if not products:
        logger.warning("No products found")
        return
    
    # Save results
    csv_file = parser.save_to_csv()
    json_file = parser.save_to_json()
    
    # Print summary
    print(parser.get_summary())
    
    if csv_file:
        print(f"CSV file saved: {csv_file}")
    if json_file:
        print(f"JSON file saved: {json_file}")

if __name__ == "__main__":
    main()
