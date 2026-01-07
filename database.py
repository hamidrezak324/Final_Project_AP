import pandas as pd
import os
from model import User, Food
from datetime import datetime, date
from typing import List, Optional
import json


class Database:
    def __init__(self):
        # CSV files used as simple persistent storage
        self.users_file = "users.csv"
        self.foods_file = "foods.csv"

        # Phase 4 tables (orders and order items)
        self.orders_file = "orders.csv"
        self.order_items_file = "order_items.csv"

        # Initialize files if they do not exist
        self._init_files()

    def _init_files(self):
        """
        Create required CSV files with predefined columns
        if they do not already exist.
        """
        if not os.path.exists(self.users_file):
            cols = [
                'user_id', 'role', 'first_name', 'last_name', 'email', 'password',
                'phone', 'national_code', 'address', 'personnel_id',
                'loyalty_points', 'failed_attempts', 'is_locked'
            ]
            pd.DataFrame(columns=cols).to_csv(self.users_file, index=False)

        if not os.path.exists(self.foods_file):
            cols = [
                'food_id', 'name', 'category', 'selling_price', 'cost_price',
                'ingredients', 'description', 'stock',
                'available_dates', 'image_path'
            ]
            pd.DataFrame(columns=cols).to_csv(self.foods_file, index=False)

        # -------- Phase 4: Orders --------
        if not os.path.exists(self.orders_file):
            cols = [
                'order_id', 'customer_id', 'order_date', 'delivery_date',
                'status', 'total_amount', 'discount_amount',
                'payment_method', 'discount_code'
            ]
            pd.DataFrame(columns=cols).to_csv(self.orders_file, index=False)

        if not os.path.exists(self.order_items_file):
            cols = ['order_id', 'food_id', 'quantity', 'unit_price']
            pd.DataFrame(columns=cols).to_csv(self.order_items_file, index=False)

    # -------------------------------------------------------
    # User-related methods
    # -------------------------------------------------------

    def load_users(self) -> pd.DataFrame:
        """Load all users from the CSV file."""
        return pd.read_csv(self.users_file)

    def save_user(self, user: User):
        """
        Save a new user into the users table.
        Performs validation for unique email and national code.
        """
        df = self.load_users()

        # Check if national code already exists (mainly for customers)
        if hasattr(user, 'national_code') and user.national_code:
            if not df[df['national_code'] == user.national_code].empty:
                raise ValueError("National code already exists")

        # Check for duplicate email
        if not df[df['email'] == user.email].empty:
            raise ValueError("Email already exists")

        user_data = {
            'user_id': user._user_id,
            'role': user.get_role(),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'password': user._password,
            'phone': getattr(user, 'phone', None),
            'national_code': getattr(user, 'national_code', ""),
            'address': getattr(user, 'address', None),
            'personnel_id': getattr(user, 'personnel_id', None),
            'loyalty_points': getattr(user, 'loyalty_points', 0),
            'failed_attempts': 0,
            'is_locked': False
        }

        new_df = pd.concat([df, pd.DataFrame([user_data])], ignore_index=True)
        new_df.to_csv(self.users_file, index=False)

    def reset_failed_attempts(self, email: str):
        """Reset failed login attempts and unlock the user."""
        self.update_user_login_state(email, 0, False)

    def update_user_login_state(self, email: str, failed_attempts: int, is_locked: bool):
        """
        Update login-related fields such as failed attempts
        and account lock status.
        """
        df = self.load_users()
        index = df[df['email'] == email].index

        if len(index) > 0:
            df.at[index[0], 'failed_attempts'] = failed_attempts
            df.at[index[0], 'is_locked'] = is_locked
            df.to_csv(self.users_file, index=False)

    def find_user_by_email(self, email: str) -> Optional[pd.Series]:
        """Find and return a user by email."""
        df = self.load_users()
        user = df[df['email'] == email]
        return None if user.empty else user.iloc[0]

    def find_admin_by_personnel(self, personnel_id: str) -> Optional[pd.Series]:
        """Find an admin user by personnel ID."""
        df = self.load_users()
        admin = df[df['personnel_id'] == personnel_id]
        return None if admin.empty else admin.iloc[0]

    def update_user_profile(self, email: str, updated_fields: dict):
        """
        Update editable user profile fields.
        Only columns that exist in the table are updated.
        """
        df = self.load_users()
        index = df[df['email'] == email].index

        if len(index) > 0:
            for field, value in updated_fields.items():
                if field in df.columns:
                    df.at[index[0], field] = value
            df.to_csv(self.users_file, index=False)
        else:
            raise ValueError("User not found")

    def find_user_by_national_code(self, national_code: str) -> Optional[pd.Series]:
        """Find a user using national code."""
        df = self.load_users()
        user = df[df['national_code'] == national_code]
        return None if user.empty else user.iloc[0]

    # -------------------------------------------------------
    # Food-related methods (Dates stored as JSON)
    # -------------------------------------------------------

    def _parse_dates(self, date_str: str) -> List[date]:
        """
        Parse a JSON string of dates into a list of date objects.
        Supports legacy comma-separated date formats as fallback.
        """
        if pd.isna(date_str) or date_str == "":
            return []

        try:
            # Preferred format: JSON array
            dates = json.loads(date_str)
            return [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]
        except (json.JSONDecodeError, TypeError, ValueError):
            try:
                # Fallback for old comma-separated format
                return [
                    datetime.strptime(d.strip(), "%Y-%m-%d").date()
                    for d in date_str.split(',')
                ]
            except Exception:
                return []

    def _format_dates(self, dates_list: List[date]) -> str:
        """Convert a list of date objects to a JSON string."""
        return json.dumps([d.strftime("%Y-%m-%d") for d in dates_list])

    def load_foods(self) -> pd.DataFrame:
        """
        Load foods from CSV.
        All values are initially read as strings to avoid type issues,
        then converted explicitly.
        """
        df = pd.read_csv(self.foods_file, dtype=str)

        # Parse available dates column
        df['available_dates'] = df['available_dates'].apply(self._parse_dates)

        # Convert numeric fields
        df['selling_price'] = pd.to_numeric(df['selling_price'])
        df['cost_price'] = pd.to_numeric(df['cost_price'])
        df['stock'] = pd.to_numeric(df['stock'])

        return df

    def find_food_by_id(self, food_id: str) -> Optional[pd.Series]:
        """Find a food item by its ID."""
        df = self.load_foods()
        food = df[df['food_id'] == food_id]
        return None if food.empty else food.iloc[0]

    def update_food_stock(self, food_id: str, new_stock: int):
        """Update the stock quantity of a food item."""
        df = self.load_foods()
        index = df[df['food_id'] == food_id].index

        if len(index) > 0:
            df.at[index[0], 'stock'] = new_stock
            df.to_csv(self.foods_file, index=False)
        else:
            raise ValueError("Food not found")

    def save_food(self, food: Food):
        """Save a new food item into the foods table."""
        df = self.load_foods()

        food_data = {
            'food_id': str(food.food_id),
            'name': str(food.name),
            'category': str(food.category),
            'selling_price': float(food.selling_price),
            'cost_price': float(food.cost_price),
            'ingredients': str(food.ingredients),
            'description': str(food.description),
            'stock': int(food.stock),
            'available_dates': self._format_dates(food.available_dates),
            'image_path': str(food.image_path) if food.image_path else None
        }

        cols = [
            'food_id', 'name', 'category', 'selling_price', 'cost_price',
            'ingredients', 'description', 'stock',
            'available_dates', 'image_path'
        ]

        new_df = pd.concat([df, pd.DataFrame([food_data], columns=cols)], ignore_index=True)
        new_df.to_csv(self.foods_file, index=False)

    # -------------------------------------------------------
    # Order-related methods (Phase 4)
    # -------------------------------------------------------

    def save_order(self, order):
        """
        Save an order record.
        Handles empty or non-existing CSV files safely.
        """
        if os.path.exists(self.orders_file) and os.path.getsize(self.orders_file) > 0:
            df = pd.read_csv(self.orders_file)
        else:
            df = pd.DataFrame(columns=[
                'order_id', 'customer_id', 'order_date', 'delivery_date',
                'status', 'total_amount', 'discount_amount',
                'payment_method', 'discount_code'
            ])

        order_data = {
            'order_id': order.order_id,
            'customer_id': order.customer_id,
            'order_date': order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            'delivery_date': order.delivery_date.strftime("%Y-%m-%d"),
            'status': order.status,
            'total_amount': order._total_amount,
            'discount_amount': order.discount_amount,
            'payment_method': order.payment_method,
            'discount_code': order.discount_code
        }

        new_df = pd.concat([df, pd.DataFrame([order_data])], ignore_index=True)
        new_df.to_csv(self.orders_file, index=False)

    def save_order_items(self, order_id: str, items):
        """Save all items related to a specific order."""
        if os.path.exists(self.order_items_file) and os.path.getsize(self.order_items_file) > 0:
            df = pd.read_csv(self.order_items_file)
        else:
            df = pd.DataFrame(columns=['order_id', 'food_id', 'quantity', 'unit_price'])

        items_data = []
        for item in items:
            items_data.append({
                'order_id': order_id,
                'food_id': item.food.food_id,
                'quantity': item.quantity,
                'unit_price': item.unit_price
            })

        if items_data:
            new_df = pd.concat([df, pd.DataFrame(items_data)], ignore_index=True)
            new_df.to_csv(self.order_items_file, index=False)

    def update_order_status(self, order_id: str, new_status: str):
        """Update the status of an existing order."""
        df = pd.read_csv(self.orders_file)
        index = df[df['order_id'] == order_id].index

        if len(index) > 0:
            df.at[index[0], 'status'] = new_status
            df.to_csv(self.orders_file, index=False)

    def get_order_items(self, order_id: str) -> pd.DataFrame:
        """Retrieve all items belonging to a specific order."""
        df = pd.read_csv(self.order_items_file)
        return df[df['order_id'] == order_id]
