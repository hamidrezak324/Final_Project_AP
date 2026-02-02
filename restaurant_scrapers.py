from scraper import BaseRestaurantScraper
from typing import List, Dict
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time


class SnappFoodScraper(BaseRestaurantScraper):
    """Scraper for Snappfood using Selenium"""
    
    def __init__(self):
        super().__init__("SnappFood", "https://snappfood.ir")
    
    def scrape_menu(self, restaurant_url: str) -> List[Dict]:
        """
        Scrape menu items from a Snappfood restaurant page
        
        Args:
            restaurant_url: Full URL of the restaurant menu page
            
        Returns:
            List of dictionaries containing food items data
        """
        try:
 
            html = self.fetch_page(
                restaurant_url,
                wait_for_selector='[data-testid^="ProductCard-pv:"]',
                wait_time=15
            )
            
            if not html:
                print("❌ Failed to load page")
                return []
            

            soup = BeautifulSoup(html, 'html.parser')
            menu_items = []
            
  
            food_cards = soup.find_all('div', attrs={
                'data-testid': lambda x: x and x.startswith('ProductCard-pv:')
            })
            
            print(f"✅ Found {len(food_cards)} food cards")
            
            for idx, card in enumerate(food_cards, 1):
                try:
                    item = self._parse_food_card(card, idx)
                    if item:
                        menu_items.append(item)
                        
                except Exception as e:
                    print(f"Error parsing card {idx}: {e}")
                    continue
            
            print(f"\n🎉 Successfully scraped {len(menu_items)} items")
            return menu_items
            
        except Exception as e:
            print(f"❌ Fatal error in scrape_menu: {e}")
            return []
        
        finally:

            self._close_driver()
    
    def _parse_food_card(self, card, index: int) -> Dict:
        """Parse a single food card element"""
        

        name = self._extract_name(card)
        if not name:
            print(f"⚠️ [{index}] No name found, skipping")
            return None
        
     
        description = self._extract_description(card)
        
  
        prices = self._extract_prices(card)
        
        if not prices['final_price']:
            print(f"⚠️ [{index}] {name}: No price found, skipping")
            return None
        
        discount = self._extract_discount(card)
        
        stock_info = self._extract_stock(card)
        
        print(f"✅ [{index}] {name}: {prices['final_price']:,} تومان {discount}")
        
        return {
            'restaurant': self.name,
            'food_name': name,
            'description': description,
            'price': prices['final_price'],
            'original_price': prices['original_price'],
            'discount': discount,
            'stock': stock_info,
            'scraped_at': pd.Timestamp.now()
        }
    
    def _extract_name(self, card) -> str:
        """Extract food name from card"""
        name_tag = card.find('h3')
        return name_tag.get_text(strip=True) if name_tag else ""
    
    def _extract_description(self, card) -> str:
        """Extract food description from card"""

        desc_tag = card.find('p', class_=lambda x: x and 'krMlTV' in str(x))
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        return description[:50] if description else ""
    
    def _extract_prices(self, card) -> Dict:
        """Extract prices from card (original and final)"""
        prices = {
            'final_price': 0,
            'original_price': 0
        }
        

        original_price_tag = card.find('p', class_=lambda x: x and 'iZfgtS' in str(x))
        if original_price_tag:
            prices['original_price'] = self._extract_number(original_price_tag.get_text(strip=True))

        final_price_tag = card.find('p', class_=lambda x: x and 'hWPlsu' in str(x))
        if final_price_tag:
            prices['final_price'] = self._extract_number(final_price_tag.get_text(strip=True))
        

        if prices['final_price'] == 0:
            all_price_tags = card.find_all('p', class_=lambda x: x and 'sc-jXbUNg' in str(x))
            for p_tag in all_price_tags:
                price_num = self._extract_number(p_tag.get_text(strip=True))
                if price_num and price_num >= 1000:
                    prices['final_price'] = price_num
                    break
        

        if prices['original_price'] == 0 and prices['final_price'] > 0:
            prices['original_price'] = prices['final_price']
            
        return prices
    
    def _extract_discount(self, card) -> str:
        """Extract discount percentage from card"""

        discount_tag = card.find('span', class_=lambda x: x and 'discount-label__percentage' in str(x))
        
        if discount_tag:
            discount_text = discount_tag.get_text(strip=True)

            discount_match = re.search(r'(\d+)', discount_text)
            if discount_match:
                return f"{discount_match.group(1)}%"
        
        return "0%"
    
    def _extract_stock(self, card) -> str:
        """Extract stock information from card"""

        stock_patterns = [
            r'موجودی\s*(\d+)',
            r'(\d+)\s*عدد\s*موجود',
            r'موجود\s*:\s*(\d+)'
        ]
        
        card_text = card.get_text()
        
        for pattern in stock_patterns:
            match = re.search(pattern, card_text)
            if match:
                return match.group(1)
        
   
        if 'ناموجود' in card_text or 'موجود نیست' in card_text:
            return "0"
        
        return "نامشخص"
    
    def _extract_number(self, text: str) -> int:
        """
        Extract number from Persian/English text
        
        Args:
            text: Text containing numbers (e.g., "185٬000" or "185,000")
            
        Returns:
            Integer number or 0 if not found
        """
        if not text:
            return 0
        

        clean_text = re.sub(r'[^\d۰-۹]', '', text)
        

        persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
        clean_text = clean_text.translate(persian_to_english)

        try:
            return int(clean_text) if clean_text else 0
        except ValueError:
            return 0

    def _close_driver(self):
        """Close the Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("✅ Selenium WebDriver closed")