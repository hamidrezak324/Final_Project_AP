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
    """Scraper for Snappfood using Selenium """
    
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
            print(f"Starting scrape for: {restaurant_url}")
            
            # waiting for ProductCard
            html = self._try_strategy_1(restaurant_url)
            
            if not html:
                # waiting for other elements
                print("Strategy 1 failed, trying Strategy 2...")
                html = self._try_strategy_2(restaurant_url)
            
            if not html:
                # scroll without any strategies
                print("Strategy 2 failed, trying Strategy 3...")
                html = self._try_strategy_3(restaurant_url)
            
            if not html:
                print("All strategies failed to load page")
                return []
            
            print("Page loaded successfully")
            
            # ParsingHTML
            soup = BeautifulSoup(html, 'html.parser')
            menu_items = []
            
            # different strategies for finding food cards
            food_cards = self._find_food_cards(soup)
            
            print(f"Found {len(food_cards)} food cards")
            
            if len(food_cards) == 0:
                print("No food cards found. Saving HTML for debugging...")
                self._save_debug_html(html)
                print("HTML saved to snappfood_debug.html")
                
                # trying to find any related content to food
                menu_items = self._extract_from_any_structure(soup)
            else:
                # parsing found cards
                for idx, card in enumerate(food_cards, 1):
                    try:
                        item = self._parse_food_card(card, idx)
                        if item:
                            menu_items.append(item)
                    except Exception as e:
                        print(f"Error parsing card {idx}: {e}")
                        continue
            
            print(f"\nSuccessfully scraped {len(menu_items)} items")
            return menu_items
            
        except Exception as e:
            print(f"Fatal error in scrape_menu: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        finally:
            self._close_driver()
    
    def _try_strategy_1(self, url: str) -> str:
        """Strategy 1: waiting for ProductCard"""
        try:
            return self.fetch_page(
                url,
                wait_for_selector='[data-testid^="ProductCard"]',
                wait_time=30
            )
        except Exception as e:
            print(f"Strategy 1 error: {e}")
            return ""
    
    def _try_strategy_2(self, url: str) -> str:
        """Strategy 2: waiting for other elements"""
        try:
            self._init_driver()
            print(f"Loading: {url}")
            self.driver.get(url)
            
            # waiting for body
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # scrolling the page
            print("Scrolling page...")
            self._scroll_page()
            
            # additional time for loading
            time.sleep(5)
            
            return self.driver.page_source
            
        except Exception as e:
            print(f"Strategy 2 error: {e}")
            return ""
    
    def _try_strategy_3(self, url: str) -> str:
        """Strategy 3: without any special waiting"""
        try:
            self._init_driver()
            print(f"Loading: {url}")
            self.driver.get(url)
            
            # just wait a little
            time.sleep(10)
            
            # scrolling
            print("Scrolling page")
            for _ in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            return self.driver.page_source
            
        except Exception as e:
            print(f"Strategy 3 error: {e}")
            return ""
    
    def _find_food_cards(self, soup: BeautifulSoup) -> list:
        """Finding food cards with different selectors"""
        
        # selector 1: data-testid containing ProductCard
        cards = soup.find_all('div', attrs={
            'data-testid': lambda x: x and x.startswith('ProductCard')
        })
        if cards:
            print(f" Found {len(cards)} cards with ProductCard testid")
            return cards
    
    def _extract_from_any_structure(self, soup: BeautifulSoup) -> List[Dict]:
        """Extracting food from any structure found"""
        items = []
        
       
        titles = soup.find_all(['h3', 'h4', 'h5'])
        
        print(f"Found {len(titles)} potential food titles")
        
        for title in titles:
            try:
                name = title.get_text(strip=True)
                
                # finding parent div
                parent = title.find_parent('div')
                if not parent:
                    continue
                
                # extracting price from parent
                parent_text = parent.get_text()
                prices = re.findall(r'(\d{1,3}(?:[,٬]\d{3})*)', parent_text)
                
                if not prices:
                    continue
                
                # converting price
                price = self._extract_number(prices[0])
                
                if price >= 1000:  # reasonable price
                    items.append({
                        'restaurant': self.name,
                        'food_name': name,
                        'description': '',
                        'price': price,
                        'original_price': price,
                        'discount': '0%',
                        'stock': 'نامشخص',
                        'scraped_at': pd.Timestamp.now()
                    })
                    print(f"✓ Extracted: {name}: {price:,} تومان")
            
            except Exception as e:
                continue
        
        return items
    
    def _save_debug_html(self, html: str):
        """Save HTML for debugging"""
        try:
            with open('snappfood_debug.html', 'w', encoding='utf-8') as f:
                f.write(html)
        except Exception as e:
            print(f"Error saving debug HTML: {e}")
    
    def _parse_food_card(self, card, index: int) -> Dict:
        """Parse a single food card element"""
        
        # extracting name
        name = self._extract_name(card)
        if not name:
            return None
        
        # extracting description
        description = self._extract_description(card)
        
        # extracting price
        prices = self._extract_prices(card)
        
        if not prices['final_price']:
            print(f"[{index}] {name}: No price found, skipping")
            return None
        
        discount = self._extract_discount(card)
        stock_info = self._extract_stock(card)
        
        print(f"[{index}] {name}: {prices['final_price']:,} تومان {discount}")
        
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
        # searching with different tags
        for tag in ['h3', 'h4', 'h5', 'h2']:
            name_tag = card.find(tag)
            if name_tag:
                return name_tag.get_text(strip=True)
        
        # searching with class
        name_tag = card.find(class_=lambda x: x and 'title' in str(x).lower())
        if name_tag:
            return name_tag.get_text(strip=True)
        
        return ""
    
    def _extract_description(self, card) -> str:
        """Extract food description from card"""
        # searching with different classes
        desc_tag = card.find('p', class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['desc', 'description', 'detail']
        ))
        
        if desc_tag:
            description = desc_tag.get_text(strip=True)
            return description[:100] if description else ""
        
        return ""
    
    def _extract_prices(self, card) -> Dict:
        """Extract prices from card (original and final)"""
        prices = {
            'final_price': 0,
            'original_price': 0
        }
        
        # searching with all p and span tags
        price_tags = card.find_all(['p', 'span', 'div'])
        
        price_candidates = []
        
        for tag in price_tags:
            text = tag.get_text(strip=True)
            price = self._extract_number(text)
            
            # if the number is greater than 1000, it is probably a price
            if price >= 1000:
                price_candidates.append(price)
        
        # removing duplicates
        price_candidates = list(set(price_candidates))
        price_candidates.sort()
        
        if len(price_candidates) == 0:
            return prices
        elif len(price_candidates) == 1:
            prices['final_price'] = price_candidates[0]
            prices['original_price'] = price_candidates[0]
        else:
            # lowest price = final price
            # highest price = original price (before discount)
            prices['final_price'] = price_candidates[0]
            prices['original_price'] = price_candidates[-1]
        
        return prices
    
    def _extract_discount(self, card) -> str:
        """Extract discount percentage from card"""
        # searching in the entire card text
        card_text = card.get_text()
        
        # different discount patterns
        patterns = [
            r'(\d+)\s*%',
            r'٪\s*(\d+)',
            r'(\d+)\s*٪',
            r'تخفیف\s*(\d+)',
            r'discount.*?(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, card_text, re.IGNORECASE)
            if match:
                return f"{match.group(1)}%"
        
        return "0%"
    
    def _extract_stock(self, card) -> str:
        """Extract stock information from card"""
        card_text = card.get_text()
        
        # stock patterns
        stock_patterns = [
            r'موجودی\s*(\d+)',
            r'(\d+)\s*عدد\s*موجود',
            r'موجود\s*:\s*(\d+)'
        ]
        
        for pattern in stock_patterns:
            match = re.search(pattern, card_text)
            if match:
                return match.group(1)
        
        # checking if the food is unavailable
        unavailable_keywords = ['ناموجود', 'موجود نیست', 'اتمام', 'تمام شد']
        if any(keyword in card_text for keyword in unavailable_keywords):
            return "0"
        
        return "نامشخص"
    
    def _extract_number(self, text: str) -> int:
        """
        Extract number from Persian/English text
        
        Args:
            text: Text containing numbers
            
        Returns:
            Integer number or 0 if not found
        """
        if not text:
            return 0
        
        # removing all characters except Persian and English numbers
        clean_text = re.sub(r'[^\d۰-۹]', '', text)
        
        # converting Persian numbers to English
        persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
        clean_text = clean_text.translate(persian_to_english)
        
        try:
            return int(clean_text) if clean_text else 0
        except ValueError:
            return 0

    def _close_driver(self):
        """Close the Selenium WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                print("✅ Selenium WebDriver closed")
            except Exception as e:
                print(f"Error closing driver: {e}")