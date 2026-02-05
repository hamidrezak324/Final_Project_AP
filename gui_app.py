# gui_app.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import threading
import os
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')   
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, date, timedelta

# adding path to project files
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import AuthManager
from food_service import FoodService
from order_service import OrderService
from customer_service import CustomerService
from admin_service import AdminService
from model import Cart, Order
from database import Database
from restaurant_scrapers import SnappFoodScraper
from price_comparison import PriceComparisonGUI

class FoodDeliveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("سامانه سفارش غذا")
        self.root.geometry("1000x700")
        
        # font settings
        self.font = ("Alibaba", 10)
        self.title_font = ("Alibaba", 14, "bold")
        
        # services
        self.auth = AuthManager()
        self.food_service = FoodService()
        self.order_service = OrderService()
        self.customer_service = CustomerService()
        self.admin_service = AdminService()
        self.db = Database() 

        # scrapers and price comparator
        self.snappfood_scraper = SnappFoodScraper()
        self.price_comparator = None
        
        # user status
        self.current_user = None
        self.user_role = None
        self.cart = Cart()
        self.selected_date = date.today()
        
        #comparison
        self.our_df = None
        self.comp_df = None
        self.comparison_done = False
        self.merged_df = None  
        
        # create pages
        self.create_login_page()
    
    def clear_window(self):
        """clear current window content"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    # -------------------------------------------------------
    # login/register page
    # -------------------------------------------------------
    def create_login_page(self):
        self.clear_window()
        
        # main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # title
        ttk.Label(main_frame, text="سامانه سفارش غذا", font=self.title_font).pack(pady=20)
        
        # login frame
        login_frame = ttk.LabelFrame(main_frame, text="ورود کاربر", padding=15)
        login_frame.pack(fill=tk.X, pady=10)
        
        # email
        ttk.Label(login_frame, text="ایمیل:", font=self.font).grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.email_entry = ttk.Entry(login_frame, width=30, font=self.font)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # password
        ttk.Label(login_frame, text="رمز عبور:", font=self.font).grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.password_entry = ttk.Entry(login_frame, width=30, show="*", font=self.font)
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # login buttons
        btn_frame = ttk.Frame(login_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        
        ttk.Button(btn_frame, text="ورود مشتری", 
                  command=self.login_customer, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="ورود ادمین", 
                  command=self.login_admin, width=15).pack(side=tk.LEFT, padx=5)
        
        # seperator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)
        
        # rigester_button
        ttk.Button(main_frame, text="ثبت‌نام مشتری جدید", 
                  command=self.create_register_page, width=20).pack(pady=10)
    
    def login_customer(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        
        if not email or not password:
            messagebox.showwarning("خطا", "لطفا ایمیل و رمز عبور را وارد کنید")
            return
        
        success, msg, user = self.auth.login_user(email, password, is_admin=False)
        
        if success:
            self.current_user = user
            self.user_role = "Customer"
            messagebox.showinfo("موفقیت", "ورود موفقیت‌آمیز بود")
            self.create_customer_dashboard()
        else:
            messagebox.showerror("خطا", msg)
    
    def login_admin(self):
        email  = self.email_entry.get() 
        password = self.password_entry.get()
        
        if not email  or not password:
            messagebox.showwarning("خطا", "لطفا شناسه ایمیل یا شماره پرسنلی و رمز عبور را وارد کنید")
            return

        user_record = self.db.find_user_by_email(email)
        if user_record is not None and user_record['role'] == 'Admin':

            success, msg, user = self.auth.login_user(email, password, is_admin=False)

            
            if success and user.get_role() == "Admin":
                self.current_user = user
                self.user_role = "Admin"
                messagebox.showinfo("موفقیت", "ورود ادمین موفقیت‌آمیز بود")
                self.create_admin_dashboard()
            else:
                messagebox.showerror("خطا", msg)
        else:
             messagebox.showerror("خطا", "کاربر ادمین با این ایمیل یافت نشد")
    # -------------------------------------------------------
    # register page
    # -------------------------------------------------------
    def create_register_page(self):
        self.clear_window()
        
        # main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # title
        ttk.Label(main_frame, text="ثبت‌نام مشتری جدید", font=self.title_font).pack(pady=10)
        
        # register form
        form_frame = ttk.Frame(main_frame, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # row 1: first name and last name
        ttk.Label(form_frame, text="نام:", font=self.font).grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.reg_firstname = ttk.Entry(form_frame, width=25, font=self.font)
        self.reg_firstname.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="نام خانوادگی:", font=self.font).grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)
        self.reg_lastname = ttk.Entry(form_frame, width=25, font=self.font)
        self.reg_lastname.grid(row=0, column=3, padx=5, pady=5)
        
        # row 2: email
        ttk.Label(form_frame, text="ایمیل:", font=self.font).grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.reg_email = ttk.Entry(form_frame, width=60, font=self.font)
        self.reg_email.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # row 3: password
        ttk.Label(form_frame, text="رمز عبور:", font=self.font).grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.reg_password = ttk.Entry(form_frame, width=25, show="*", font=self.font)
        self.reg_password.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="تکرار رمز عبور:", font=self.font).grid(row=2, column=2, padx=5, pady=5, sticky=tk.E)
        self.reg_confirm = ttk.Entry(form_frame, width=25, show="*", font=self.font)
        self.reg_confirm.grid(row=2, column=3, padx=5, pady=5)
        
        # row 4: phone and national code
        ttk.Label(form_frame, text="تلفن همراه:", font=self.font).grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        self.reg_phone = ttk.Entry(form_frame, width=25, font=self.font)
        self.reg_phone.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="کد ملی:", font=self.font).grid(row=3, column=2, padx=5, pady=5, sticky=tk.E)
        self.reg_national = ttk.Entry(form_frame, width=25, font=self.font)
        self.reg_national.grid(row=3, column=3, padx=5, pady=5)
        
        # row 5: address
        ttk.Label(form_frame, text="آدرس:", font=self.font).grid(row=4, column=0, padx=5, pady=5, sticky=tk.NE)
        self.reg_address = tk.Text(form_frame, width=58, height=4, font=self.font)
        self.reg_address.grid(row=4, column=1, columnspan=3, padx=5, pady=5)
        
        # buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="ثبت‌نام", 
                  command=self.register_customer, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="بازگشت", 
                  command=self.create_login_page, width=15).pack(side=tk.LEFT, padx=10)
    
    def register_customer(self):
        try:
            success, msg = self.auth.register_customer(
                first_name=self.reg_firstname.get(),
                last_name=self.reg_lastname.get(),
                email=self.reg_email.get(),
                phone=self.reg_phone.get(),
                national_code=self.reg_national.get(),
                password=self.reg_password.get(),
                confirm_password=self.reg_confirm.get(),
                address=self.reg_address.get("1.0", tk.END).strip()
            )
            
            if success:
                messagebox.showinfo("موفقیت", msg)
                self.create_login_page()
            else:
                messagebox.showerror("خطا", msg)
        except Exception as e:
            messagebox.showerror("خطا", str(e))
    
    # -------------------------------------------------------
    # customer dashboard
    # -------------------------------------------------------
    def create_customer_dashboard(self):
        self.clear_window()
        
        # menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # menus
        user_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=f"کاربر: {self.current_user.full_name}", menu=user_menu)
        user_menu.add_command(label="پروفایل", command=self.show_profile)
        user_menu.add_command(label="سبد خرید", command=self.show_cart)
        user_menu.add_command(label="سفارشات من", command=self.show_order_history)
        user_menu.add_separator()
        user_menu.add_command(label="خروج", command=self.logout)
        
        # food menu
        food_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="منوی غذاها", menu=food_menu)
        food_menu.add_command(label="نمایش منوی امروز", command=self.show_today_menu)
        food_menu.add_command(label="جستجوی غذا", command=self.show_search_food)
        
        # points menu
        points_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="امتیازات", menu=points_menu)
        points_menu.add_command(label="امتیازات من", command=self.show_loyalty_points)
        points_menu.add_command(label="تبدیل به کد تخفیف", command=self.convert_points)

        review_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="نظرات", menu=review_menu)
        review_menu.add_command(label="نظرات من", command=self.show_my_reviews)
        
        # welcome page
        welcome_frame = ttk.Frame(self.root, padding=30)
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(welcome_frame, text=f"خوش آمدید {self.current_user.full_name}!", 
                 font=self.title_font).pack(pady=20)
        
        ttk.Label(welcome_frame, text="از منوی بالا برای دسترسی به امکانات استفاده کنید", 
                 font=self.font).pack(pady=10)
        
        # quick buttons
        btn_frame = ttk.Frame(welcome_frame)
        btn_frame.pack(pady=30)
        
        ttk.Button(btn_frame, text="📋 منوی امروز", 
                  command=self.show_today_menu, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="🛒 سبد خرید", 
                  command=self.show_cart, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="📦 سفارشات من", 
                  command=self.show_order_history, width=15).pack(side=tk.LEFT, padx=10)
    
    def show_today_menu(self):
        self.clear_window()
        
        # top bar
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="بازگشت", 
                  command=self.create_customer_dashboard).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="منوی غذاهای امروز", 
                 font=self.title_font).pack(side=tk.LEFT, padx=20)
        
        # Treeview for displaying foods
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # columns
        columns = ("نام", "دسته‌بندی", "قیمت (تومان)", "موجودی", "توضیحات")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # set columns
        tree.heading("نام", text="نام")
        tree.heading("دسته‌بندی", text="دسته‌بندی")
        tree.heading("قیمت (تومان)", text="قیمت (تومان)")
        tree.heading("موجودی", text="موجودی")
        tree.heading("توضیحات", text="توضیحات")
        
        tree.column("نام", width=150)
        tree.column("دسته‌بندی", width=100)
        tree.column("قیمت (تومان)", width=100)
        tree.column("موجودی", width=80)
        tree.column("توضیحات", width=200)
        
        # scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # get today's foods
        foods = self.food_service.get_menu_for_date(date.today())
        
        for food in foods:
            tree.insert("", tk.END, values=(
                food.name,
                food.category,
                f"{food.selling_price:,.0f}",
                food.stock,
                food.description[:50] + "..." if len(food.description) > 50 else food.description
            ))
        
        # buttons frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="افزودن به سبد خرید", 
                  command=lambda: self.add_to_cart_from_tree(tree)).pack(side=tk.LEFT, padx=5)
    
    def add_to_cart_from_tree(self, tree):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("خطا", "لطفاً یک غذا انتخاب کنید")
            return
        
        item_values = tree.item(selected_item[0])['values']
        food_name = item_values[0]
        
        # search food by name
        foods = self.food_service.search_foods(food_name)
        if not foods:
            messagebox.showerror("خطا", "غذا پیدا نشد")
            return
        
        food = foods[0]
        
        # get quantity
        quantity = simpledialog.askinteger("تعداد", f"تعداد {food_name} را وارد کنید:", 
                                          parent=self.root, minvalue=1, maxvalue=food.stock)
        if quantity:
            try:
                self.food_service.add_to_cart(self.cart, food.food_id, quantity)
                messagebox.showinfo("موفقیت", f"{quantity} عدد {food_name} به سبد خرید اضافه شد")
            except ValueError as e:
                messagebox.showerror("خطا", str(e))
    
    def show_cart(self):
        self.clear_window()
        
        # top bar
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="بازگشت", 
                  command=self.create_customer_dashboard).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="سبد خرید من", 
                 font=self.title_font).pack(side=tk.LEFT, padx=20)
        
        if not self.cart.items:
            # empty cart
            empty_frame = ttk.Frame(self.root, padding=50)
            empty_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(empty_frame, text="سبد خرید شما خالی است", 
                     font=self.title_font).pack(pady=20)
            ttk.Button(empty_frame, text="بازگشت به منو", 
                      command=self.show_today_menu).pack()
            return
        
        # Treeview for displaying cart
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("نام غذا", "قیمت واحد", "تعداد", "ویرایش تعداد", "قیمت کل")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        
        tree.heading("نام غذا", text="نام غذا")
        tree.heading("قیمت واحد", text="قیمت واحد (تومان)")
        tree.heading("تعداد", text="تعداد")
        tree.heading("ویرایش تعداد", text="ویرایش تعداد")
        tree.heading("قیمت کل", text="قیمت کل (تومان)")
        
        tree.column("نام غذا", width=200)
        tree.column("قیمت واحد", width=120)
        tree.column("تعداد", width=80)
        tree.column("ویرایش تعداد", width=120)
        tree.column("قیمت کل", width=120)
        
        # adding items
        total = 0
        for item in self.cart.items:
            item_total = item.total_price
            total += item_total
            tree.insert("", tk.END, values=(
                item.food.name,
                f"{item.unit_price:,.0f}",
                item.quantity,
                "ویرایش",  
                f"{item_total:,.0f}"
            ))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # showing total
        total_frame = ttk.Frame(self.root)
        total_frame.pack(pady=10)
        
        ttk.Label(total_frame, text=f"مجموع سبد خرید: {total:,.0f} تومان", 
                 font=("Tahoma", 12, "bold")).pack()
        
        # buttons frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=15)
        
        ttk.Button(btn_frame, text="حذف انتخاب شده", 
                  command=lambda: self.remove_from_cart(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="ویرایش تعداد انتخاب شده", 
                  command=lambda: self.edit_quantity(tree)).pack(side=tk.LEFT, padx=5)          
        ttk.Button(btn_frame, text="تسویه حساب", 
                  command=self.checkout_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="خالی کردن سبد", 
                  command=self.clear_cart).pack(side=tk.LEFT, padx=5)
    
    def remove_from_cart(self, tree):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("خطا", "لطفاً یک آیتم انتخاب کنید")
            return
        
        item_values = tree.item(selected_item[0])['values']
        food_name = item_values[0]
        
        # find food_id
        for item in self.cart.items:
            if item.food.name == food_name:
                self.food_service.remove_from_cart(self.cart, item.food.food_id)
                messagebox.showinfo("موفقیت", f"{food_name} از سبد خرید حذف شد")
                self.show_cart()
                return
    
    def clear_cart(self):
        if messagebox.askyesno("تأیید", "آیا مطمئن هستید که می‌خواهید سبد خرید را خالی کنید؟"):
            self.cart.clear()
            messagebox.showinfo("موفقیت", "سبد خرید خالی شد")
            self.show_cart()
    
    def checkout_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("تسویه حساب")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # delivery date
        ttk.Label(dialog, text="تاریخ تحویل:", font=self.font).pack(pady=5)
        
        # use simple DateEntry (in reality use datepicker)
        delivery_date = date.today() + timedelta(days=1)
        date_label = ttk.Label(dialog, text=delivery_date.strftime("%Y-%m-%d"), 
                              font=self.font, relief=tk.SUNKEN, width=15)
        date_label.pack(pady=5)
        
        # payment method
        ttk.Label(dialog, text="روش پرداخت:", font=self.font).pack(pady=5)
        payment_var = tk.StringVar(value=Order.PAYMENT_ONLINE)
        
        ttk.Radiobutton(dialog, text="پرداخت آنلاین", 
                       variable=payment_var, value=Order.PAYMENT_ONLINE).pack()
        ttk.Radiobutton(dialog, text="پرداخت نقدی هنگام تحویل", 
                       variable=payment_var, value=Order.PAYMENT_CASH).pack()
        
        # discount code
        ttk.Label(dialog, text="کد تخفیف (اختیاری):", font=self.font).pack(pady=5)
        discount_entry = ttk.Entry(dialog, width=20, font=self.font)
        discount_entry.pack()
        
        # buttons
        def process_checkout():
            try:
                order = self.order_service.checkout(
                    cart=self.cart,
                    customer_id=self.current_user.user_id,
                    delivery_date=delivery_date,
                    payment_method=payment_var.get(),
                    discount_code_str=discount_entry.get() or None
                )
                
                dialog.destroy()
                messagebox.showinfo("موفقیت", f"سفارش شما با کد {order.order_id} ثبت شد")
                
                # payment
                if payment_var.get() == Order.PAYMENT_ONLINE:
                    if messagebox.askyesno("پرداخت", "آیا مایل به پرداخت آنلاین هستید؟"):
                        self.order_service.process_payment(order.order_id)
                        messagebox.showinfo("موفقیت", "پرداخت با موفقیت انجام شد")
                
                self.create_customer_dashboard()
                
            except ValueError as e:
                messagebox.showerror("خطا", str(e))
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="تأیید سفارش", 
                  command=process_checkout, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="انصراف", 
                  command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=10)
    
    def show_order_history(self):
        self.clear_window()
        
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="بازگشت", 
                  command=self.create_customer_dashboard).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="سفارشات من", 
                 font=self.title_font).pack(side=tk.LEFT, padx=20)
        
        # get order history
        orders = self.customer_service.get_order_history(self.current_user.user_id)
        
        if not orders:
            ttk.Label(self.root, text="شما هیچ سفارشی ندارید", 
                     font=self.font).pack(pady=50)
            return
        
        # Treeview for displaying orders
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("کد سفارش", "تاریخ", "وضعیت", "مبلغ نهایی", "تعداد آیتم‌ها")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("کد سفارش", width=120)
        tree.column("تاریخ", width=120)
        tree.column("وضعیت", width=100)
        tree.column("مبلغ نهایی", width=120)
        tree.column("تعداد آیتم‌ها", width=100)
        
        for order in orders:
            tree.insert("", tk.END, values=(
                order['order_id'][:10] + "...",
                order['date'],
                order['status'],
                f"{order['final_amount']:,.0f}",
                len(order['items'])
            ))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # show order details
        def show_order_details():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("خطا", "لطفاً یک سفارش انتخاب کنید")
                return
            
            item_values = tree.item(selected_item[0])['values']
            order_id_short = item_values[0]
            
            # find complete order
            for order in orders:
                if order['order_id'].startswith(order_id_short[:10]):
                    self.show_order_detail(order)
                    break
        
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="مشاهده جزییات", 
                  command=show_order_details).pack()
    
    def show_order_detail(self, order):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"جزییات سفارش {order['order_id']}")
        dialog.geometry("600x550")
        
        # order info
        info_frame = ttk.LabelFrame(dialog, text="اطلاعات سفارش", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(info_frame, text=f"کد سفارش: {order['order_id']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"تاریخ: {order['date']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"وضعیت: {order['status']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"مبلغ کل: {order['total_amount']:,.0f} تومان").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"مبلغ پرداختی: {order['final_amount']:,.0f} تومان").pack(anchor=tk.W)

        can_review = order['status'] in ['Paid', 'Sent']
        
        # order items
        items_frame = ttk.LabelFrame(dialog, text="آیتم‌های سفارش", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tree_frame = ttk.Frame(items_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("نام غذا", "قیمت واحد", "تعداد", "قیمت کل")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            tree.heading(col, text=col)
        
        for item in order['items']:
            tree.insert("", tk.END, values=(
                item['food_name'],
                f"{item['unit_price']:,.0f}",
                item['quantity'],
                f"{item['total']:,.0f}"
            ))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        if can_review:
            ttk.Button(btn_frame, text="ثبت نظر", 
                  command=lambda: self.submit_review_dialog(order)).pack(side=tk.LEFT, padx=5)

            reviews_df = self.db.get_reviews_by_order(order['order_id'])
            if not reviews_df.empty:
                ttk.Button(btn_frame, text="📋 نمایش نظرات", 
                        command=lambda: self.show_order_reviews(order['order_id'])).pack(side=tk.LEFT, padx=5)      
        
        # close button
        ttk.Button(dialog, text="بستن", 
                  command=dialog.destroy).pack(pady=10)
    
    def show_loyalty_points(self):
        points = self.customer_service.get_user_points(self.current_user.user_id)
        messagebox.showinfo("امتیازات وفاداری", 
                          f"شما {points} امتیاز وفاداری دارید.\n\n"
                          f"هر 1000 تومان خرید = 1 امتیاز\n"
                          f"100 امتیاز = کد تخفیف 10%")
    
    def convert_points(self):
        points = self.customer_service.get_user_points(self.current_user.user_id)
        
        if points < 100:
            messagebox.showwarning("خطا", f"حداقل امتیاز مورد نیاز: 100\nامتیاز فعلی شما: {points}")
            return
        
        if messagebox.askyesno("تبدیل امتیاز", 
                             f"آیا می‌خواهید 100 امتیاز خود را به یک کد تخفیف 10% تبدیل کنید؟\n"
                             f"امتیاز فعلی: {points}"):
            try:
                discount = self.customer_service.generate_discount_code(
                    self.current_user.user_id, 100
                )
                messagebox.showinfo("موفقیت", 
                                  f"کد تخفیف شما: {discount.code}\n"
                                  f"تخفیف: {discount.discount_percentage}%\n"
                                  f"معتبر تا: {discount.expiry_date.strftime('%Y-%m-%d')}")
            except ValueError as e:
                messagebox.showerror("خطا", str(e))
    
    def show_profile(self):
        messagebox.showinfo("پروفایل", 
                          f"نام: {self.current_user.full_name}\n"
                          f"ایمیل: {self.current_user.email}\n"
                          f"تلفن: {getattr(self.current_user, 'phone', 'ثبت نشده')}\n"
                          f"آدرس: {getattr(self.current_user, 'address', 'ثبت نشده')}")
    
    def show_search_food(self):
        query = simpledialog.askstring("جستجوی غذا", "عبارت جستجو را وارد کنید:", parent=self.root)
        if query:
            foods = self.food_service.search_foods(query)
            
            if not foods:
                messagebox.showinfo("نتیجه", "غذایی یافت نشد")
                return
            
            # display results in new window
            result_window = tk.Toplevel(self.root)
            result_window.title(f"نتایج جستجو برای: {query}")
            result_window.geometry("600x400")
            
            tree_frame = ttk.Frame(result_window)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            columns = ("نام", "دسته‌بندی", "قیمت", "موجودی", "توضیحات")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
            
            for col in columns:
                tree.heading(col, text=col)
            
            for food in foods:
                tree.insert("", tk.END, values=(
                    food.name,
                    food.category,
                    f"{food.selling_price:,.0f}",
                    food.stock,
                    food.description[:50] + "..." if len(food.description) > 50 else food.description
                ))
            
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # -------------------------------------------------------
    # admin dashboard
    # -------------------------------------------------------
    def create_admin_dashboard(self):
        self.clear_window()
        
        # menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # menus
        user_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=f"ادمین: {self.current_user.full_name}", menu=user_menu)
        user_menu.add_command(label="پروفایل", command=self.show_admin_profile)
        user_menu.add_separator()
        user_menu.add_command(label="خروج", command=self.logout)
        
        admin_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="مدیریت", menu=admin_menu)
        admin_menu.add_command(label="مدیریت غذاها", command=self.show_food_management)
        admin_menu.add_command(label="مدیریت سفارشات", command=self.show_order_management)
        admin_menu.add_command(label="گزارشات فروش", command=self.show_sales_reports)
        admin_menu.add_command(label="ایجاد کد تخفیف", command=self.create_admin_discount)
        
        report_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="گزارشات", menu=report_menu)
        report_menu.add_command(label="گزارش فروش و سود", command=self.create_sales_report_page)

        scraping_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📊 اسکرپ و مقایسه", menu=scraping_menu)
        scraping_menu.add_command(label="اسکرپ قیمت‌های Snappfood", command=self.show_scraping_page)
        scraping_menu.add_command(label="مقایسه قیمت با رقبا", command=self.show_price_comparison)
        scraping_menu.add_command(label="نمایش نمودار مقایسه", command=self.show_comparison_chart)
        scraping_menu.add_command(label="اسکرپ همزمان چند رستوران", command=self.show_multi_scraping)
        
        # admin welcome page
        welcome_frame = ttk.Frame(self.root, padding=30)
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(welcome_frame, text="پنل مدیریت رستوران", 
                 font=self.title_font).pack(pady=20)
        
        ttk.Label(welcome_frame, text=f"خوش آمدید ادمین {self.current_user.full_name}", 
                 font=self.font).pack(pady=10)
        
        # quick buttons
        btn_frame = ttk.Frame(welcome_frame)
        btn_frame.pack(pady=30)
        
        ttk.Button(btn_frame, text="🍽️ مدیریت غذاها", 
                  command=self.show_food_management, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="📦 مدیریت سفارشات", 
                  command=self.show_order_management, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="📊 گزارشات فروش", 
                  command=self.show_sales_reports, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="🔍 مقایسه قیمت", 
                  command=self.show_price_comparison, width=20).pack(side=tk.LEFT, padx=10)
    def show_admin_profile(self):
        messagebox.showinfo("پروفایل ادمین", 
                          f"نام: {self.current_user.full_name}\n"
                          f"ایمیل: {self.current_user.email}\n"
                          f"شناسه پرسنلی: {self.current_user.personnel_id}")
    
    def show_food_management(self):
        self.clear_window()
        
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="بازگشت", 
                  command=self.create_admin_dashboard).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="مدیریت غذاها", 
                 font=self.title_font).pack(side=tk.LEFT, padx=20)
        
        # add food button
        ttk.Button(top_frame, text="➕ غذای جدید", 
                  command=self.show_add_food_dialog).pack(side=tk.RIGHT)
        
        # Treeview for displaying foods
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("ID", "نام", "دسته‌بندی", "قیمت فروش", "قیمت تمام", "موجودی", "تاریخ‌های موجودی")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("ID", width=100)
        tree.column("نام", width=150)
        tree.column("دسته‌بندی", width=100)
        tree.column("قیمت فروش", width=100)
        tree.column("قیمت تمام", width=100)
        tree.column("موجودی", width=80)
        tree.column("تاریخ‌های موجودی", width=150)
        
        # get all foods
        foods = self.admin_service.food_service.get_all_foods()
        
        for food in foods:
            tree.insert("", tk.END, values=(
                food.food_id[:8] + "...",
                food.name,
                food.category,
                f"{food.selling_price:,.0f}",
                f"{food.cost_price:,.0f}",
                food.stock,
                f"{len(food.available_dates)} روز"
            ))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # buttons frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="ویرایش", 
                  command=lambda: self.edit_food(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="حذف", 
                  command=lambda: self.delete_food(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="بروزرسانی", 
                  command=self.show_food_management).pack(side=tk.LEFT, padx=5)

    def show_add_food_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("افزودن غذای جدید")
        dialog.geometry("550x650")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # form
        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # local variables for inputs
        restaurant_id_entry = None
        name_entry = None
        category_entry = None
        selling_price_entry = None
        cost_price_entry = None
        stock_entry = None
        ingredients_text = None
        description_text = None
        dates_text = None
        
        # rows
        rows = [
            ("شناسه رستوران:", "entry"),
            ("نام غذا:", "entry"),
            ("دسته‌بندی:", "entry"),
            ("قیمت فروش (تومان):", "entry"),
            ("قیمت تمام شده (تومان):", "entry"),
            ("موجودی:", "entry"),
            ("مواد اولیه:", "text"),
            ("توضیحات:", "text"),
        ]
        
        for i, (label, field_type) in enumerate(rows):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky=tk.E)
            
            if field_type == "entry":
                if label == "شناسه رستوران:":
                    entry = ttk.Entry(form_frame, width=40)
                    entry.insert(0, "restaurant_001")
                    restaurant_id_entry = entry
                elif label == "نام غذا:":
                    entry = ttk.Entry(form_frame, width=40)
                    name_entry = entry
                elif label == "دسته‌بندی:":
                    entry = ttk.Entry(form_frame, width=40)
                    category_entry = entry
                elif label == "قیمت فروش (تومان):":
                    entry = ttk.Entry(form_frame, width=40)
                    selling_price_entry = entry
                elif label == "قیمت تمام شده (تومان):":
                    entry = ttk.Entry(form_frame, width=40)
                    cost_price_entry = entry
                elif label == "موجودی:":
                    entry = ttk.Entry(form_frame, width=40)
                    entry.insert(0, "10")
                    stock_entry = entry
                entry.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)
                    
            elif field_type == "text":
                if label == "مواد اولیه:":
                    text = tk.Text(form_frame, width=40, height=3)
                    ingredients_text = text
                elif label == "توضیحات:":
                    text = tk.Text(form_frame, width=40, height=3)
                    description_text = text
                text.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)
        
        # explanation of available dates
        row_index = len(rows)
        ttk.Label(form_frame, text="تاریخ‌های موجودی (به فرمت YYYY-MM-DD):").grid(
            row=row_index, column=0, columnspan=2, pady=10
        )
        
        dates_text = tk.Text(form_frame, width=40, height=4)
        dates_text.grid(row=row_index+1, column=0, columnspan=2, padx=5, pady=5)
        dates_text.insert("1.0", "هر تاریخ در یک خط\nمثال:\n2024-01-15\n2024-01-16\n2024-01-17")
        
        # local function to save food
        def save_food_local():
            try:
                # get restaurant id
                restaurant_id = restaurant_id_entry.get().strip()
                if not restaurant_id:
                    messagebox.showerror("خطا", "شناسه رستوران نمی‌تواند خالی باشد")
                    return
                
                # check other required fields
                if not name_entry.get().strip():
                    messagebox.showerror("خطا", "نام غذا نمی‌تواند خالی باشد")
                    return
                
                if not category_entry.get().strip():
                    messagebox.showerror("خطا", "دسته‌بندی نمی‌تواند خالی باشد")
                    return
                
                try:
                    selling_price = float(selling_price_entry.get())
                    cost_price = float(cost_price_entry.get())
                    stock = int(stock_entry.get())
                    
                    if selling_price <= 0 or cost_price <= 0 or stock < 0:
                        raise ValueError("مقادیر باید مثبت باشند")
                        
                except ValueError as e:
                    messagebox.showerror("خطا", f"مقدار عددی نامعتبر: {str(e)}")
                    return
                
                # convert dates
                dates_str = dates_text.get("1.0", tk.END).strip()
                date_lines = [line.strip() for line in dates_str.split('\n') if line.strip()]
                
                available_dates = []
                for line in date_lines:
                    if line and not line.startswith("هر") and not line.startswith("مثال"):
                        try:
                            d = datetime.strptime(line.strip(), "%Y-%m-%d").date()
                            available_dates.append(d)
                        except ValueError:
                            pass
                
                if not available_dates:
                    available_dates = [date.today()]
                
                # create food
                food = self.admin_service.add_new_food(
                    name=name_entry.get().strip(),
                    category=category_entry.get().strip(),
                    selling_price=selling_price,
                    cost_price=cost_price,
                    ingredients=ingredients_text.get("1.0", tk.END).strip(),
                    description=description_text.get("1.0", tk.END).strip(),
                    stock=stock,
                    available_dates_list=available_dates,
                    restaurant_id=restaurant_id
                )
                
                messagebox.showinfo("موفقیت", f"غذای '{food.name}' با موفقیت اضافه شد")
                dialog.destroy()
                self.show_food_management()
                
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در ذخیره غذا: {str(e)}")
        
        # buttons (only once created)
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="ذخیره", 
                command=save_food_local, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="انصراف", 
                command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=10)
    
    def edit_food(self, tree):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("خطا", "لطفاً یک غذا انتخاب کنید")
            return
        
        item_values = tree.item(selected_item[0])['values']
        food_id_short = item_values[0]
        
        # find food
        foods = self.admin_service.food_service.get_all_foods()
        selected_food = None
        for food in foods:
            if food.food_id.startswith(food_id_short[:8]):
                selected_food = food
                break
        
        if not selected_food:
            messagebox.showerror("خطا", "غذا پیدا نشد")
            return
        
        # display edit dialog
        field = simpledialog.askstring("ویرایش", 
                                     f"ویرایش {selected_food.name}\n\n"
                                     f"1. نام\n2. دسته‌بندی\n3. قیمت فروش\n4. قیمت تمام شده\n"
                                     f"5. موجودی\n6. توضیحات\n\n"
                                     f"شماره فیلد را وارد کنید:", parent=self.root)
        
        if not field:
            return
        
        try:
            field_num = int(field)
            field_name = ""
            current_value = ""
            
            if field_num == 1:
                field_name = "name"
                current_value = selected_food.name
            elif field_num == 2:
                field_name = "category"
                current_value = selected_food.category
            elif field_num == 3:
                field_name = "selling_price"
                current_value = selected_food.selling_price
            elif field_num == 4:
                field_name = "cost_price"
                current_value = selected_food.cost_price
            elif field_num == 5:
                field_name = "stock"
                current_value = selected_food.stock
            elif field_num == 6:
                field_name = "description"
                current_value = selected_food.description
            else:
                messagebox.showerror("خطا", "شماره فیلد نامعتبر است")
                return
            
            new_value = simpledialog.askstring("مقدار جدید", 
                                             f"مقدار جدید برای {field_name} (فعلی: {current_value}):",
                                             parent=self.root)
            
            if new_value:
                # convert data type
                if field_name in ['selling_price', 'cost_price']:
                    new_value = float(new_value)
                elif field_name == 'stock':
                    new_value = int(new_value)
                
                # update
                self.admin_service.update_food_info(selected_food.food_id, **{field_name: new_value})
                messagebox.showinfo("موفقیت", "غذا با موفقیت به‌روزرسانی شد")
                self.show_food_management()
                
        except ValueError as e:
            messagebox.showerror("خطا", str(e))
    
    def delete_food(self, tree):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("خطا", "لطفاً یک غذا انتخاب کنید")
            return
        
        item_values = tree.item(selected_item[0])['values']
        food_name = item_values[1]
        
        if messagebox.askyesno("حذف غذا", f"آیا مطمئن هستید که می‌خواهید '{food_name}' را حذف کنید؟"):
            # find food_id
            foods = self.admin_service.food_service.get_all_foods()
            for food in foods:
                if food.name == food_name:
                    self.admin_service.delete_food(food.food_id)
                    messagebox.showinfo("موفقیت", f"غذای {food_name} حذف شد")
                    self.show_food_management()
                    return
    
    def show_order_management(self):
        self.clear_window()
        
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="بازگشت", 
                  command=self.create_admin_dashboard).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="مدیریت سفارشات", 
                 font=self.title_font).pack(side=tk.LEFT, padx=20)
        
        # get all orders
        orders = self.admin_service.get_all_orders()
        
        if not orders:
            ttk.Label(self.root, text="هیچ سفارشی وجود ندارد", 
                     font=self.font).pack(pady=50)
            return
        
        # Treeview for displaying orders
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("کد سفارش", "مشتری", "تاریخ", "وضعیت", "مبلغ کل", "روش پرداخت")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("کد سفارش", width=120)
        tree.column("مشتری", width=150)
        tree.column("تاریخ", width=120)
        tree.column("وضعیت", width=100)
        tree.column("مبلغ کل", width=100)
        tree.column("روش پرداخت", width=120)
        
        for order in orders:
            tree.insert("", tk.END, values=(
                order['order_id'][:10] + "...",
                order['customer_name'],
                order['date'],
                order['status'],
                f"{order['total_amount']:,.0f}",
                order['payment_method']
            ))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # buttons frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="تغییر وضعیت", 
                  command=lambda: self.change_order_status(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="بروزرسانی", 
                  command=self.show_order_management).pack(side=tk.LEFT, padx=5)
    
    def change_order_status(self, tree):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("خطا", "لطفاً یک سفارش انتخاب کنید")
            return
        
        item_values = tree.item(selected_item[0])['values']
        order_id_short = item_values[0]
        current_status = item_values[3]
        
        # find order_id
        orders = self.admin_service.get_all_orders()
        selected_order = None
        for order in orders:
            if order['order_id'].startswith(order_id_short[:10]):
                selected_order = order
                break
        
        if not selected_order:
            messagebox.showerror("خطا", "سفارش پیدا نشد")
            return
        
        # select new status dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("تغییر وضعیت سفارش")
        dialog.geometry("300x200")
        
        ttk.Label(dialog, text=f"سفارش: {selected_order['order_id'][:15]}...").pack(pady=10)
        ttk.Label(dialog, text=f"وضعیت فعلی: {current_status}").pack(pady=5)
        
        # possible statuses
        status_var = tk.StringVar(value=current_status)
        
        statuses = ["Pending", "Paid", "Sent", "Cancelled"]
        for status in statuses:
            ttk.Radiobutton(dialog, text=status, 
                           variable=status_var, value=status).pack(anchor=tk.W)
        
        def update_status():
            try:
                self.admin_service.update_order_status(
                    selected_order['order_id'], 
                    status_var.get()
                )
                messagebox.showinfo("موفقیت", "وضعیت سفارش به‌روزرسانی شد")
                dialog.destroy()
                self.show_order_management()
            except ValueError as e:
                messagebox.showerror("خطا", str(e))
        
        ttk.Button(dialog, text="بروزرسانی", 
                  command=update_status).pack(pady=15)
    
    def show_sales_reports(self):
        self.clear_window()
        
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="بازگشت", 
                  command=self.create_admin_dashboard).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="گزارشات فروش", 
                 font=self.title_font).pack(side=tk.LEFT, padx=20)
        
        # select date frame
        date_frame = ttk.LabelFrame(self.root, text="انتخاب بازه زمانی", padding=15)
        date_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(date_frame, text="از تاریخ:").grid(row=0, column=0, padx=5, pady=5)
        start_day = ttk.Spinbox(date_frame, from_=1, to=31, width=5, 
                               value=date.today().day)
        start_day.grid(row=0, column=1, padx=5, pady=5)
        
        start_month = ttk.Spinbox(date_frame, from_=1, to=12, width=5,
                                 value=date.today().month)
        start_month.grid(row=0, column=2, padx=5, pady=5)
        
        start_year = ttk.Spinbox(date_frame, from_=2023, to=2025, width=7,
                                value=date.today().year)
        start_year.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(date_frame, text="تا تاریخ:").grid(row=1, column=0, padx=5, pady=5)
        end_day = ttk.Spinbox(date_frame, from_=1, to=31, width=5,
                             value=date.today().day)
        end_day.grid(row=1, column=1, padx=5, pady=5)
        
        end_month = ttk.Spinbox(date_frame, from_=1, to=12, width=5,
                               value=date.today().month)
        end_month.grid(row=1, column=2, padx=5, pady=5)
        
        end_year = ttk.Spinbox(date_frame, from_=2023, to=2025, width=7,
                              value=date.today().year)
        end_year.grid(row=1, column=3, padx=5, pady=5)
        
        def generate_report():
            try:
                start_date = date(
                    int(start_year.get()),
                    int(start_month.get()),
                    int(start_day.get())
                )
                end_date = date(
                    int(end_year.get()),
                    int(end_month.get()),
                    int(end_day.get())
                )
                
                if start_date > end_date:
                    messagebox.showerror("خطا", "تاریخ شروع باید قبل از تاریخ پایان باشد")
                    return
                
                report = self.admin_service.get_sales_report(start_date, end_date)
                
                # display report
                report_text = (
                    f"📊 گزارش فروش\n"
                    f"بازه زمانی: {report['start_date']} تا {report['end_date']}\n"
                    f"────────────────\n"
                    f"تعداد سفارشات: {report['order_count']}\n"
                    f"فروش کل: {report['total_sales']:,.0f} تومان\n"
                    f"سود خالص: {report['total_profit']:,.0f} تومان\n"
                    f"────────────────\n"
                    f"میانگین هر سفارش: {report['total_sales']/max(report['order_count'], 1):,.0f} تومان"
                )
                
                # display report window
                report_window = tk.Toplevel(self.root)
                report_window.title("گزارش فروش")
                report_window.geometry("400x300")
                
                text_widget = tk.Text(report_window, font=("Tahoma", 11), padx=10, pady=10)
                text_widget.pack(fill=tk.BOTH, expand=True)
                
                text_widget.insert("1.0", report_text)
                text_widget.config(state=tk.DISABLED)
                
                # draw chart button
                ttk.Button(report_window, text="📈 رسم نمودار", 
                          command=self.show_sales_and_profit_chart).pack(pady=10)
                
            except ValueError as e:
                messagebox.showerror("خطا", "تاریخ نامعتبر است")
        
        ttk.Button(date_frame, text="تولید گزارش", 
                  command=generate_report).grid(row=2, column=0, columnspan=4, pady=15)
    
    def create_admin_discount(self):
        # create discount for customer
        customer_id = simpledialog.askstring("ایجاد کد تخفیف", 
                                           "شناسه مشتری را وارد کنید:", parent=self.root)
        if not customer_id:
            return
        
        # get discount percentage
        discount_percent = simpledialog.askfloat("درصد تخفیف", 
                                               "درصد تخفیف را وارد کنید (0-100):",
                                               parent=self.root, minvalue=0, maxvalue=100)
        if discount_percent is None:
            return
        
        try:
            discount = self.admin_service.create_discount_for_customer(
                customer_id, discount_percent
            )
            
            messagebox.showinfo("موفقیت", 
                              f"کد تخفیف ایجاد شد:\n\n"
                              f"کد: {discount.code}\n"
                              f"تخفیف: {discount.discount_percentage}%\n"
                              f"معتبر تا: {discount.expiry_date.strftime('%Y-%m-%d')}\n"
                              f"برای مشتری: {customer_id}")
        except ValueError as e:
            messagebox.showerror("خطا", str(e))
    
    # -------------------------------------------------------
    # public functions
    # -------------------------------------------------------
    def logout(self):
        self.current_user = None
        self.user_role = None
        self.cart = Cart()
        self.create_login_page()

    def edit_quantity(self, tree=None):
        """Editing food quantity in Carts""" 
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("خطا", "لطفاً یک آیتم از سبد خرید انتخاب کنید")
            return
        
        item_values = tree.item(selected_item[0])['values']
        food_name = item_values[0]
        current_quantity = int(item_values[2])  # current value
        
        # find food_id
        food_id = None
        for item in self.cart.items:
            if item.food.name == food_name:
                food_id = item.food.food_id
                food_obj = item.food
                break
        
        if not food_id:
            messagebox.showerror("خطا", "غذا در سبد خرید پیدا نشد")
            return
        
        # dialog for getting new quantity
        dialog = tk.Toplevel(self.root)
        dialog.title(f"ویرایش تعداد {food_name}")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"ویرایش تعداد '{food_name}'", 
                 font=self.title_font).pack(pady=10)
        
        ttk.Label(dialog, text=f"موجودی: {food_obj.stock}").pack(pady=5)
        ttk.Label(dialog, text=f"تعداد فعلی: {current_quantity}").pack(pady=5)
        
        # Spinbox for selecting quantity
        quantity_var = tk.IntVar(value=current_quantity)
        spinbox = ttk.Spinbox(
            dialog, 
            from_=1, 
            to=food_obj.stock, 
            textvariable=quantity_var,
            width=10,
            font=self.font
        )
        spinbox.pack(pady=10)
        
        def update_quantity():
            new_quantity = quantity_var.get()
            
            if new_quantity <= 0:
                messagebox.showerror("خطا", "تعداد باید بیشتر از صفر باشد")
                return
            
            try:
                # update quantity in cart
                self.food_service.update_cart_item_quantity(
                    self.cart, 
                    food_id, 
                    new_quantity
                )
                
                messagebox.showinfo("موفقیت", f"تعداد {food_name} به {new_quantity} تغییر کرد")
                dialog.destroy()
                self.show_cart()  # reset cart page
                
            except ValueError as e:
                messagebox.showerror("خطا", str(e))
        
        # buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="بروزرسانی", 
                  command=update_quantity, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="انصراف", 
                  command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)   


    def submit_review_dialog(self, order):
        """submitting reviews"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"ثبت نظر برای سفارش {order['order_id'][:10]}...")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # title
        ttk.Label(dialog, text="ثبت نظر و امتیازدهی", 
                 font=self.title_font).pack(pady=10)
        
        # select food for review (optional)
        ttk.Label(dialog, text="انتخاب غذا (اختیاری):", 
                 font=self.font).pack(pady=5, anchor=tk.W, padx=10)
        
        food_var = tk.StringVar(value="همه غذاها")
        food_combo = ttk.Combobox(dialog, textvariable=food_var, 
                                 width=30, font=self.font, state="readonly")
        food_items = ["همه غذاها"] + [item['food_name'] for item in order['items']]
        food_combo['values'] = food_items
        food_combo.pack(pady=5, padx=10, fill=tk.X)
        
        # rating
        ttk.Label(dialog, text="امتیاز (۱ تا ۵):", 
                 font=self.font).pack(pady=10, anchor=tk.W, padx=10)
        
        rating_frame = ttk.Frame(dialog)
        rating_frame.pack(pady=5, padx=10, fill=tk.X)
        
        rating_var = tk.IntVar(value=5)
        
        for i in range(1, 6):
            ttk.Radiobutton(rating_frame, text=str(i), 
                          variable=rating_var, value=i).pack(side=tk.LEFT, padx=5)
        
        # comment
        ttk.Label(dialog, text="نظر شما:", 
                 font=self.font).pack(pady=10, anchor=tk.W, padx=10)
        
        comment_text = tk.Text(dialog, height=6, width=40, font=self.font)
        comment_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        # submit review function
        def submit_review():
            try:
                food_name = food_var.get()
                if food_name == "همه غذاها":
                    food_name = None
                
                rating = rating_var.get()
                comment = comment_text.get("1.0", tk.END).strip()
                
                if not comment:
                    if messagebox.askokcancel("تأیید", 
                                            "آیا مطمئن هستید که می‌خواهید نظر بدون متن ثبت کنید؟"):
                        comment = "بدون نظر"
                    else:
                        return
                
                # submit review
                self.customer_service.submit_review(
                    customer_id=self.current_user.user_id,
                    order_id=order['order_id'],
                    rating=rating,
                    comment=f"{'برای ' + food_name + ': ' if food_name else ''}{comment}"
                )
                
                messagebox.showinfo("موفقیت", "نظر شما با موفقیت ثبت شد")
                dialog.destroy()
                
            except ValueError as e:
                messagebox.showerror("خطا", str(e))
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در ثبت نظر: {str(e)}")
        
        # buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        ttk.Button(btn_frame, text="ثبت نظر", 
                  command=submit_review, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="انصراف", 
                  command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5) 


    def show_order_reviews(self, order_id):
        """نمایش نظرات ثبت شده برای یک سفارش"""
        # get reviews from database
        reviews_df = self.db.get_reviews_by_order(order_id)
        
        if reviews_df.empty:
            messagebox.showinfo("نظرات", "هنوز نظری برای این سفارش ثبت نشده است")
            return
        
        # create review window
        dialog = tk.Toplevel(self.root)
        dialog.title(f"نظرات سفارش {order_id[:10]}...")
        dialog.geometry("500x400")
        
        # Treeview for displaying reviews
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("امتیاز", "نظر", "تاریخ")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        
        tree.heading("امتیاز", text="امتیاز")
        tree.heading("نظر", text="نظر")
        tree.heading("تاریخ", text="تاریخ")
        
        tree.column("امتیاز", width=80)
        tree.column("نظر", width=300)
        tree.column("تاریخ", width=100)
        
        for _, row in reviews_df.iterrows():
            # convert rating to stars
            stars = "★" * int(row['rating']) + "☆" * (5 - int(row['rating']))
            
            tree.insert("", tk.END, values=(
                stars,
                row['comment'][:50] + "..." if len(row['comment']) > 50 else row['comment'],
                row['review_date'][:10]
            ))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # close button
        ttk.Button(dialog, text="بستن", 
                  command=dialog.destroy).pack(pady=10)


    def show_my_reviews(self):
        """نمایش تمام نظرات ثبت شده توسط کاربر"""
        self.clear_window()
        
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="بازگشت", 
                  command=self.create_customer_dashboard).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="نظرات من", 
                 font=self.title_font).pack(side=tk.LEFT, padx=20)
        
        # get all user reviews
        reviews_df = pd.read_csv(self.db.reviews_file)
        user_reviews = reviews_df[reviews_df['customer_id'] == self.current_user.user_id]
        
        if user_reviews.empty:
            ttk.Label(self.root, text="شما هنوز نظری ثبت نکرده‌اید", 
                     font=self.font).pack(pady=50)
            return
        
        # Treeview for displaying reviews
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("سفارش", "امتیاز", "نظر", "تاریخ")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        tree.heading("سفارش", text="کد سفارش")
        tree.heading("امتیاز", text="امتیاز")
        tree.heading("نظر", text="نظر")
        tree.heading("تاریخ", text="تاریخ")
        
        tree.column("سفارش", width=120)
        tree.column("امتیاز", width=80)
        tree.column("نظر", width=250)
        tree.column("تاریخ", width=100)
        
        for _, row in user_reviews.iterrows():
            # convert rating to stars
            stars = "★" * int(row['rating']) + "☆" * (5 - int(row['rating']))
            
            tree.insert("", tk.END, values=(
                row['order_id'][:10] + "...",
                stars,
                row['comment'][:40] + "..." if len(row['comment']) > 40 else row['comment'],
                row['review_date'][:10]
            ))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)   

    def create_sales_report_page(self):
        self.clear_window()
        
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="گزارش فروش و سود", font=self.title_font).pack(pady=15)
        
        # ── input date ────────────────────────────────
        date_frame = ttk.Frame(main_frame)
        date_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(date_frame, text="از تاریخ (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)
        self.start_date_entry = ttk.Entry(date_frame, width=15)
        self.start_date_entry.pack(side=tk.LEFT, padx=5)
        self.start_date_entry.insert(0, (date.today() - timedelta(days=30)).strftime("%Y-%m-%d"))
        
        ttk.Label(date_frame, text="تا تاریخ (YYYY-MM-DD):").pack(side=tk.LEFT, padx=20)
        self.end_date_entry = ttk.Entry(date_frame, width=15)
        self.end_date_entry.pack(side=tk.LEFT, padx=5)
        self.end_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        
        # show button
        ttk.Button(
            main_frame, 
            text="نمایش گزارش و نمودار", 
            command=self.show_sales_and_profit_chart,
            width=25
        ).pack(pady=15)
        
        # where the chart will be placed
        self.chart_frame = ttk.Frame(main_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # return button
        ttk.Button(main_frame, text="بازگشت به داشبورد", 
                command=self.create_admin_dashboard).pack(pady=10)         

    def show_sales_and_profit_chart(self):
        try:
            start_str = self.start_date_entry.get().strip()
            end_str   = self.end_date_entry.get().strip()
            
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date   = datetime.strptime(end_str,   "%Y-%m-%d").date()
            
            if start_date > end_date:
                messagebox.showerror("خطا", "تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد")
                return
                
            # get data from service
            report = self.admin_service.get_sales_report(start_date, end_date)
            
            # summary text (optional)
            summary_text = (
                f"تعداد سفارش‌ها: {report['order_count']}\n"
                f"جمع فروش: {report['total_sales']:,.0f} تومان\n"
                f"جمع سود: {report['total_profit']:,.0f} تومان"
            )
            messagebox.showinfo("خلاصه گزارش", summary_text)   # or display in label
            
            #draw chart
            fig = Figure(figsize=(7, 4), dpi=100)
            ax = fig.add_subplot(111)
            
            categories = ['فروش کل', 'سود خالص']
            values = [report['total_sales'], report['total_profit']]
            colors = ['#4e79a7', '#76b7b2']
            
            bars = ax.bar(categories, values, color=colors, width=0.5)
            
            ax.set_title(f"گزارش فروش و سود\nاز {start_str} تا {end_str}", fontsize=12)
            ax.set_ylabel("مبلغ (تومان)", fontsize=10)
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            
            # display number on columns
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height,
                        f"{int(height):,}", ha='center', va='bottom', fontsize=10)
            
            # delete previous chart if exists
            for widget in self.chart_frame.winfo_children():
                widget.destroy()
            
            # display chart in tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.root.update_idletasks()       
            self.chart_frame.update()
            
        except ValueError as e:
            messagebox.showerror("خطا در تاریخ", f"فرمت تاریخ نامعتبر است\n{e}")
        except Exception as e:
            messagebox.showerror("خطا", f"مشکلی پیش آمد:\n{str(e)}")
    # -------------------------------------------------------
    # scraping and price comparison pages
    # -------------------------------------------------------
    
    def show_scraping_page(self):
        """صفحه اسکرپ قیمت‌های Snappfood"""
        self.clear_window()
        
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="بازگشت", 
                  command=self.create_admin_dashboard).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="اسکرپ قیمت‌های Snappfood", 
                 font=self.title_font).pack(side=tk.LEFT, padx=20)
        
        # main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # restaurant link
        ttk.Label(main_frame, text="لینک رستوران در Snappfood:", 
                 font=self.font).pack(anchor=tk.W, pady=5)
        
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        self.scraping_url = ttk.Entry(url_frame, width=60, font=self.font)
        self.scraping_url.pack(side=tk.LEFT, padx=5)
        self.scraping_url.insert(0, "https://snappfood.ir/restaurant/menu/...")
        
        # scraping status
        self.scraping_status = tk.StringVar(value="آماده")
        status_label = ttk.Label(main_frame, textvariable=self.scraping_status,
                                font=("Tahoma", 11), foreground="blue")
        status_label.pack(pady=10)
        
        # buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="شروع اسکرپ", 
                  command=self.start_scraping_thread, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="نمایش نتایج", 
                  command=self.show_scraping_results, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="ذخیره به CSV", 
                  command=self.save_scraping_results, width=15).pack(side=tk.LEFT, padx=5)
        
        # Treeview for displaying results
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        columns = ("نام غذا", "قیمت", "توضیحات", "تخفیف")
        self.scraping_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.scraping_tree.heading(col, text=col)
        
        self.scraping_tree.column("نام غذا", width=150)
        self.scraping_tree.column("قیمت", width=100)
        self.scraping_tree.column("توضیحات", width=200)
        self.scraping_tree.column("تخفیف", width=80)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.scraping_tree.yview)
        self.scraping_tree.configure(yscrollcommand=scrollbar.set)
        
        self.scraping_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # save results
        self.scraped_items = []
    
    def start_scraping_thread(self):
        """start scraping in a separate thread"""
        url = self.scraping_url.get().strip()
        if not url:
            messagebox.showwarning("خطا", "لطفا لینک رستوران را وارد کنید")
            return
        
        self.scraping_status.set("در حال اسکرپ... لطفا صبر کنید")
        
        # use thread to prevent GUI from freezing
        def scraping_task():
            try:
                items = self.snappfood_scraper.scrape_menu(url)
                self.scraped_items = items
                
                # update GUI from main thread
                self.root.after(0, self.update_scraping_results, items)
                
            except Exception as e:
                self.root.after(0, lambda: self.scraping_status.set(f"خطا: {str(e)}"))
        
        threading.Thread(target=scraping_task, daemon=True).start()
    
    def update_scraping_results(self, items):
        """update Treeview with scraping results"""
        # removing previous results
        for item in self.scraping_tree.get_children():
            self.scraping_tree.delete(item)
        
        # add new items
        for item in items:
            self.scraping_tree.insert("", tk.END, values=(
                item['food_name'],
                f"{item['price']:,}",
                item.get('description', ''),
                item.get('discount', '0%')
            ))
        
        self.scraping_status.set(f"اسکرپ کامل شد. {len(items)} آیتم یافت شد.")
    
    def show_scraping_results(self):
        """display scraping results"""
        if not self.scraped_items:
            messagebox.showinfo("نتایج", "هیچ داده‌ای برای نمایش وجود ندارد")
            return
        
        result_text = f"تعداد غذاهای یافت شده: {len(self.scraped_items)}\n\n"
        for item in self.scraped_items[:10]:  # only first 10 items
            result_text += f"• {item['food_name']}: {item['price']:,} تومان\n"
        
        messagebox.showinfo("نتایج اسکرپ", result_text)
    
    def save_scraping_results(self):
        """save scraping results to CSV file"""
        if not self.scraped_items:
            messagebox.showwarning("خطا", "هیچ داده‌ای برای ذخیره وجود ندارد")
            return
        
        try:
            # convert to DataFrame
            df = pd.DataFrame(self.scraped_items)
            
            # save with current timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snappfood_scraped_{timestamp}.csv"
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            messagebox.showinfo("موفقیت", f"نتایج در فایل {filename} ذخیره شد")
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در ذخیره فایل: {str(e)}")
    
    def show_price_comparison(self):
        """price comparison page"""
        self.clear_window()
        
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="بازگشت", 
                  command=self.create_admin_dashboard).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="مقایسه قیمت با رقبا", 
                 font=self.title_font).pack(side=tk.LEFT, padx=20)
        
        # main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # select files
        ttk.Label(main_frame, text="فایل قیمت‌های ما:", 
                 font=self.font).pack(anchor=tk.W, pady=5)
        
        our_file_frame = ttk.Frame(main_frame)
        our_file_frame.pack(fill=tk.X, pady=5)
        
        self.our_prices_file = ttk.Entry(our_file_frame, width=40, font=self.font)
        self.our_prices_file.pack(side=tk.LEFT, padx=5)
        self.our_prices_file.insert(0, "our_prices.csv")
        
        ttk.Button(our_file_frame, text="انتخاب فایل", 
                  command=self.select_our_file).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(main_frame, text="فایل قیمت‌های رقبا:", 
                 font=self.font).pack(anchor=tk.W, pady=10)
        
        comp_file_frame = ttk.Frame(main_frame)
        comp_file_frame.pack(fill=tk.X, pady=5)
        
        self.comp_prices_file = ttk.Entry(comp_file_frame, width=40, font=self.font)
        self.comp_prices_file.pack(side=tk.LEFT, padx=5)
        self.comp_prices_file.insert(0, "competitor_prices.csv")
        
        ttk.Button(comp_file_frame, text="انتخاب فایل", 
                  command=self.select_comp_file).pack(side=tk.LEFT, padx=5)
        
        # buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="بارگذاری و مقایسه", 
                  command=self.load_and_compare, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="نمایش گزارش", 
                  command=self.show_comparison_report, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="ذخیره گزارش", 
                  command=self.save_comparison_report, width=20).pack(side=tk.LEFT, padx=5)
        
        # status
        self.comparison_status = tk.StringVar(value="آماده")
        status_label = ttk.Label(main_frame, textvariable=self.comparison_status,
                                font=("Tahoma", 11), foreground="blue")
        status_label.pack(pady=10)
    
    def select_our_file(self):
        """select our prices file"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="فایل قیمت‌های ما را انتخاب کنید",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.our_prices_file.delete(0, tk.END)
            self.our_prices_file.insert(0, filename)
    
    def select_comp_file(self):
        """انتخاب فایل قیمت‌های رقبا"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="فایل قیمت‌های رقبا را انتخاب کنید",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.comp_prices_file.delete(0, tk.END)
            self.comp_prices_file.insert(0, filename)
    
    def load_and_compare(self):
        """loading files and comparing prices"""
        our_file = self.our_prices_file.get().strip()
        comp_file = self.comp_prices_file.get().strip()

        if not our_file or not comp_file:
            messagebox.showwarning("خطا", "لطفاً هر دو فایل را انتخاب کنید")
            return

        try:
            # 1. reading files with appropriate encoding for Persian
            our_df = pd.read_csv(our_file, encoding='utf-8-sig')
            comp_df = pd.read_csv(comp_file, encoding='utf-8-sig')

            # 2. standardizing column names (more flexible)
            our_df = our_df.rename(columns={
                'نام غذا': 'name',
                'نام': 'name',
                'غذا': 'name',
                'قیمت فروش': 'our_price',
                'selling_price': 'our_price',
                'قیمت': 'our_price'
            })

            comp_df = comp_df.rename(columns={
                'food_name': 'name',
                'نام غذا': 'name',
                'نام': 'name',
                'price': 'comp_price',
                'قیمت': 'comp_price',
                'قیمت اصلی': 'comp_price'
            })

            # checking for required columns
            required_our = {'name', 'our_price'}
            required_comp = {'name', 'comp_price'}

            if not required_our.issubset(our_df.columns):
                missing = required_our - set(our_df.columns)
                raise ValueError(f"ستون‌های مورد نیاز در فایل خودمان پیدا نشد: {missing}")

            if not required_comp.issubset(comp_df.columns):
                missing = required_comp - set(comp_df.columns)
                raise ValueError(f"ستون‌های مورد نیاز در فایل رقبا پیدا نشد: {missing}")

            # 3. converting prices to numbers (if needed)
            our_df['our_price'] = pd.to_numeric(our_df['our_price'], errors='coerce')
            comp_df['comp_price'] = pd.to_numeric(comp_df['comp_price'], errors='coerce')

            # deleting rows with invalid prices
            our_df = our_df.dropna(subset=['our_price'])
            comp_df = comp_df.dropna(subset=['comp_price'])

            # 4. performing merge
            merged = pd.merge(
                our_df[['name', 'our_price']],
                comp_df[['name', 'comp_price']],
                on='name',
                how='inner'
            )

            if merged.empty:
                messagebox.showinfo("نتیجه مقایسه", "هیچ غذای مشترکی با نام مشابه پیدا نشد.")
                self.comparison_status.set("مقایسه انجام شد – ۰ مورد مشترک")
                return

            # 5. calculating difference and percentage
            merged['difference'] = merged['our_price'] - merged['comp_price']
            merged['percent'] = (merged['difference'] / merged['comp_price'] * 100).round(1)

            # 6. saving result for future use
            self.merged_df = merged          
            self.comparison_done = True      

            # 7. feedback to user
            msg = f"مقایسه با موفقیت انجام شد\nتعداد غذاهای مشترک: {len(merged)}\n"
            msg += f"میانگین اختلاف قیمت: {merged['difference'].mean():,.0f} تومان"

            messagebox.showinfo("موفقیت مقایسه", msg)
            self.comparison_status.set(f"مقایسه انجام شد – {len(merged)} مورد مشترک")

        except pd.errors.EmptyDataError:
            messagebox.showerror("خطا", "یکی از فایل‌ها خالی است یا ساختار درستی ندارد.")
        except UnicodeDecodeError:
            messagebox.showerror("خطا", "مشکل در خواندن فایل (encoding). فایل را با UTF-8 ذخیره کنید.")
        except Exception as e:
            messagebox.showerror("خطا در بارگذاری یا مقایسه", str(e))
            self.comparison_status.set("خطا در فرآیند مقایسه")
    
    def show_comparison_report(self):
        if not hasattr(self, 'merged_df') or self.merged_df is None:
                messagebox.showwarning("خطا", "ابتدا فایل‌ها را بارگذاری و مقایسه کنید")
                return

        if self.merged_df.empty:
                messagebox.showinfo("گزارش", "هیچ مورد مشترکی برای نمایش وجود ندارد")
                return

            # here we can open the Treeview or report window
        summary = self.merged_df[['name', 'our_price', 'comp_price', 'difference', 'percent']].to_string(index=False)
        messagebox.showinfo("گزارش مقایسه", summary)
    
    def show_report_in_window(self, report_df):
        """display report in new window"""
        report_window = tk.Toplevel(self.root)
        report_window.title("گزارش مقایسه قیمت")
        report_window.geometry("800x500")
        
        # Treeview
        tree_frame = ttk.Frame(report_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ["غذا", "قیمت ما", "میانگین رقبا", "اختلاف", "درصد اختلاف", "وضعیت"]
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("غذا", width=150)
        tree.column("قیمت ما", width=100)
        tree.column("میانگین رقبا", width=100)
        tree.column("اختلاف", width=100)
        tree.column("درصد اختلاف", width=100)
        tree.column("وضعیت", width=100)
        
        for _, row in report_df.iterrows():
            status_text = "ارزان‌تر" if row['price_difference'] < 0 else "گران‌تر"
            status_color = "green" if row['price_difference'] < 0 else "red"
            
            tree.insert("", tk.END, values=(
                row['our_food'],
                f"{row['our_price']:,}",
                f"{row['avg_competitor_price']:,}",
                f"{row['price_difference']:,}",
                f"{row['price_difference_percent']:.1f}%",
                status_text
            ))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # summary
        summary_frame = ttk.Frame(report_window)
        summary_frame.pack(pady=10)
        
        cheaper_count = len(report_df[report_df['status'] == 'Cheaper'])
        expensive_count = len(report_df[report_df['status'] == 'More Expensive'])
        
        ttk.Label(summary_frame, 
                 text=f"ارزان‌تر: {cheaper_count} مورد | گران‌تر: {expensive_count} مورد",
                 font=("Tahoma", 11, "bold")).pack()
    
    def save_comparison_report(self):
        """save comparison report"""
        if not hasattr(self, 'merged_df') or self.merged_df is None or self.merged_df.empty:
            messagebox.showwarning("خطا", "ابتدا فایل‌ها را بارگذاری و مقایسه کنید")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"price_comparison_report_{timestamp}.csv"
        self.merged_df.to_csv(filename, index=False, encoding='utf-8-sig')
        messagebox.showinfo("ذخیره موفق", f"گزارش در فایل {filename} ذخیره شد")
    
    def show_comparison_chart(self):
        """display price comparison chart"""
        if not self.price_comparator:
            messagebox.showwarning("خطا", "لطفا ابتدا فایل‌ها را بارگذاری کنید")
            return
        
        try:
            self.price_comparator.plot_price_comparison()
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در رسم نمودار: {str(e)}")
    
    def show_multi_scraping(self):
        """scrape multiple restaurants at once"""
        self.clear_window()
        
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="بازگشت", 
                  command=self.create_admin_dashboard).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="اسکرپ همزمان چند رستوران", 
                 font=self.title_font).pack(side=tk.LEFT, padx=20)
        
        # main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # list of links
        ttk.Label(main_frame, text="لینک‌های رستوران‌ها (هر لینک در یک خط):", 
                 font=self.font).pack(anchor=tk.W, pady=5)
        
        self.urls_text = tk.Text(main_frame, width=70, height=10, font=self.font)
        self.urls_text.pack(pady=5)
        self.urls_text.insert("1.0", "https://snappfood.ir/restaurant/menu/...\nhttps://snappfood.ir/restaurant/menu/...")
        
        # status
        self.multi_status = tk.StringVar(value="آماده")
        status_label = ttk.Label(main_frame, textvariable=self.multi_status,
                                font=("Tahoma", 11), foreground="blue")
        status_label.pack(pady=10)
        
        # buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="شروع اسکرپ همزمان", 
                  command=self.start_multi_scraping, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="توقف همه اسکرپ‌ها", 
                  command=self.stop_all_scraping, width=20).pack(side=tk.LEFT, padx=5)
        
        # results
        results_frame = ttk.LabelFrame(main_frame, text="نتایج", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.results_text = tk.Text(results_frame, width=70, height=15, font=self.font)
        self.results_text.pack(fill=tk.BOTH, expand=True)
    
    def start_multi_scraping(self):
        """start scraping multiple restaurants at once"""
        urls_text = self.urls_text.get("1.0", tk.END).strip()
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        if not urls:
            messagebox.showwarning("خطا", "لطفا حداقل یک لینک وارد کنید")
            return
        
        self.multi_status.set(f"در حال اسکرپ {len(urls)} رستوران...")
        self.results_text.delete("1.0", tk.END)
        
        def scraping_task():
            all_results = []
            for i, url in enumerate(urls, 1):
                try:
                    # update status
                    status = f"در حال اسکرپ رستوران {i} از {len(urls)}..."
                    self.root.after(0, lambda s=status: self.multi_status.set(s))
                    
                    # scrape
                    items = self.snappfood_scraper.scrape_menu(url)
                    
                    # display results
                    result_text = f"رستوران {i}: {len(items)} آیتم یافت شد\n"
                    for item in items[:3]:  # only first 3 items
                        result_text += f"   • {item['food_name'][:30]}...: {item['price']:,}\n"
                    
                    self.root.after(0, lambda t=result_text: self.results_text.insert(tk.END, t + "\n"))
                    all_results.extend(items)
                    
                except Exception as e:
                    error_text = f" رستوران {i}: خطا - {str(e)}\n"
                    self.root.after(0, lambda t=error_text: self.results_text.insert(tk.END, t))
            
            # end
            self.root.after(0, lambda: self.multi_status.set(f"اسکرپ کامل شد. {len(all_results)} آیتم یافت شد."))
            
            # save all results
            if all_results:
                try:
                    df = pd.DataFrame(all_results)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"multi_scraped_{timestamp}.csv"
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                    
                    self.root.after(0, lambda: self.results_text.insert(
                        tk.END, f"\n📁 تمام نتایج در {filename} ذخیره شد\n"))
                except Exception as e:
                    self.root.after(0, lambda: self.results_text.insert(
                        tk.END, f"\nخطا در ذخیره: {str(e)}\n"))
        
        # execute in separate thread
        threading.Thread(target=scraping_task, daemon=True).start()
    
    def stop_all_scraping(self):
        """stop all scraping"""
        # add stop logic here
        self.multi_status.set("عملیات متوقف شد")
        self.results_text.insert(tk.END, "\n عملیات توسط کاربر متوقف شد\n")            

def main():
    root = tk.Tk()
    app = FoodDeliveryApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()