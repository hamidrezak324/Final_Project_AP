import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from model import Review, DiscountCode, OrderItem
from database import Database

class CustomerService:
    def __init__(self):
        self.db = Database()

    # -------------------------------------------------------
    # Order History
    # -------------------------------------------------------
    def get_order_history(self, customer_id: str) -> List[dict]:
        """
        دریافت لیست سفارشات مشتری به همراه جزئیات.
        نکته: قیمت‌ها باید همان زمان خرید باشند (ثابت شده).
        """
        orders_df = self.db.get_customer_orders(customer_id)
        history = []

        for _, order_row in orders_df.iterrows():
            # دریافت آیتم‌های سفارش
            items_df = self.db.get_order_items(order_row['order_id'])
            
            # ساخت لیستی از جزئیات غذاها برای نمایش
            items_details = []
            for _, item_row in items_df.iterrows():
                items_details.append({
                    'food_name': item_row['food_id'], # نام غذا را می‌توان از روی food_id گرفتن (ساده‌سازی)
                    'quantity': int(item_row['quantity']),
                    'unit_price': float(item_row['unit_price']),
                    'total': int(item_row['quantity']) * float(item_row['unit_price'])
                })
            
            history.append({
                'order_id': order_row['order_id'],
                'date': order_row['order_date'],
                'status': order_row['status'],
                'total_amount': float(order_row['total_amount']) + float(order_row['discount_amount']), # مبلغ کل قبل از تخفیف یا بعد؟ معمولا مبلغ پرداختی نمایش داده می‌شود
                'final_amount': float(order_row['total_amount']),
                'items': items_details
            })
        
        return history

    # -------------------------------------------------------
    # Reviews
    # -------------------------------------------------------
    def submit_review(self, customer_id: str, order_id: str, rating: int, comment: str):
        """ثبت نظر برای یک سفارش"""
        # بررسی اینکه آیا قبلاً نظر داده است یا خیر (اختیاری ولی خوب است)
        existing = self.db.get_reviews_by_order(order_id)
        # اگر بخواهیم فقط یک نظر مجاز باشد:
        # if not existing.empty: raise ValueError("شما قبلاً برای این سفارش نظر ثبت کرده‌اید.")

        review = Review(
            review_id=str(uuid.uuid4()),
            customer_id=customer_id,
            order_id=order_id,
            rating=rating,
            comment=comment
        )
        self.db.save_review(review)

    # -------------------------------------------------------
    # Loyalty & Discounts
    # -------------------------------------------------------
    def get_user_points(self, customer_id: str) -> int:
        """دریافت امتیاز فعلی کاربر"""
        df = self.db.load_users()
        user = df[df['user_id'] == customer_id]
        if user.empty: return 0
        return int(user.iloc[0]['loyalty_points'])

    def add_purchase_points(self, customer_id: str, total_amount: float):
        """
        اضافه کردن امتیاز خرید.
        فرض: هر ۱۰۰۰ تومان = ۱ امتیاز
        """
        points = int(total_amount // 1000)
        if points > 0:
            self.db.add_loyalty_points(customer_id, points)

    def generate_discount_code(self, customer_id: str, points_cost: int) -> DiscountCode:
        """
        تبدیل امتیاز به کد تخفیف.
        فرض: هزینه ۱۰۰ امتیاز = ۱۰٪ تخفیف
        """
        if points_cost < 100:
            raise ValueError("حداقل امتیاز برای کد تخفیف ۱۰۰ است")

        self.db.deduct_loyalty_points(customer_id, points_cost)
        
        code = f"LO-{uuid.uuid4().hex[:6].upper()}" # کد شش کاراکتری
        
        discount = DiscountCode(
            code=code,
            discount_percentage=10.0, # تخفیف ۱۰ درصدی ثابت برای این پروژه
            expiry_date=datetime.now() + timedelta(days=30) # اعتبار ۳۰ روزه
        )
        
        self.db.save_discount_code(discount)
        return discount