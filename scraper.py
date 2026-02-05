from abc import ABC, abstractmethod
from typing import Dict, List
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time


class BaseRestaurantScraper(ABC):
    """Base class for restaurant scrapers using Selenium"""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.driver = None
    
    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        if self.driver:
            return
        
        chrome_options = Options()
        
        # Headless mode 
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # to prevent being detected as a bot
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        
        # additional settings
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # install and initialize ChromeDriver automatically
        service = Service(ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # hide webdriver feature
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        
        print("✅ Selenium WebDriver initialized")
    
    def _close_driver(self):
        """Close Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("✅ Selenium WebDriver closed")
    
    @abstractmethod
    def scrape_menu(self, restaurant_url: str) -> List[Dict]:
        """Abstract method for scraping menu - must be implemented by subclasses"""
        pass
    
    def fetch_page(self, url: str, wait_for_selector: str = None, wait_time: int = 10) -> str:
        """
        Fetch webpage using Selenium
        
        Args:
            url: URL to fetch
            wait_for_selector: CSS selector to wait for (optional)
            wait_time: Maximum wait time in seconds
            
        Returns:
            HTML content as string
        """
        try:
            self._init_driver()
            
            print(f"🔄 Loading: {url}")
            self.driver.get(url)
            
            # wait for specific element to load (if specified)
            if wait_for_selector:
                print(f"⏳ Waiting for element: {wait_for_selector}")
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                )
            else:
                # wait for page to load
                time.sleep(3)
            
            # scroll to load lazy-loaded images
            self._scroll_page()
            
            html = self.driver.page_source
            print("✅ Page loaded successfully")
            
            return html
            
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
    
    def _scroll_page(self):
        """Scroll page to load lazy-loaded content"""
        try:
            # scroll gradually to the bottom of the page
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # scroll to the bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # calculate new height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # if height didn't change, we've reached the end of the page
                if new_height == last_height:
                    break
                    
                last_height = new_height
            
            # scroll to the top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Scroll error (non-critical): {e}")
    
    def save_to_csv(self, data: List[Dict], filename: str):
        """Save scraped data to CSV file"""
        if not data:
            print("No data to save")
            return
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"Data saved to {filename}")
    
    def __del__(self):
        """Cleanup: close driver when object is destroyed"""
        self._close_driver()