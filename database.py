import pandas as pd
import os
import json
from model import User, Food
from datetime import datetime, date
from typing import List, Optional


class Database:
    def __init__(self):
        self.users_file = "users.csv"
        self.foods_file = "foods.csv"
        self.orders_file = "orders.csv"
        self.order_items_file = "order_items.csv"
        self.reviews_file = "reviews.csv"
        self.discount_codes_file = "discount_codes.csv"
        self._init_files()

    def _init_files(self):
        # Users table
        if not os.path.exists(self.users_file):
            cols = [
                'user_id', 'role', 'first_name', 'last_name', 'email', 'password',
                'phone', 'national_code', 'address', 'personnel_id',
                'loyalty_points', 'failed_attempts', 'is_locked'
            ]
            pd.DataFrame(columns=cols).to_csv(self.users_file, index=False)

        # Foods table
        if not os.path.exists(self.foods_file):
            cols = [
            'food_id', 'restaurant_id', 'name', 'category', 'selling_price', 'cost_price',
            'ingredients', 'description', 'stock', 'available_dates'
            ]
            pd.DataFrame(columns=cols).to_csv(self.foods_file, index=False)

        # Orders table
        if not os.path.exists(self.orders_file):
            cols = [
                'order_id', 'customer_id', 'order_date', 'delivery_date',
                'status', 'total_amount', 'discount_amount',
                'payment_method', 'discount_code'
            ]
            pd.DataFrame(columns=cols).to_csv(self.orders_file, index=False)

        # Order items table
        if not os.path.exists(self.order_items_file):
            cols = ['order_id', 'food_id', 'quantity', 'unit_price']
            pd.DataFrame(columns=cols).to_csv(self.order_items_file, index=False)

        # Reviews table (Phase 5)
        if not os.path.exists(self.reviews_file):
            cols = [
                'review_id', 'customer_id', 'order_id',
                'rating', 'comment', 'review_date'
            ]
            pd.DataFrame(columns=cols).to_csv(self.reviews_file, index=False)

        # Discount codes table (Phase 5)
        if not os.path.exists(self.discount_codes_file):
            cols = [
                'code', 'discount_percentage', 'expiry_date',
                'is_used', 'customer_id'
            ]
            pd.DataFrame(columns=cols).to_csv(self.discount_codes_file, index=False)

    # -------------------------------------------------------
    # Users
    # -------------------------------------------------------
    def load_users(self) -> pd.DataFrame:
        return pd.read_csv(self.users_file)

    def save_user(self, user: User):
        df = self.load_users()

        if hasattr(user, 'national_code') and user.national_code:
            if not df[df['national_code'] == user.national_code].empty:
                raise ValueError("National code already exists")

        if not df[df['email'] == user.email].empty:
            raise ValueError("Email already exists")

        user_data = {
            'user_id': user.user_id,
            'role': user.get_role(),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'password': user.password,
            'phone': getattr(user, 'phone', None),
            'national_code': getattr(user, 'national_code', ""),
            'address': getattr(user, 'address', None),
            'personnel_id': getattr(user, 'personnel_id', None),
            'loyalty_points': getattr(user, 'loyalty_points', 0),
            'failed_attempts': 0,
            'is_locked': False
        }

        pd.concat(
            [df, pd.DataFrame([user_data])],
            ignore_index=True
        ).to_csv(self.users_file, index=False)

    def update_user_login_state(self, email: str, failed_attempts: int, is_locked: bool):
        df = self.load_users()
        index = df[df['email'] == email].index
        if len(index) > 0:
            df.at[index[0], 'failed_attempts'] = failed_attempts
            df.at[index[0], 'is_locked'] = is_locked
            df.to_csv(self.users_file, index=False)

    def find_user_by_email(self, email: str) -> Optional[pd.Series]:
        df = self.load_users()
        user = df[df['email'] == email]
        return None if user.empty else user.iloc[0]

    def find_admin_by_personnel(self, personnel_id: str) -> Optional[pd.Series]:
        df = self.load_users()
        df['personnel_id'] = df['personnel_id'].astype(str).str.strip()
        # remove 0 from float
        df['personnel_id'] = df['personnel_id'].str.replace(r'\.0$', '', regex=True)
        admin = df[(df['personnel_id'] == str(personnel_id).strip()) & (df['role'] == 'Admin')]
        return None if admin.empty else admin.iloc[0]

    def update_user_profile(self, email: str, updated_fields: dict):
        df = self.load_users()
        index = df[df['email'] == email].index
        if len(index) > 0:
            for field, value in updated_fields.items():
                if field in df.columns:
                    df.at[index[0], field] = value
            df.to_csv(self.users_file, index=False)
        else:
            raise ValueError("User not found")

    # -------------------------------------------------------
    # Foods (JSON Date Handling)
    # -------------------------------------------------------
    def _parse_dates(self, date_str: str) -> List[date]:
        if pd.isna(date_str) or date_str == "":
            return []
        try:
            dates = json.loads(date_str)
            return [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]
        except Exception:
            return []

    def _format_dates(self, dates_list: List[date]) -> str:
        return json.dumps([d.strftime("%Y-%m-%d") for d in dates_list])

    def load_foods(self) -> pd.DataFrame:
        df = pd.read_csv(self.foods_file, dtype=str)
        df['available_dates'] = df['available_dates'].apply(self._parse_dates)
        df['selling_price'] = pd.to_numeric(df['selling_price'])
        df['cost_price'] = pd.to_numeric(df['cost_price'])
        df['stock'] = pd.to_numeric(df['stock'])
        return df

    def find_food_by_id(self, food_id: str) -> Optional[pd.Series]:
        df = self.load_foods()
        food = df[df['food_id'] == food_id]
        return None if food.empty else food.iloc[0]

    def update_food_stock(self, food_id: str, new_stock: int):
        df = self.load_foods()
        index = df[df['food_id'] == food_id].index
        if len(index) > 0:
            df.at[index[0], 'stock'] = new_stock
            df.to_csv(self.foods_file, index=False)

    def save_food(self, food: Food):
        df = self.load_foods()
        food_data = {
            'food_id': str(food.food_id),
            'restaurant_id': str(food.restaurant_id),
            'name': str(food.name),
            'category': str(food.category),
            'selling_price': float(food.selling_price),
            'cost_price': float(food.cost_price),
            'ingredients': str(food.ingredients),
            'description': str(food.description),
            'stock': int(food.stock),
            'available_dates': self._format_dates(food.available_dates)
        }

        pd.concat(
            [df, pd.DataFrame([food_data])],
            ignore_index=True
        ).to_csv(self.foods_file, index=False)

    # -------------------------------------------------------
    # Orders
    # -------------------------------------------------------
    def save_order(self, order):
        if os.path.exists(self.orders_file) and os.path.getsize(self.orders_file) > 0:
            df = pd.read_csv(self.orders_file)
        else:
            df = pd.DataFrame(columns=[
                    'order_id', 'restaurant_id', 'customer_id', 'order_date', 'delivery_date',
                    'status', 'total_amount', 'discount_amount',
                    'payment_method', 'discount_code'
            ])

        order_data = {
            'order_id': order.order_id,
            'restaurant_id': order.restaurant_id, 
            'customer_id': order.customer_id,
            'order_date': order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            'delivery_date': order.delivery_date.strftime("%Y-%m-%d"),
            'status': order.status,
            'total_amount': order._total_amount,
            'discount_amount': order.discount_amount,
            'payment_method': order.payment_method,
            'discount_code': order.discount_code
        }

        pd.concat(
            [df, pd.DataFrame([order_data])],
            ignore_index=True
        ).to_csv(self.orders_file, index=False)

    def save_order_items(self, order_id: str, items):
        if os.path.exists(self.order_items_file) and os.path.getsize(self.order_items_file) > 0:
            df = pd.read_csv(self.order_items_file)
        else:
            df = pd.DataFrame(columns=['order_id', 'food_id', 'quantity', 'unit_price'])

        items_data = [
            {
                'order_id': order_id,
                'food_id': i.food.food_id,
                'quantity': i.quantity,
                'unit_price': i.unit_price
            } for i in items
        ]

        if items_data:
            pd.concat(
                [df, pd.DataFrame(items_data)],
                ignore_index=True
            ).to_csv(self.order_items_file, index=False)

    def update_order_status(self, order_id: str, new_status: str):
        df = pd.read_csv(self.orders_file)
        index = df[df['order_id'] == order_id].index
        if len(index) > 0:
            df.at[index[0], 'status'] = new_status
            df.to_csv(self.orders_file, index=False)

    def get_order_items(self, order_id: str) -> pd.DataFrame:
        df = pd.read_csv(self.order_items_file)
        return df[df['order_id'] == order_id]

    def get_customer_orders(self, customer_id: str) -> pd.DataFrame:
        df = pd.read_csv(self.orders_file)
        return df[df['customer_id'] == customer_id].sort_values(
            "order_date", ascending=False
        )

    def get_order_by_id(self, order_id: str) -> Optional[pd.Series]:
        """Retrieve a specific order by its ID"""
        df = pd.read_csv(self.orders_file)
        order = df[df['order_id'] == order_id]
        return None if order.empty else order.iloc[0]

    # -------------------------------------------------------
    # Reviews & Loyalty
    # -------------------------------------------------------
    def save_review(self, review):
        """Save a customer's review"""
        df = pd.read_csv(self.reviews_file)
        review_data = {
            'review_id': review.review_id,
            'customer_id': review.customer_id,
            'order_id': review.order_id,
            'rating': review.rating,
            'comment': review.comment,
            'review_date': review.review_date.strftime("%Y-%m-%d %H:%M:%S")
        }

        pd.concat(
            [df, pd.DataFrame([review_data])],
            ignore_index=True
        ).to_csv(self.reviews_file, index=False)

    def add_loyalty_points(self, customer_id: str, points: int):
        """Add loyalty points to a customer"""
        df = self.load_users()
        index = df[df['user_id'] == customer_id].index
        if len(index) > 0:
            current_points = int(df.at[index[0], 'loyalty_points'])
            df.at[index[0], 'loyalty_points'] = current_points + points
            df.to_csv(self.users_file, index=False)

    def deduct_loyalty_points(self, customer_id: str, points: int):
        """Deduct loyalty points (used for discount codes)"""
        df = self.load_users()
        index = df[df['user_id'] == customer_id].index
        if len(index) > 0:
            current = int(df.at[index[0], 'loyalty_points'])
            if current < points:
                raise ValueError("Insufficient loyalty points")
            df.at[index[0], 'loyalty_points'] = current - points
            df.to_csv(self.users_file, index=False)

    # -------------------------------------------------------
    # Discount Codes
    # -------------------------------------------------------
    def save_discount_code(self, discount_code):
        """Save a new discount code"""
        df = pd.read_csv(self.discount_codes_file)
        code_data = {
            'code': discount_code.code,
            'discount_percentage': discount_code.discount_percentage,
            'expiry_date': discount_code.expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
            'is_used': discount_code.is_used,
            'customer_id': discount_code.customer_id or ""
        }

        pd.concat(
            [df, pd.DataFrame([code_data])],
            ignore_index=True
        ).to_csv(self.discount_codes_file, index=False)

    def find_discount_code(self, code: str) -> Optional[pd.Series]:
        """Find a discount code"""
        df = pd.read_csv(self.discount_codes_file)
        result = df[df['code'] == code]
        return None if result.empty else result.iloc[0]

    def mark_discount_code_used(self, code: str):
        """Mark a discount code as used"""
        df = pd.read_csv(self.discount_codes_file)
        index = df[df['code'] == code].index
        if len(index) > 0:
            df.at[index[0], 'is_used'] = True
            df.to_csv(self.discount_codes_file, index=False)

    def get_reviews_by_order(self, order_id: str) -> pd.DataFrame:
        """Retrieve all reviews related to a specific order"""
        df = pd.read_csv(self.reviews_file)
        return df[df['order_id'] == order_id]
