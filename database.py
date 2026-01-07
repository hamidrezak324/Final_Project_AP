import pandas as pd
import os
from model import User, Food
from datetime import datetime, date
from typing import List

class Database:
    def __init__(self):
        self.users_file = "users.csv"
        self._init_files()
        self.foods_file = "foods.csv"

    def _init_files(self):
        """create the files if they don't exist"""
        if not os.path.exists(self.users_file):
            # create the initial dataframe with the required columns
            cols = [
                'user_id', 'role', 'first_name', 'last_name', 'email', 'password', 
                'phone', 'national_code', 'address', 'personnel_id', 
                'loyalty_points', 'failed_attempts', 'is_locked'
            ]
            pd.DataFrame(columns=cols).to_csv(self.users_file, index=False)
        if not os.path.exists(self.foods_file):
            cols = [
                'food_id', 'name', 'category', 'selling_price', 'cost_price', 
                'ingredients', 'description', 'stock', 'available_dates', 'image_path'
            ]
            pd.DataFrame(columns=cols).to_csv(self.foods_file, index=False)

    def load_users(self) -> pd.DataFrame:
        return pd.read_csv(self.users_file)

    def save_user(self, user: User):
        df = self.load_users()
        # Check if national code already exists (for customers)
        if hasattr(user, 'national_code') and user.national_code:
            if not df[df['national_code'] == user.national_code].empty:
                raise ValueError("National code already exists")
        # Check if email already exists
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
        
        # add the new user to the dataframe
        new_df = pd.concat([df, pd.DataFrame([user_data])], ignore_index=True)
        new_df.to_csv(self.users_file, index=False)

    def reset_failed_attempts(self, email: str):
        """reset the failed attempts after successful login"""
        self.update_user_login_state(email, 0, False)    

    def update_user_login_state(self, email: str, failed_attempts: int, is_locked: bool):
        """update the login state (locking or the number of failed attempts)"""
        df = self.load_users()
        index = df[df['email'] == email].index
        
        if len(index) > 0:
            df.at[index[0], 'failed_attempts'] = failed_attempts
            df.at[index[0], 'is_locked'] = is_locked
            df.to_csv(self.users_file, index=False)

    def find_user_by_email(self, email: str) -> pd.Series:
        df = self.load_users()
        user = df[df['email'] == email]
        if user.empty:
            return None
        return user.iloc[0]

    def find_admin_by_personnel(self, personnel_id: str) -> pd.Series:
        df = self.load_users()
        admin = df[df['personnel_id'] == personnel_id]
        if admin.empty:
            return None
        return admin.iloc[0]

    def update_user_profile(self, email: str, updated_fields: dict):
        """update the user profile fields"""
        df = self.load_users()
        index = df[df['email'] == email].index
    
        if len(index) > 0:
            for field, value in updated_fields.items():
                if field in df.columns:
                    df.at[index[0], field] = value
            df.to_csv(self.users_file, index=False)
        else:
            raise ValueError("User not found")    

    def find_user_by_national_code(self, national_code: str) -> pd.Series:
        """Find user by national code"""
        df = self.load_users()
        user = df[df['national_code'] == national_code]
        if user.empty:
            return None
        return user.iloc[0]    

    def _parse_dates(self, date_str: str) -> List[date]:
        if pd.isna(date_str) or date_str == "":
            return []
        try:
            dates_str = date_str.split(',')
            return [datetime.strptime(d.strip(), "%Y-%m-%d").date() for d in dates_str]
        except:
            return []

    def _format_dates(self, dates_list: List[date]) ->str:
        """convert the list of dates to a string"""  
        return ",".join([d.strftime("%Y-%m-%d") for d in dates_list])                

    def load_foods(self) -> pd.DataFrame:
        df = pd.read_csv(self.foods_file)
        # parse the list of dates
        df['available_dates'] = df['available_dates'].apply(self._parse_dates)
        return df

    def save_food(self, food: Food):
        df = self.load_foods()
        
        # if the food already exists update it, if not add it
        # for simplicity we assume that we always add it (the admin can manage it)
        
        food_data = {
            'food_id': food.food_id,
            'name': food.name,
            'category': food.category,
            'selling_price': food.selling_price,
            'cost_price': food.cost_price,
            'ingredients': food.ingredients,
            'description': food.description,
            'stock': food.stock,
            'available_dates': self._format_dates(food.available_dates),
            'image_path': food.image_path
        }
        
        new_df = pd.concat([df, pd.DataFrame([food_data])], ignore_index=True)
        new_df.to_csv(self.foods_file, index=False)

    def update_food_stock(self, food_id: str, new_stock: int):
        df = self.load_foods()
        index = df[df['food_id'] == food_id].index
        if len(index) > 0:
            df.at[index[0], 'stock'] = new_stock
            df.to_csv(self.foods_file, index=False)