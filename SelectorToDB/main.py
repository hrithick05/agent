import asyncio
import json
import csv
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional

class UniversalEcommerceScraper:
    def __init__(self):
        self.products = []
        
        # Configuration for different e-commerce sites
        self.site_configs = {
            'amazon': {
                'name': 'Amazon India',
                'url': 'https://www.amazon.in/s?k=fridge+double+door+fridge+5+star',
                'product_selector': 'div[data-component-type="s-search-result"]',
                'name_selectors': [
                    'h2.a-size-medium span',
                    'h2.a-size-medium',
                    'span.a-size-medium'
                ],
                'price_selectors': [
                    'span.a-price-whole',
                    '.a-price .a-price-whole',
                    'span.a-price[data-a-size="xl"]'
                ],
                'original_price_selectors': [
                    'span.a-price.a-text-price',
                    'span.a-text-price'
                ],
                'rating_selectors': [
                    'span.a-size-small.a-color-base',
                    '.a-icon-alt'
                ],
                'reviews_selectors': [
                    'span.a-size-mini',
                    'a[href*="customerReviews"] span'
                ],
                'discount_selectors': [
                    'span:contains("% off")',
                    'span:contains("off")'
                ],
                'offers_selectors': [
                    'span.s-coupon-unclipped',
                    'span.a-color-base:contains("coupon")',
                    'span:contains("back with")'
                ]
            },
            
            'flipkart': {
                'name': 'Flipkart',
                'url': 'https://www.flipkart.com/search?q=phone%20case',
                'product_selector': 'div[class*="_4WELSP"]',  # Main product container
                'name_selectors': [
                    'a[class*="wjcEIp"]',  # Product title link
                    'a[title]',  # Title attribute
                    'img[alt]',  # Image alt text
                    'a[href*="/p/"]'  # Product link
                ],
                'price_selectors': [
                    'div[class*="Nx9bqj"]',  # Current price
                    'div[class*="hl05eU"] div[class*="Nx9bqj"]',  # Price in container
                    'div:contains("₹")',
                    'span:contains("₹")'
                ],
                'original_price_selectors': [
                    'div[class*="yRaY8j"]',  # Original price
                    'div[class*="hl05eU"] div[class*="yRaY8j"]',  # Original price in container
                    'span[class*="strike"]',
                    'del'
                ],
                'rating_selectors': [
                    'div[class*="XQDdHH"]',  # Rating container
                    'span[class*="Y1HWO0"] div[class*="XQDdHH"]',  # Rating in span
                    'div[class*="_5OesEi"] span[class*="Y1HWO0"] div[class*="XQDdHH"]',  # Full rating path
                    'div[class*="star"]',
                    'span[class*="rating"]'
                ],
                'reviews_selectors': [
                    'span[class*="Wphh3N"]',  # Review count
                    'div[class*="_5OesEi"] span[class*="Wphh3N"]',  # Review count in rating container
                    'span:contains("(")',
                    'span:contains("ratings")',
                    'div:contains("ratings")'
                ],
                'discount_selectors': [
                    'div[class*="UkUFwK"] span',  # Discount percentage
                    'div[class*="hl05eU"] div[class*="UkUFwK"] span',  # Discount in price container
                    'span:contains("% off")',
                    'div:contains("% off")'
                ],
                'offers_selectors': [
                    'div[class*="+7E521"]',  # Wishlist button
                    'div[class*="oUss6M"]',  # Wishlist container
                    'div[class*="offer"]',
                    'span[class*="coupon"]',
                    'div:contains("Save")'
                ]
            },
            
            'meesho': {
                'name': 'Meesho',
                'url': 'https://www.meesho.com/search?q=perfumes',
                'product_selector': 'div[class*="product"]',
                'name_selectors': [
                    'div[class*="title"]',
                    'h1', 'h2', 'h3',
                    'span[class*="title"]'
                ],
                'price_selectors': [
                    'span[class*="price"]',
                    'div[class*="price"]',
                    'span[class*="amount"]'
                ],
                'original_price_selectors': [
                    'span[class*="strike"]',
                    'span[class*="original"]'
                ],
                'rating_selectors': [
                    'span[class*="rating"]',
                    'div[class*="star"]',
                    'span[class*="score"]'
                ],
                'reviews_selectors': [
                    'span[class*="review"]',
                    'span:contains("ratings")'
                ],
                'discount_selectors': [
                    'span:contains("% off")',
                    'span:contains("off")'
                ],
                'offers_selectors': [
                    'span[class*="offer"]',
                    'div[class*="coupon"]'
                ]
            },
            
            'sathya': {
                'name': 'Sathya Store',
                'url': 'https://www.sathya.store/search?category=&q=vivo+mobile',
                'product_selector': 'div.product-box',
                'name_selectors': [
                    'a[href*="/category/"]',
                    'img[alt]',
                    'h4',
                    'h3',
                    'div[class*="title"]'
                ],
                'price_selectors': [
                    'h4:contains("₹")',
                    'span:contains("₹")',
                    'div:contains("₹")',
                    'p:contains("₹")'
                ],
                'original_price_selectors': [
                    'span[class*="strike"]',
                    'span[class*="original"]',
                    'del',
                    'span:contains("MRP")',
                    'span:contains("M.R.P")',
                    'div:contains("MRP")',
                    'p:contains("MRP")'
                ],
                'rating_selectors': [
                    'div[class*="star"]',
                    'span[class*="rating"]',
                    'div[class*="review"]',
                    'div[class*="rating"]',
                    'span[class*="score"]',
                    'div[class*="Rating"]'
                ],
                'reviews_selectors': [
                    'span[class*="review"]',
                    'span:contains("ratings")',
                    'div:contains("ratings")',
                    'span:contains("Reviews")',
                    'div:contains("Reviews")',
                    'span[class*="Review"]'
                ],
                'discount_selectors': [
                    'span:contains("% off")',
                    'span:contains("off")',
                    'div:contains("Save")'
                ],
                'offers_selectors': [
                    'span[class*="offer"]',
                    'div[class*="coupon"]',
                    'div:contains("Save")'
                ]
            }
        }
    
    async def scrape_site(self, site_key: str, custom_url: str = None):
        """Scrape products from a specific site"""
        if site_key not in self.site_configs:
            raise ValueError(f"Unknown site: {site_key}. Available: {list(self.site_configs.keys())}")
        
        config = self.site_configs[site_key]
        url = custom_url or config['url']
        
        print(f"\n{'='*60}")
        print(f"🛒 Scraping {config['name']}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        async with AsyncWebCrawler() as crawler:
            try:
                result = await crawler.arun(
                    url=url,
                    wait_for=f'css:{config["product_selector"]}',
                    css_selector=config['product_selector']
                )
                
                if not result.success:
                    print(f"❌ Failed to load {config['name']}")
                    return
                
                print(f"✅ {config['name']} loaded successfully")
                
                # Try both extracted content and full HTML
                if result.extracted_content:
                    await self.parse_products_with_config(result.extracted_content, config, site_key)
                else:
                    print("⚠️ No extracted content, trying full HTML parsing...")
                    await self.parse_products_from_html_with_config(result.html, config, site_key)
                    
            except Exception as e:
                print(f"❌ Error scraping {config['name']}: {e}")
    
    async def parse_products_with_config(self, product_elements: List[str], config: Dict, site_key: str):
        """Parse products using specific configuration"""
        print(f"📄 Found {len(product_elements)} product elements")
        
        for i, element in enumerate(product_elements):
            try:
                soup = BeautifulSoup(element, 'html.parser')
                product_data = self.extract_product_data_with_config(soup, i+1, config, site_key)
                if product_data and self.validate_product_data(product_data, site_key):
                    self.products.append(product_data)
                    print(f"✅ Product {i+1}: {product_data['name'][:50]}...")
                else:
                    print(f"⚠️ Product {i+1}: Skipped (validation failed)")
            except Exception as e:
                print(f"❌ Error parsing product {i+1}: {e}")
    
    async def parse_products_from_html_with_config(self, html_content: str, config: Dict, site_key: str):
        """Parse products from full HTML using configuration"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try different product container selectors
        product_containers = []
        
        # Primary selector
        containers = soup.select(config['product_selector'])
        if containers:
            product_containers = containers
        else:
            # Site-specific fallback selectors
            if site_key == 'flipkart':
                fallback_selectors = [
                    'div[class*="_4WELSP"]',  # Main product container
                    'div[class*="slAVV4"]',   # Alternative container
                    'div[class*="hl05eU"]',   # Price container
                    'div[class*="DMMoT0"]',  # Product link container
                    'a[href*="/p/"]',        # Product links
                    'div[data-id]'            # Generic data-id
                ]
            else:
                # Generic fallback selectors
                fallback_selectors = [
                    'div[class*="product"]',
                    'div[class*="item"]',
                    'div[class*="card"]',
                    'div[data-id]',
                    'div[class*="search"]'
                ]
            
            for selector in fallback_selectors:
                containers = soup.select(selector)
                if containers:
                    product_containers = containers
                    break
        
        print(f"📄 Found {len(product_containers)} product containers in HTML")
        
        for i, container in enumerate(product_containers):
            try:
                product_data = self.extract_product_data_with_config(container, i+1, config, site_key)
                if product_data and self.validate_product_data(product_data, site_key):
                    self.products.append(product_data)
                    print(f"✅ Product {i+1}: {product_data['name'][:50]}...")
                else:
                    print(f"⚠️ Product {i+1}: Skipped (validation failed)")
            except Exception as e:
                print(f"❌ Error parsing product {i+1}: {e}")
    
    def extract_product_data_with_config(self, soup: BeautifulSoup, index: int, config: Dict, site_key: str) -> Optional[Dict]:
        """Extract product data using configuration-based selectors"""
        try:
            # Extract product name - special handling for Sathya Store and Flipkart
            if site_key == 'sathya':
                name = self.extract_sathya_name(soup)
            elif site_key == 'flipkart':
                name = self.extract_flipkart_name(soup)
            else:
                name = self.extract_with_multiple_selectors(soup, config['name_selectors'], 'Product name')
            
            # Extract current price
            current_price = self.extract_with_multiple_selectors(soup, config['price_selectors'], 'Current price')
            
            # Extract original price - special handling for Sathya Store
            if site_key == 'sathya':
                original_price = self.extract_sathya_original_price(soup)
            else:
                original_price = self.extract_with_multiple_selectors(soup, config['original_price_selectors'], 'Original price')
            
            # Extract rating
            rating = self.extract_with_multiple_selectors(soup, config['rating_selectors'], 'Rating')
            
            # Extract reviews
            reviews = self.extract_with_multiple_selectors(soup, config['reviews_selectors'], 'Reviews')
            
            # Extract discount
            discount = self.extract_with_multiple_selectors(soup, config['discount_selectors'], 'Discount')
            
            # Extract offers
            offers = self.extract_offers_with_config(soup, config['offers_selectors'])
            
            # Extract additional info
            delivery = self.extract_delivery_info(soup)
            availability = self.extract_availability(soup)
            
            return {
                'index': index,
                'name': name,
                'current_price': current_price,
                'original_price': original_price,
                'rating': rating,
                'reviews': reviews,
                'discount': discount,
                'offers': offers,
                'delivery': delivery,
                'availability': availability,
                'site': site_key,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error extracting product data: {e}")
            return None
    
    def extract_sathya_name(self, soup: BeautifulSoup) -> str:
        """Special name extraction for Sathya Store"""
        try:
            # Try to get name from image alt attribute first
            img = soup.find('img')
            if img and img.get('alt'):
                alt_text = img.get('alt').strip()
                if alt_text and len(alt_text) > 5 and not alt_text.startswith('₹'):
                    return alt_text
            
            # Try to get name from link href
            link = soup.find('a', href=True)
            if link:
                href = link.get('href', '')
                if '/category/' in href:
                    # Extract product name from URL
                    parts = href.split('/')
                    if len(parts) > 0:
                        name = parts[-1].replace('-', ' ').title()
                        if name and len(name) > 3:
                            return name
            
            # Try to get name from product detail section
            product_detail = soup.find('div', class_='product-detail')
            if product_detail:
                # Look for title in product detail
                title_elem = product_detail.find('h4') or product_detail.find('h3') or product_detail.find('h2')
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if title_text and len(title_text) > 5 and not title_text.startswith('₹'):
                        return title_text
            
            # Try to get name from any text content
            text_content = soup.get_text(strip=True)
            if text_content and len(text_content) > 10:
                # Clean up the text and find the first meaningful line
                lines = text_content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 5 and not line.startswith('₹') and not line.startswith('(') and not line.startswith('Save'):
                        return line
                        
        except Exception as e:
            print(f"Error extracting Sathya name: {e}")
        
        return 'N/A'
    
    def extract_flipkart_name(self, soup: BeautifulSoup) -> str:
        """Special name extraction for Flipkart"""
        try:
            # Try to get name from image alt attribute first (most reliable)
            img = soup.find('img', class_=lambda x: x and 'DByuf4' in x)
            if img and img.get('alt'):
                alt_text = img.get('alt').strip()
                if alt_text and len(alt_text) > 5:
                    return alt_text
            
            # Try to get name from product link title
            link = soup.find('a', class_=lambda x: x and 'wjcEIp' in x)
            if link:
                title = link.get('title', '').strip()
                if title and len(title) > 5:
                    return title
                
                # Try to get text from link
                link_text = link.get_text(strip=True)
                if link_text and len(link_text) > 5:
                    return link_text
            
            # Try to get name from any product link
            product_link = soup.find('a', href=lambda x: x and '/p/' in x)
            if product_link:
                title = product_link.get('title', '').strip()
                if title and len(title) > 5:
                    return title
                
                link_text = product_link.get_text(strip=True)
                if link_text and len(link_text) > 5:
                    return link_text
            
            # Try to get name from any image alt
            img = soup.find('img')
            if img and img.get('alt'):
                alt_text = img.get('alt').strip()
                if alt_text and len(alt_text) > 5:
                    return alt_text
                        
        except Exception as e:
            print(f"Error extracting Flipkart name: {e}")
        
        return 'N/A'
    
    def extract_sathya_original_price(self, soup: BeautifulSoup) -> str:
        """Special original price extraction for Sathya Store (MRP)"""
        try:
            # First try the working selectors from debug
            mrp_selectors = [
                'span:contains("MRP")',
                'div:contains("MRP")',
                'p:contains("MRP")'
            ]
            
            for selector in mrp_selectors:
                if ':contains(' in selector:
                    text_to_find = selector.split(':contains("')[1].split('")')[0]
                    elements = soup.find_all(string=re.compile(text_to_find, re.IGNORECASE))
                    if elements:
                        parent = elements[0].parent
                        if parent:
                            text = parent.get_text(strip=True)
                            # Extract price from MRP text
                            price_match = re.search(r'₹([\d,]+)', text)
                            if price_match:
                                return f"₹{price_match.group(1)}"
            
            # Fallback: Look for MRP in text content
            text_content = soup.get_text(strip=True)
            
            # Search for MRP patterns
            mrp_patterns = [
                r'MRP[:\s]*₹?([\d,]+)',
                r'M\.R\.P[:\s]*₹?([\d,]+)',
                r'₹([\d,]+)\s*\(MRP\)',
                r'₹([\d,]+)\s*\(M\.R\.P\)'
            ]
            
            for pattern in mrp_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    price = match.group(1)
                    return f"₹{price}"
                
        except Exception as e:
            print(f"Error extracting Sathya original price: {e}")
        
        return 'N/A'
    
    def extract_with_multiple_selectors(self, soup: BeautifulSoup, selectors: List[str], field_name: str) -> str:
        """Try multiple selectors to extract data"""
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    # Handle :contains() pseudo-selector manually
                    text_to_find = selector.split(':contains("')[1].split('")')[0]
                    # Find elements that contain the text
                    elements = soup.find_all(string=re.compile(text_to_find, re.IGNORECASE))
                    if elements:
                        # Get the parent element and extract its text
                        parent = elements[0].parent
                        if parent:
                            return parent.get_text(strip=True)
                        return elements[0].strip()
                else:
                    element = soup.select_one(selector)
                    if element:
                        text = element.get_text(strip=True)
                        if text and text != 'N/A' and len(text) > 0:
                            return text
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue
        return 'N/A'
    
    def extract_offers_with_config(self, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
        """Extract offers using configuration"""
        offers = []
        
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    text_to_find = selector.split(':contains("')[1].split('")')[0]
                    elements = soup.find_all(text=re.compile(text_to_find, re.IGNORECASE))
                    for element in elements:
                        if element.strip():
                            offers.append(element.strip())
                else:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(strip=True)
                        if text and text not in offers:
                            offers.append(text)
            except:
                continue
        
        return offers
    
    def extract_delivery_info(self, soup: BeautifulSoup) -> str:
        """Extract delivery information"""
        delivery_selectors = [
            'div[class*="delivery"]',
            'span[class*="delivery"]',
            'div[class*="shipping"]',
            'span:contains("delivery")',
            'span:contains("shipping")'
        ]
        
        for selector in delivery_selectors:
            try:
                if ':contains(' in selector:
                    elements = soup.find_all(text=re.compile('delivery|shipping', re.IGNORECASE))
                    if elements:
                        return elements[0].strip()
                else:
                    element = soup.select_one(selector)
                    if element:
                        return element.get_text(strip=True)
            except:
                continue
        
        return 'N/A'
    
    def extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract availability information"""
        availability_selectors = [
            'span[class*="stock"]',
            'div[class*="availability"]',
            'span:contains("bought")',
            'span:contains("stock")'
        ]
        
        for selector in availability_selectors:
            try:
                if ':contains(' in selector:
                    elements = soup.find_all(text=re.compile('bought|stock|available', re.IGNORECASE))
                    if elements:
                        return elements[0].strip()
                else:
                    element = soup.select_one(selector)
                    if element:
                        return element.get_text(strip=True)
            except:
                continue
        
        return 'N/A'
    
    def validate_product_data(self, product_data: Dict, site_key: str) -> bool:
        """Validate product data based on site"""
        # Basic validation
        if not product_data['name'] or product_data['name'] == 'N/A':
            return False
        
        # Site-specific validation
        if site_key == 'amazon':
            # Amazon products should have reasonable names
            if len(product_data['name']) < 10:
                return False
        
        elif site_key == 'flipkart':
            # Flipkart products should have names
            if len(product_data['name']) < 5:
                return False
        
        elif site_key == 'sathya':
            # Sathya Store - be very lenient, just check if we have some name
            if len(product_data['name']) < 2:
                return False
            # Don't accept price as name
            if product_data['name'].startswith('₹'):
                return False
        
        elif site_key == 'meesho':
            # Meesho might have shorter names, be more lenient
            if len(product_data['name']) < 3:
                return False
        
        return True
    
    def save_to_json(self, filename: str = None) -> str:
        """Save products to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"universal_products_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Products saved to {filename}")
        return filename
    
    def save_to_csv(self, filename: str = None) -> str:
        """Save products to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"universal_products_{timestamp}.csv"
        
        if not self.products:
            print("⚠️ No products to save")
            return filename
        
        # Flatten offers list for CSV
        csv_data = []
        for product in self.products:
            row = product.copy()
            row['offers'] = '; '.join(product['offers']) if product['offers'] else ''
            csv_data.append(row)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if csv_data:
                writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)
        
        print(f"💾 Products saved to {filename}")
        return filename
    
    def print_summary(self):
        """Print scraping summary"""
        print(f"\n📊 Universal Scraping Summary:")
        print(f"   Total products found: {len(self.products)}")
        
        if self.products:
            # Group by site
            by_site = {}
            for product in self.products:
                site = product.get('site', 'unknown')
                if site not in by_site:
                    by_site[site] = []
                by_site[site].append(product)
            
            for site, products in by_site.items():
                print(f"   {site}: {len(products)} products")
            
            print(f"\n🔍 Sample products:")
            for i, product in enumerate(self.products[:5]):
                print(f"   {i+1}. [{product['site']}] {product['name'][:50]}...")
                print(f"      Price: {product['current_price']} | Rating: {product['rating']} | Reviews: {product['reviews']}")

async def main():
    """Main function to demonstrate the universal scraper"""
    scraper = UniversalEcommerceScraper()
    
    # Test different sites
    sites_to_test = ['amazon', 'flipkart', 'meesho', 'sathya']
    
    for site in sites_to_test:
        try:
            await scraper.scrape_site(site)
            await asyncio.sleep(2)  # Delay between sites
        except Exception as e:
            print(f"❌ Error with {site}: {e}")
    
    # Print final summary
    scraper.print_summary()
    
    # Save results
    json_file = scraper.save_to_json()
    csv_file = scraper.save_to_csv()
    
    print(f"\n✅ Universal scraping completed!")
    print(f"📁 Output files:")
    print(f"   📄 JSON: {json_file}")
    print(f"   📊 CSV: {csv_file}")

if __name__ == "__main__":
    asyncio.run(main())