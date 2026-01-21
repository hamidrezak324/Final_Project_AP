# gui_app.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
from datetime import datetime, date, timedelta

# اضافه کردن مسیر فایل‌های پروژه به sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import AuthManager
from food_service import FoodService
from order_service import OrderService
from customer_service import CustomerService
from admin_service import AdminService
from model import Cart, Order
from database import Database

class FoodDeliveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("سامانه سفارش غذا")
        self.root.geometry("1000x700")
        
        # تنظیمات فونت
        self.font = ("Tahoma", 10)
        self.title_font = ("Tahoma", 14, "bold")
        
        # سرویس‌ها
        self.auth = AuthManager()
        self.food_service = FoodService()
        self.order_service = OrderService()
        self.customer_service = CustomerService()
        self.admin_service = AdminService()
        self.db = Database() 
        
        # وضعیت کاربر
        self.current_user = None
        self.user_role = None
        self.cart = Cart()
        self.selected_date = date.today()
        
        # ایجاد صفحات
        self.create_login_page()
    
    def clear_window(self):
        """پاک کردن محتوای فعلی پنجره"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    # -------------------------------------------------------
    # صفحه ورود/ثبت‌نام
    # -------------------------------------------------------
    def create_login_page(self):
        self.clear_window()
        
        # فریم اصلی
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # عنوان
        ttk.Label(main_frame, text="سامانه سفارش غذا", font=self.title_font).pack(pady=20)
        
        # فریم ورود
        login_frame = ttk.LabelFrame(main_frame, text="ورود کاربر", padding=15)
        login_frame.pack(fill=tk.X, pady=10)
        
        # ایمیل
        ttk.Label(login_frame, text="ایمیل:", font=self.font).grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.email_entry = ttk.Entry(login_frame, width=30, font=self.font)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # رمز عبور
        ttk.Label(login_frame, text="رمز عبور:", font=self.font).grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.password_entry = ttk.Entry(login_frame, width=30, show="*", font=self.font)
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # دکمه‌های ورود
        btn_frame = ttk.Frame(login_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        
        ttk.Button(btn_frame, text="ورود مشتری", 
                  command=self.login_customer, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="ورود ادمین", 
                  command=self.login_admin, width=15).pack(side=tk.LEFT, padx=5)
        
        # جداکننده
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)
        
        # دکمه ثبت‌نام
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
            messagebox.showwarning("خطا", "لطفا شناسه ایمیل و رمز عبور را وارد کنید")
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
    # صفحه ثبت‌نام
    # -------------------------------------------------------
    def create_register_page(self):
        self.clear_window()
        
        # فریم اصلی
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # عنوان
        ttk.Label(main_frame, text="ثبت‌نام مشتری جدید", font=self.title_font).pack(pady=10)
        
        # فرم ثبت‌نام
        form_frame = ttk.Frame(main_frame, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # ردیف 1: نام و نام خانوادگی
        ttk.Label(form_frame, text="نام:", font=self.font).grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.reg_firstname = ttk.Entry(form_frame, width=25, font=self.font)
        self.reg_firstname.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="نام خانوادگی:", font=self.font).grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)
        self.reg_lastname = ttk.Entry(form_frame, width=25, font=self.font)
        self.reg_lastname.grid(row=0, column=3, padx=5, pady=5)
        
        # ردیف 2: ایمیل
        ttk.Label(form_frame, text="ایمیل:", font=self.font).grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.reg_email = ttk.Entry(form_frame, width=60, font=self.font)
        self.reg_email.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # ردیف 3: رمز عبور
        ttk.Label(form_frame, text="رمز عبور:", font=self.font).grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.reg_password = ttk.Entry(form_frame, width=25, show="*", font=self.font)
        self.reg_password.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="تکرار رمز عبور:", font=self.font).grid(row=2, column=2, padx=5, pady=5, sticky=tk.E)
        self.reg_confirm = ttk.Entry(form_frame, width=25, show="*", font=self.font)
        self.reg_confirm.grid(row=2, column=3, padx=5, pady=5)
        
        # ردیف 4: تلفن و کد ملی
        ttk.Label(form_frame, text="تلفن همراه:", font=self.font).grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        self.reg_phone = ttk.Entry(form_frame, width=25, font=self.font)
        self.reg_phone.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="کد ملی:", font=self.font).grid(row=3, column=2, padx=5, pady=5, sticky=tk.E)
        self.reg_national = ttk.Entry(form_frame, width=25, font=self.font)
        self.reg_national.grid(row=3, column=3, padx=5, pady=5)
        
        # ردیف 5: آدرس
        ttk.Label(form_frame, text="آدرس:", font=self.font).grid(row=4, column=0, padx=5, pady=5, sticky=tk.NE)
        self.reg_address = tk.Text(form_frame, width=58, height=4, font=self.font)
        self.reg_address.grid(row=4, column=1, columnspan=3, padx=5, pady=5)
        
        # دکمه‌ها
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
    # داشبورد مشتری
    # -------------------------------------------------------
    def create_customer_dashboard(self):
        self.clear_window()
        
        # نوار منو
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # منوها
        user_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=f"کاربر: {self.current_user.full_name}", menu=user_menu)
        user_menu.add_command(label="پروفایل", command=self.show_profile)
        user_menu.add_command(label="سبد خرید", command=self.show_cart)
        user_menu.add_command(label="سفارشات من", command=self.show_order_history)
        user_menu.add_separator()
        user_menu.add_command(label="خروج", command=self.logout)
        
        # منوی غذاها
        food_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="منوی غذاها", menu=food_menu)
        food_menu.add_command(label="نمایش منوی امروز", command=self.show_today_menu)
        food_menu.add_command(label="جستجوی غذا", command=self.show_search_food)
        
        # منوی امتیازات
        points_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="امتیازات", menu=points_menu)
        points_menu.add_command(label="امتیازات من", command=self.show_loyalty_points)
        points_menu.add_command(label="تبدیل به کد تخفیف", command=self.convert_points)
        
        # صفحه خوش‌آمدگویی
        welcome_frame = ttk.Frame(self.root, padding=30)
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(welcome_frame, text=f"خوش آمدید {self.current_user.full_name}!", 
                 font=self.title_font).pack(pady=20)
        
        ttk.Label(welcome_frame, text="از منوی بالا برای دسترسی به امکانات استفاده کنید", 
                 font=self.font).pack(pady=10)
        
        # دکمه‌های سریع
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
        
        # نوار بالایی
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="بازگشت", 
                  command=self.create_customer_dashboard).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="منوی غذاهای امروز", 
                 font=self.title_font).pack(side=tk.LEFT, padx=20)
        
        # Treeview برای نمایش غذاها
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ستون‌ها
        columns = ("نام", "دسته‌بندی", "قیمت (تومان)", "موجودی", "توضیحات")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # تنظیم ستون‌ها
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
        
        # نوار اسکرول
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # دریافت غذاهای امروز
        foods = self.food_service.get_menu_for_date(date.today())
        
        for food in foods:
            tree.insert("", tk.END, values=(
                food.name,
                food.category,
                f"{food.selling_price:,.0f}",
                food.stock,
                food.description[:50] + "..." if len(food.description) > 50 else food.description
            ))
        
        # فریم دکمه‌ها
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
        
        # جستجوی غذا با نام
        foods = self.food_service.search_foods(food_name)
        if not foods:
            messagebox.showerror("خطا", "غذا پیدا نشد")
            return
        
        food = foods[0]
        
        # دریافت تعداد
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
        
        # نوار بالایی
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="بازگشت", 
                  command=self.create_customer_dashboard).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="سبد خرید من", 
                 font=self.title_font).pack(side=tk.LEFT, padx=20)
        
        if not self.cart.items:
            # سبد خرید خالی
            empty_frame = ttk.Frame(self.root, padding=50)
            empty_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(empty_frame, text="سبد خرید شما خالی است", 
                     font=self.title_font).pack(pady=20)
            ttk.Button(empty_frame, text="بازگشت به منو", 
                      command=self.show_today_menu).pack()
            return
        
        # Treeview برای نمایش سبد خرید
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("نام غذا", "قیمت واحد", "تعداد", "قیمت کل")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        
        tree.heading("نام غذا", text="نام غذا")
        tree.heading("قیمت واحد", text="قیمت واحد (تومان)")
        tree.heading("تعداد", text="تعداد")
        tree.heading("قیمت کل", text="قیمت کل (تومان)")
        
        tree.column("نام غذا", width=200)
        tree.column("قیمت واحد", width=120)
        tree.column("تعداد", width=80)
        tree.column("قیمت کل", width=120)
        
        # اضافه کردن آیتم‌ها
        total = 0
        for item in self.cart.items:
            item_total = item.total_price
            total += item_total
            tree.insert("", tk.END, values=(
                item.food.name,
                f"{item.unit_price:,.0f}",
                item.quantity,
                f"{item_total:,.0f}"
            ))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # نمایش مجموع
        total_frame = ttk.Frame(self.root)
        total_frame.pack(pady=10)
        
        ttk.Label(total_frame, text=f"مجموع سبد خرید: {total:,.0f} تومان", 
                 font=("Tahoma", 12, "bold")).pack()
        
        # فریم دکمه‌ها
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=15)
        
        ttk.Button(btn_frame, text="حذف انتخاب شده", 
                  command=lambda: self.remove_from_cart(tree)).pack(side=tk.LEFT, padx=5)
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
        
        # پیدا کردن food_id
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
        
        # تاریخ تحویل
        ttk.Label(dialog, text="تاریخ تحویل:", font=self.font).pack(pady=5)
        
        # استفاده از DateEntry ساده (در واقعیت از datepicker استفاده کنید)
        delivery_date = date.today() + timedelta(days=1)
        date_label = ttk.Label(dialog, text=delivery_date.strftime("%Y-%m-%d"), 
                              font=self.font, relief=tk.SUNKEN, width=15)
        date_label.pack(pady=5)
        
        # روش پرداخت
        ttk.Label(dialog, text="روش پرداخت:", font=self.font).pack(pady=5)
        payment_var = tk.StringVar(value=Order.PAYMENT_ONLINE)
        
        ttk.Radiobutton(dialog, text="پرداخت آنلاین", 
                       variable=payment_var, value=Order.PAYMENT_ONLINE).pack()
        ttk.Radiobutton(dialog, text="پرداخت نقدی هنگام تحویل", 
                       variable=payment_var, value=Order.PAYMENT_CASH).pack()
        
        # کد تخفیف
        ttk.Label(dialog, text="کد تخفیف (اختیاری):", font=self.font).pack(pady=5)
        discount_entry = ttk.Entry(dialog, width=20, font=self.font)
        discount_entry.pack()
        
        # دکمه‌ها
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
                
                # پرداخت
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
        
        # دریافت تاریخچه سفارشات
        orders = self.customer_service.get_order_history(self.current_user.user_id)
        
        if not orders:
            ttk.Label(self.root, text="شما هیچ سفارشی ندارید", 
                     font=self.font).pack(pady=50)
            return
        
        # Treeview برای نمایش سفارشات
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
        
        # دکمه مشاهده جزییات
        def show_order_details():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("خطا", "لطفاً یک سفارش انتخاب کنید")
                return
            
            item_values = tree.item(selected_item[0])['values']
            order_id_short = item_values[0]
            
            # پیدا کردن سفارش کامل
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
        dialog.geometry("600x500")
        
        # نمایش اطلاعات سفارش
        info_frame = ttk.LabelFrame(dialog, text="اطلاعات سفارش", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(info_frame, text=f"کد سفارش: {order['order_id']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"تاریخ: {order['date']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"وضعیت: {order['status']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"مبلغ کل: {order['total_amount']:,.0f} تومان").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"مبلغ پرداختی: {order['final_amount']:,.0f} تومان").pack(anchor=tk.W)
        
        # آیتم‌های سفارش
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
        
        # دکمه بستن
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
            
            # نمایش نتایج در یک پنجره جدید
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
    # داشبورد ادمین
    # -------------------------------------------------------
    def create_admin_dashboard(self):
        self.clear_window()
        
        # نوار منو
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # منوها
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
        
        # صفحه خوش‌آمدگویی ادمین
        welcome_frame = ttk.Frame(self.root, padding=30)
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(welcome_frame, text="پنل مدیریت رستوران", 
                 font=self.title_font).pack(pady=20)
        
        ttk.Label(welcome_frame, text=f"خوش آمدید ادمین {self.current_user.full_name}", 
                 font=self.font).pack(pady=10)
        
        # دکمه‌های سریع
        btn_frame = ttk.Frame(welcome_frame)
        btn_frame.pack(pady=30)
        
        ttk.Button(btn_frame, text="🍽️ مدیریت غذاها", 
                  command=self.show_food_management, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="📦 مدیریت سفارشات", 
                  command=self.show_order_management, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="📊 گزارشات فروش", 
                  command=self.show_sales_reports, width=20).pack(side=tk.LEFT, padx=10)
    
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
        
        # دکمه افزودن غذا
        ttk.Button(top_frame, text="➕ غذای جدید", 
                  command=self.show_add_food_dialog).pack(side=tk.RIGHT)
        
        # Treeview برای نمایش غذاها
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
        
        # دریافت همه غذاها
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
        
        # فریم دکمه‌ها
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
        
        # فرم
        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # متغیرهای محلی برای ورودی‌ها
        restaurant_id_entry = None
        name_entry = None
        category_entry = None
        selling_price_entry = None
        cost_price_entry = None
        stock_entry = None
        ingredients_text = None
        description_text = None
        dates_text = None
        
        # ردیف‌ها
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
        
        # توضیح تاریخ‌های موجودی
        row_index = len(rows)
        ttk.Label(form_frame, text="تاریخ‌های موجودی (به فرمت YYYY-MM-DD):").grid(
            row=row_index, column=0, columnspan=2, pady=10
        )
        
        dates_text = tk.Text(form_frame, width=40, height=4)
        dates_text.grid(row=row_index+1, column=0, columnspan=2, padx=5, pady=5)
        dates_text.insert("1.0", "هر تاریخ در یک خط\nمثال:\n2024-01-15\n2024-01-16\n2024-01-17")
        
        # تابع محلی برای ذخیره غذا
        def save_food_local():
            try:
                # دریافت شناسه رستوران
                restaurant_id = restaurant_id_entry.get().strip()
                if not restaurant_id:
                    messagebox.showerror("خطا", "شناسه رستوران نمی‌تواند خالی باشد")
                    return
                
                # بررسی سایر فیلدهای ضروری
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
                
                # تبدیل تاریخ‌ها
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
                
                # ایجاد غذا
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
        
        # دکمه‌ها (فقط یک بار ایجاد شوند)
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
        
        # پیدا کردن غذا
        foods = self.admin_service.food_service.get_all_foods()
        selected_food = None
        for food in foods:
            if food.food_id.startswith(food_id_short[:8]):
                selected_food = food
                break
        
        if not selected_food:
            messagebox.showerror("خطا", "غذا پیدا نشد")
            return
        
        # نمایش دیالوگ ویرایش
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
                # تبدیل نوع داده
                if field_name in ['selling_price', 'cost_price']:
                    new_value = float(new_value)
                elif field_name == 'stock':
                    new_value = int(new_value)
                
                # به‌روزرسانی
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
            # پیدا کردن food_id
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
        
        # دریافت همه سفارشات
        orders = self.admin_service.get_all_orders()
        
        if not orders:
            ttk.Label(self.root, text="هیچ سفارشی وجود ندارد", 
                     font=self.font).pack(pady=50)
            return
        
        # Treeview برای نمایش سفارشات
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
        
        # فریم دکمه‌ها
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
        
        # پیدا کردن order_id کامل
        orders = self.admin_service.get_all_orders()
        selected_order = None
        for order in orders:
            if order['order_id'].startswith(order_id_short[:10]):
                selected_order = order
                break
        
        if not selected_order:
            messagebox.showerror("خطا", "سفارش پیدا نشد")
            return
        
        # دیالوگ انتخاب وضعیت جدید
        dialog = tk.Toplevel(self.root)
        dialog.title("تغییر وضعیت سفارش")
        dialog.geometry("300x200")
        
        ttk.Label(dialog, text=f"سفارش: {selected_order['order_id'][:15]}...").pack(pady=10)
        ttk.Label(dialog, text=f"وضعیت فعلی: {current_status}").pack(pady=5)
        
        # وضعیت‌های ممکن
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
        
        # فریم انتخاب تاریخ
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
                
                # نمایش گزارش
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
                
                # پنجره نمایش گزارش
                report_window = tk.Toplevel(self.root)
                report_window.title("گزارش فروش")
                report_window.geometry("400x300")
                
                text_widget = tk.Text(report_window, font=("Tahoma", 11), padx=10, pady=10)
                text_widget.pack(fill=tk.BOTH, expand=True)
                
                text_widget.insert("1.0", report_text)
                text_widget.config(state=tk.DISABLED)
                
                # دکمه رسم نمودار
                ttk.Button(report_window, text="📈 رسم نمودار", 
                          command=lambda: self.admin_service.plot_sales_chart(start_date, end_date)).pack(pady=10)
                
            except ValueError as e:
                messagebox.showerror("خطا", "تاریخ نامعتبر است")
        
        ttk.Button(date_frame, text="تولید گزارش", 
                  command=generate_report).grid(row=2, column=0, columnspan=4, pady=15)
    
    def create_admin_discount(self):
        # دریافت شناسه مشتری
        customer_id = simpledialog.askstring("ایجاد کد تخفیف", 
                                           "شناسه مشتری را وارد کنید:", parent=self.root)
        if not customer_id:
            return
        
        # درصد تخفیف
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
    # توابع عمومی
    # -------------------------------------------------------
    def logout(self):
        self.current_user = None
        self.user_role = None
        self.cart = Cart()
        self.create_login_page()

def main():
    root = tk.Tk()
    app = FoodDeliveryApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()