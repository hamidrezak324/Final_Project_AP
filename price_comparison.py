import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import pandas as pd
from datetime import datetime
import os

class PriceComparisonGUI:
    """GUI for comparing prices with Snappfood"""
    
    def __init__(self, parent_window, db, food_service):
        self.window = tk.Toplevel(parent_window)
        self.window.title("مقایسه قیمت با Snappfood")
        self.window.geometry("900x700")
        
        self.db = db
        self.food_service = food_service
        self.scraped_data = None
        self.our_foods = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """creating GUI"""
        
        # top frame - main buttons
        top_frame = ttk.Frame(self.window, padding=10)
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="مقایسه قیمت با Snappfood", 
                 font=("Tahoma", 14, "bold")).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(top_frame, text="بستن", 
                  command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # tab 1: scrape
        scrape_tab = ttk.Frame(notebook)
        notebook.add(scrape_tab, text="اسکرپ Snappfood")
        self.create_scrape_tab(scrape_tab)
        
        # tab 2: compare
        compare_tab = ttk.Frame(notebook)
        notebook.add(compare_tab, text="مقایسه قیمت‌ها")
        self.create_compare_tab(compare_tab)
        
        # tab 3: reports
        report_tab = ttk.Frame(notebook)
        notebook.add(report_tab, text="گزارش‌ها")
        self.create_report_tab(report_tab)
    
    def create_scrape_tab(self, parent):
        """scrape tab"""
        
        # راهنما
        guide_frame = ttk.LabelFrame(parent, text="راهنما", padding=10)
        guide_frame.pack(fill=tk.X, padx=10, pady=10)
        
        guide_text = """
چگونه لینک رستوران را پیدا کنیم:
1. به سایت snappfood.ir بروید
2. رستوران مورد نظر را جستجو کنید
3. به صفحه منوی رستوران بروید
4. لینک را کپی کنید و در پایین وارد کنید

نمونه لینک:
https://snappfood.ir/restaurant/menu/رستوران-نام
        """
        
        ttk.Label(guide_frame, text=guide_text, 
                 font=("Tahoma", 9), justify=tk.LEFT).pack(anchor=tk.W)
        
        # ورودی لینک
        input_frame = ttk.LabelFrame(parent, text="لینک رستوران", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(input_frame, text="لینک:", font=("Tahoma", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.url_entry = ttk.Entry(input_frame, width=60, font=("Tahoma", 9))
        self.url_entry.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.url_entry.insert(0, "https://snappfood.ir/restaurant/menu/")
        
        input_frame.columnconfigure(1, weight=1)
        
        # buttons
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.scrape_btn = ttk.Button(btn_frame, text="🔍 شروع اسکرپ", 
                                     command=self.start_scraping, width=20)
        self.scrape_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="📁 بارگذاری از فایل CSV", 
                  command=self.load_from_csv, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="💾 ذخیره نتایج", 
                  command=self.save_scraped_data, width=20).pack(side=tk.LEFT, padx=5)
        
        # status
        self.status_var = tk.StringVar(value="آماده برای اسکرپ")
        status_label = ttk.Label(parent, textvariable=self.status_var, 
                                font=("Tahoma", 10, "bold"), foreground="blue")
        status_label.pack(pady=5)
        
        # displaying results
        results_frame = ttk.LabelFrame(parent, text="نتایج اسکرپ", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # results table
        columns = ("نام", "قیمت", "قیمت اصلی", "تخفیف", "موجودی")
        self.scrape_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.scrape_tree.heading(col, text=col)
            self.scrape_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.scrape_tree.yview)
        self.scrape_tree.configure(yscrollcommand=scrollbar.set)
        
        self.scrape_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_compare_tab(self, parent):
        """compare tab"""
        
        # buttons
        btn_frame = ttk.Frame(parent, padding=10)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="🔄 بارگذاری غذاهای سیستم", 
                  command=self.load_our_foods, width=25).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="⚖️ مقایسه قیمت‌ها", 
                  command=self.compare_prices, width=25).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="💾 ذخیره گزارش", 
                  command=self.save_comparison_report, width=25).pack(side=tk.LEFT, padx=5)
        
        # compare table
        compare_frame = ttk.LabelFrame(parent, text="نتایج مقایسه", padding=10)
        compare_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("غذای ما", "قیمت ما", "غذای Snappfood", "قیمت Snappfood", "اختلاف", "درصد", "وضعیت")
        self.compare_tree = ttk.Treeview(compare_frame, columns=columns, show="headings", height=15)
        
        col_widths = {"غذای ما": 150, "قیمت ما": 100, "غذای Snappfood": 150, 
                     "قیمت Snappfood": 120, "اختلاف": 100, "درصد": 80, "وضعیت": 100}
        
        for col in columns:
            self.compare_tree.heading(col, text=col)
            self.compare_tree.column(col, width=col_widths.get(col, 100))
        
        # coloring
        self.compare_tree.tag_configure('cheaper', background='#d4edda')
        self.compare_tree.tag_configure('expensive', background='#f8d7da')
        self.compare_tree.tag_configure('same', background='#fff3cd')
        
        scrollbar = ttk.Scrollbar(compare_frame, orient=tk.VERTICAL, command=self.compare_tree.yview)
        self.compare_tree.configure(yscrollcommand=scrollbar.set)
        
        self.compare_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_report_tab(self, parent):
        """report tab"""
        
        report_frame = ttk.LabelFrame(parent, text="خلاصه گزارش", padding=20)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.report_text = tk.Text(report_frame, width=80, height=20, 
                                   font=("Tahoma", 10), wrap=tk.WORD)
        self.report_text.pack(fill=tk.BOTH, expand=True)
        
        # adding scrollbar
        scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def start_scraping(self):
        """start scraping"""
        url = self.url_entry.get().strip()
        
        if not url or url == "https://snappfood.ir/restaurant/menu/":
            messagebox.showwarning("خطا", "لطفا لینک رستوران را وارد کنید")
            return
        
        if not url.startswith("https://snappfood.ir"):
            messagebox.showwarning("خطا", "لینک باید از snappfood.ir باشد")
            return
        
        self.status_var.set("در حال اسکرپ... لطفا صبر کنید")
        self.scrape_btn.config(state='disabled')
        
        def scrape_task():
            try:
                # import scraper
                from restaurant_scrapers import SnappFoodScraper
                
                scraper = SnappFoodScraper()
                items = scraper.scrape_menu(url)
                
                # update UI in main thread
                self.window.after(0, lambda: self.display_scraped_data(items))
                
            except Exception as e:
                error_msg = f"خطا در اسکرپ: {str(e)}"
                self.window.after(0, lambda: messagebox.showerror("خطا", error_msg))
                self.window.after(0, lambda: self.status_var.set("خطا در اسکرپ"))
            finally:
                self.window.after(0, lambda: self.scrape_btn.config(state='normal'))
        
        # execute in separate thread
        threading.Thread(target=scrape_task, daemon=True).start()
    
    def display_scraped_data(self, items):
        """displaying scraped data"""
        # removing table
        for item in self.scrape_tree.get_children():
            self.scrape_tree.delete(item)
        
        if not items:
            self.status_var.set("هیچ داده‌ای یافت نشد")
            messagebox.showwarning("هشدار", "هیچ غذایی از رستوران استخراج نشد")
            return
        
        # saving data
        self.scraped_data = pd.DataFrame(items)
        
        # displaying in table
        for item in items:
            self.scrape_tree.insert("", tk.END, values=(
                item.get('food_name', 'N/A')[:30],
                f"{item.get('price', 0):,}",
                f"{item.get('original_price', 0):,}",
                item.get('discount', '0%'),
                item.get('stock', 'نامشخص')
            ))
        
        self.status_var.set(f"✅ {len(items)} آیتم استخراج شد")
        messagebox.showinfo("موفقیت", f"{len(items)} غذا از رستوران استخراج شد")
    
    def load_from_csv(self):
        """loading from CSV file"""
        filename = filedialog.askopenfilename(
            title="انتخاب فایل CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                df = pd.read_csv(filename)
                
                # convert to dictionary list
                items = df.to_dict('records')
                
                self.display_scraped_data(items)
                
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در بارگذاری فایل: {str(e)}")
    
    def save_scraped_data(self):
        """saving scraped data"""
        if self.scraped_data is None or self.scraped_data.empty:
            messagebox.showwarning("خطا", "هیچ داده‌ای برای ذخیره وجود ندارد")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snappfood_scraped_{timestamp}.csv"
        
        try:
            self.scraped_data.to_csv(filename, index=False, encoding='utf-8-sig')
            messagebox.showinfo("موفقیت", f"داده‌ها در {filename} ذخیره شد")
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در ذخیره: {str(e)}")
    
    def load_our_foods(self):
        """loading foods from system"""
        try:
            foods_df = self.db.load_foods()
            
            if foods_df.empty:
                messagebox.showwarning("هشدار", "هیچ غذایی در سیستم ثبت نشده است")
                return
            
            self.our_foods = foods_df
            messagebox.showinfo("موفقیت", f"{len(foods_df)} غذا از سیستم بارگذاری شد")
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در بارگذاری غذاها: {str(e)}")
    
    def compare_prices(self):
        """comparing prices"""
        if self.our_foods is None:
            messagebox.showwarning("خطا", "ابتدا غذاهای سیستم را بارگذاری کنید")
            return
        
        if self.scraped_data is None or self.scraped_data.empty:
            messagebox.showwarning("خطا", "ابتدا داده‌های Snappfood را اسکرپ کنید")
            return
        
        # removing table
        for item in self.compare_tree.get_children():
            self.compare_tree.delete(item)
        
        comparison_results = []
        
        # comparing with similar name
        for _, our_food in self.our_foods.iterrows():
            our_name = str(our_food['name']).lower().strip()
            our_price = float(our_food['selling_price'])
            
            # searching for similar food in Snappfood
            best_match = None
            best_similarity = 0
            
            for _, snap_food in self.scraped_data.iterrows():
                snap_name = str(snap_food.get('food_name', '')).lower().strip()
                
                # calculating simple similarity
                similarity = self.calculate_similarity(our_name, snap_name)
                
                if similarity > best_similarity and similarity > 0.5:  # minimum 50% similarity
                    best_similarity = similarity
                    best_match = snap_food
            
            if best_match is not None:
                snap_price = float(best_match.get('price', 0))
                difference = our_price - snap_price
                percent_diff = (difference / snap_price * 100) if snap_price > 0 else 0
                
                status = "ارزان‌تر" if difference < 0 else ("گران‌تر" if difference > 0 else "برابر")
                tag = 'cheaper' if difference < 0 else ('expensive' if difference > 0 else 'same')
                
                self.compare_tree.insert("", tk.END, values=(
                    our_food['name'][:20],
                    f"{our_price:,.0f}",
                    best_match.get('food_name', 'N/A')[:20],
                    f"{snap_price:,.0f}",
                    f"{difference:,.0f}",
                    f"{percent_diff:.1f}%",
                    status
                ), tags=(tag,))
                
                comparison_results.append({
                    'our_food': our_food['name'],
                    'our_price': our_price,
                    'snap_food': best_match.get('food_name'),
                    'snap_price': snap_price,
                    'difference': difference,
                    'percent_diff': percent_diff,
                    'status': status
                })
        
        if not comparison_results:
            messagebox.showwarning("هشدار", "هیچ غذای مشابهی یافت نشد")
            return
        
        # creating report
        self.generate_report(comparison_results)
        
        messagebox.showinfo("موفقیت", f"{len(comparison_results)} مورد مقایسه شد")
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """calculating similarity of two strings"""
        # الگوریتم ساده: کلمات مشترک
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def generate_report(self, results):
        """creating report"""
        self.report_text.delete("1.0", tk.END)
        
        report = f"""
{'='*60}
گزارش مقایسه قیمت با Snappfood
{'='*60}
تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}

تعداد کل مقایسه‌ها: {len(results)}
"""
        
        cheaper = [r for r in results if r['difference'] < 0]
        expensive = [r for r in results if r['difference'] > 0]
        same = [r for r in results if r['difference'] == 0]
        
        report += f"""
📊 خلاصه:
  ✅ ارزان‌تر از Snappfood: {len(cheaper)} مورد
  ❌ گران‌تر از Snappfood: {len(expensive)} مورد
  ⚖️ برابر: {len(same)} مورد

"""
        
        if cheaper:
            avg_cheaper = sum(abs(r['difference']) for r in cheaper) / len(cheaper)
            report += f"💰 میانگین صرفه‌جویی در موارد ارزان‌تر: {avg_cheaper:,.0f} تومان\n"
        
        if expensive:
            avg_expensive = sum(r['difference'] for r in expensive) / len(expensive)
            report += f"📈 میانگین اختلاف در موارد گران‌تر: {avg_expensive:,.0f} تومان\n"
        
        report += f"\n{'='*60}\n"
        report += "جزئیات موارد گران‌تر:\n"
        report += f"{'='*60}\n"
        
        for r in sorted(expensive, key=lambda x: x['difference'], reverse=True):
            report += f"""
غذا: {r['our_food']}
  قیمت ما: {r['our_price']:,.0f} تومان
  قیمت Snappfood: {r['snap_price']:,.0f} تومان
  اختلاف: +{r['difference']:,.0f} تومان ({r['percent_diff']:.1f}%)
"""
        
        self.report_text.insert("1.0", report)
    
    def save_comparison_report(self):
        """saving comparison report"""
        report_content = self.report_text.get("1.0", tk.END)
        
        if not report_content.strip():
            messagebox.showwarning("خطا", "گزارشی برای ذخیره وجود ندارد")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"price_comparison_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            messagebox.showinfo("موفقیت", f"گزارش در {filename} ذخیره شد")
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در ذخیره گزارش: {str(e)}")


# helper function to add to admin menu
def open_price_comparison(parent_window, db, food_service):
    """opening price comparison window"""
    PriceComparisonGUI(parent_window, db, food_service)


if __name__ == "__main__":
    # test
    root = tk.Tk()
    root.withdraw()  # hiding main window
    
    from database import Database
    from food_service import FoodService
    
    db = Database()
    food_service = FoodService()
    
    PriceComparisonGUI(root, db, food_service)
    root.mainloop()