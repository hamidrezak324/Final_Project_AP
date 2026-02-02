"""
Multi-threaded Restaurant Scraper
Scrapes multiple restaurants concurrently using ThreadPoolExecutor
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Type, Callable, Optional
import pandas as pd
from datetime import datetime
import time

class ThreadedRestaurantScraper:
    """
    Multi-threaded scraper for parallel restaurant menu extraction.
    Each thread creates its own scraper instance with its own WebDriver.
    """
    
    def __init__(
        self,
        scraper_class: Type,
        max_workers: int = 3,
        output_file: Optional[str] = None,
        verbose: bool = True
    ):
        """
        Initialize threaded scraper
        
        Args:
            scraper_class: Scraper class to instantiate (e.g., SnappFoodScraper)
            max_workers: Maximum number of concurrent threads (default: 3)
            output_file: Optional CSV filename to save results
            verbose: Whether to print detailed logs (default: True)
        """
        self.scraper_class = scraper_class
        self.max_workers = max_workers
        self.output_file = output_file
        self.verbose = verbose
        self.results = []
        self.errors = []
    
    def _scrape_single_restaurant(
        self, 
        url: str, 
        index: int,
        total: int
    ) -> Dict:
        """
        Scrape a single restaurant menu (runs in a separate thread)
        
        Args:
            url: Restaurant menu URL
            index: Current restaurant index
            total: Total number of restaurants
            
        Returns:
            Dictionary with 'url', 'items', and 'success' keys
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"🍽️  Thread #{index}/{total}: Starting")
            print(f"📍 URL: {url}")
            print(f"{'='*70}")
        
        try:

            scraper = self.scraper_class()
            
 
            start_time = time.time()
            items = scraper.scrape_menu(url)
            elapsed = time.time() - start_time
            
            if self.verbose:
                print(f"\n✅ Thread #{index}: SUCCESS - {len(items)} items in {elapsed:.1f}s\n")
            
            return {
                'url': url,
                'items': items,
                'success': True,
                'error': None,
                'count': len(items),
                'elapsed_time': elapsed
            }
            
        except Exception as e:
            error_msg = f"Error in thread #{index}: {str(e)}"
            if self.verbose:
                print(f"\n❌ Thread #{index}: FAILED - {error_msg}\n")
            
            return {
                'url': url,
                'items': [],
                'success': False,
                'error': error_msg,
                'count': 0,
                'elapsed_time': 0
            }
    
    def scrape_all(
        self,
        urls: List[str],
        progress_callback: Optional[Callable] = None
    ) -> pd.DataFrame:
        """
        Scrape multiple restaurant menus concurrently
        
        Args:
            urls: List of restaurant menu URLs
            progress_callback: Optional callback(current, total, items_count)
            
        Returns:
            DataFrame containing all scraped menu items
        """
        if not urls:
            print("No URLs provided")
            return pd.DataFrame()
        
        start_time = time.time()
        all_items = []
        
        if self.verbose:
            print(f"\n{' MULTI-THREADED SCRAPING STARTED ':=^80}")
            print(f" Restaurants to scrape: {len(urls)}")
            print(f" Concurrent workers: {self.max_workers}")
            print(f"{'='*80}\n")
        

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:

            future_to_url = {
                executor.submit(
                    self._scrape_single_restaurant, 
                    url, 
                    idx, 
                    len(urls)
                ): url
                for idx, url in enumerate(urls, 1)
            }
            

            completed_count = 0
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    
                    if result['success']:
                        all_items.extend(result['items'])
                    else:
                        self.errors.append({
                            'url': url,
                            'error': result['error']
                        })
                    
  
                    if progress_callback:
                        progress_callback(
                            completed_count, 
                            len(urls), 
                            result['count']
                        )
                    
                    if self.verbose:
                        print(f"📈 Overall Progress: {completed_count}/{len(urls)} "
                              f"({completed_count*100//len(urls)}%)")
                
                except Exception as e:
                    if self.verbose:
                        print(f"❌ Unexpected error for {url}: {e}")
                    self.errors.append({
                        'url': url,
                        'error': str(e)
                    })
        

        df = pd.DataFrame(all_items)
        

        total_time = time.time() - start_time
        success_count = len(urls) - len(self.errors)
        
        if self.verbose:
            print(f"\n{'🎉 SCRAPING COMPLETED ':=^80}")
            print(f"✅ Successful: {success_count}/{len(urls)}")
            print(f"❌ Failed: {len(self.errors)}/{len(urls)}")
            print(f"📦 Total items: {len(all_items)}")
            print(f"⏱️  Total time: {total_time:.2f}s")
            if len(urls) > 0:
                print(f"⚡ Average: {total_time/len(urls):.2f}s per restaurant")
            print(f"{'='*80}\n")
            
            if self.errors:
                print("⚠️ Errors encountered:")
                for err in self.errors:
                    print(f"  - {err['url']}: {err['error']}")
        

        if self.output_file and not df.empty:
            self._save_results(df)
        
        self.results = all_items
        return df
    
    def _save_results(self, df: pd.DataFrame):
        """Save results to CSV file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            

            if self.output_file:
                filename = self.output_file
            else:
                filename = f"scraped_menus_{timestamp}.csv"
            

            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            if self.verbose:
                print(f"Results saved to: {filename}")
                print(f"Columns: {', '.join(df.columns.tolist())}")
        
        except Exception as e:
            print(f"Error saving file: {e}")
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about scraped data
        
        Returns:
            Dictionary with various statistics
        """
        if not self.results:
            return {
                'status': 'No data scraped',
                'total_items': 0
            }
        
        df = pd.DataFrame(self.results)
        
        stats = {
            'total_items': len(df),
            'unique_restaurants': df['restaurant'].nunique() if 'restaurant' in df.columns else 0,
            'total_errors': len(self.errors)
        }
        

        if 'price' in df.columns:
            stats['avg_price'] = int(df['price'].mean())
            stats['min_price'] = int(df['price'].min())
            stats['max_price'] = int(df['price'].max())
        

        if 'discount' in df.columns:
            discounted = df[df['discount'] != '0%']
            stats['items_with_discount'] = len(discounted)
   
            if len(df) > 0:
                stats['discount_percentage'] = f"{len(discounted)*100//len(df)}%"
            else:
                stats['discount_percentage'] = "0%"
        

        if 'stock' in df.columns:
            out_of_stock = df[df['stock'] == '0']
            stats['out_of_stock_items'] = len(out_of_stock)
        
        return stats
    
    def print_statistics(self):
        """Print formatted statistics"""
        stats = self.get_statistics()
        
        print(f"\n{'STATISTICS ':=^60}")
        for key, value in stats.items():
            label = key.replace('_', ' ').title()
            print(f"{label:.<40} {value}")
        print("="*60 + "\n")


