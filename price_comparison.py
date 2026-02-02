import pandas as pd
import matplotlib.pyplot as plt

class PriceComparator:
    """مقایسه قیمت غذاها با رقبا"""
    
    def __init__(self, our_prices_file: str, competitor_prices_file: str):
        self.our_prices = pd.read_csv(our_prices_file)
        self.competitor_prices = pd.read_csv(competitor_prices_file)
    
    def find_similar_foods(self, food_name: str, threshold: float = 0.7):
        """پیدا کردن غذاهای مشابه با الگوریتم فازی"""
        from fuzzywuzzy import fuzz
        
        similar_items = []
        
        for _, row in self.competitor_prices.iterrows():
            ratio = fuzz.ratio(food_name.lower(), row['food_name'].lower())
            if ratio > threshold * 100:
                similar_items.append({
                    'competitor': row['restaurant'],
                    'food_name': row['food_name'],
                    'price': row['price'],
                    'similarity': ratio
                })
        
        return similar_items
    
    def generate_comparison_report(self):
        """تولید گزارش مقایسه قیمت"""
        report = []
        
        for _, our_food in self.our_prices.iterrows():
            similar_foods = self.find_similar_foods(our_food['name'])
            
            if similar_foods:
                competitor_prices = [f['price'] for f in similar_foods]
                avg_competitor_price = sum(competitor_prices) / len(competitor_prices)
                
                price_difference = our_food['price'] - avg_competitor_price
                price_difference_percent = (price_difference / avg_competitor_price) * 100
                
                report.append({
                    'our_food': our_food['name'],
                    'our_price': our_food['price'],
                    'avg_competitor_price': avg_competitor_price,
                    'price_difference': price_difference,
                    'price_difference_percent': price_difference_percent,
                    'competitors_count': len(similar_foods),
                    'status': 'Cheaper' if price_difference < 0 else 'More Expensive'
                })
        
        return pd.DataFrame(report)
    
    def plot_price_comparison(self):
        """نمودار مقایسه قیمت"""
        report = self.generate_comparison_report()
        
        if report.empty:
            print("No comparable items found")
            return
        
        plt.figure(figsize=(12, 6))
        
        # نمودار میله‌ای
        x = range(len(report))
        width = 0.35
        
        plt.bar(x, report['our_price'], width, label='Our Price', color='blue')
        plt.bar([i + width for i in x], report['avg_competitor_price'], 
                width, label='Avg Competitor Price', color='orange')
        
        plt.xlabel('Food Items')
        plt.ylabel('Price')
        plt.title('Price Comparison with Competitors')
        plt.xticks([i + width/2 for i in x], report['our_food'], rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        plt.show()