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
        
        # Headless mode (بدون باز کردن پنجره مرورگر)
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # User-Agent برای جلوگیری از شناسایی به عنوان bot
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        
        # تنظیمات اضافی
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # نصب و راه‌اندازی خودکار ChromeDriver
        service = Service(ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # مخفی کردن ویژگی webdriver
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
            
            # صبر برای لود شدن المان خاص (اگر مشخص شده باشد)
            if wait_for_selector:
                print(f"⏳ Waiting for element: {wait_for_selector}")
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                )
            else:
                # صبر کلی برای لود شدن صفحه
                time.sleep(3)
            
            # اسکرول کردن برای لود شدن lazy-loaded images
            self._scroll_page()
            
            html = self.driver.page_source
            print("✅ Page loaded successfully")
            
            return html
            
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            return ""
    
    def _scroll_page(self):
        """Scroll page to load lazy-loaded content"""
        try:
            # اسکرول تدریجی به پایین صفحه
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # اسکرول به پایین
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # محاسبه ارتفاع جدید
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # اگر ارتفاع تغییر نکرد، یعنی به انتهای صفحه رسیدیم
                if new_height == last_height:
                    break
                    
                last_height = new_height
            
            # اسکرول به بالا
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            
        except Exception as e:
            print(f"⚠️ Scroll error (non-critical): {e}")
    
    def save_to_csv(self, data: List[Dict], filename: str):
        """Save scraped data to CSV file"""
        if not data:
            print("⚠️ No data to save")
            return
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ Data saved to {filename}")
    
    def __del__(self):
        """Cleanup: close driver when object is destroyed"""
        self._close_driver()