def quick_scrape(
    scraper_class: Type,
    urls: List[str],
    max_workers: int = 3,
    save_to: Optional[str] = None,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Quick utility to scrape multiple restaurants
    
    Args:
        scraper_class: Scraper class (e.g., SnappFoodScraper)
        urls: List of restaurant URLs
        max_workers: Number of concurrent threads
        save_to: Optional CSV filename
        verbose: Print detailed logs
        
    Returns:
        DataFrame with all scraped data
    
    Example:
        >>> from snappfood_scraper import SnappFoodScraper
        >>> urls = [
        ...     "https://snappfood.ir/restaurant/menu/...",
        ...     "https://snappfood.ir/restaurant/menu/..."
        ... ]
        >>> df = quick_scrape(SnappFoodScraper, urls, max_workers=4)
    """
    scraper = ThreadedRestaurantScraper(
        scraper_class=scraper_class,
        max_workers=max_workers,
        output_file=save_to,
        verbose=verbose
    )
    
    df = scraper.scrape_all(urls)
    
    if verbose:
        scraper.print_statistics()
    
    return df


if __name__ == "__main__":
    from restaurant_scrapers import SnappFoodScraper
    

    restaurant_urls = [
        "https://snappfood.ir/restaurant/menu/%D9%BE%DB%8C%D8%AA%D8%B2%D8%A7_%D8%B4%DB%8C%D9%84%D8%A7__%D9%85%DB%8C%D8%AF%D8%A7%D9%86_%D8%A7%D9%86%D9%82%D9%84%D8%A7%D8%A8_-r-p5j2vw/?from_list=1&is_pickup=0&GAParams=",

    ]
    

    df = quick_scrape(
        SnappFoodScraper,
        restaurant_urls,
        max_workers=3,
        save_to="all_menus.csv"
    )
    
    
    print(f"\nScraped {len(df)} total items")
    if not df.empty:
        print(df.head())