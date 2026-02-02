import uuid
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List
from model import Food, DiscountCode, Order
from database import Database
from food_service import FoodService

class AdminService:
    def __init__(self):
        self.db = Database()
        # Use FoodService for displaying and searching foods
        self.food_service = FoodService()

    # -------------------------------------------------------
    # Order Management
    # -------------------------------------------------------
    def get_all_orders(self) -> List[dict]:
        """Retrieve the list of all orders in the system"""
        orders_df = pd.read_csv(self.db.orders_file)
        orders_list = []
        
        for _, row in orders_df.iterrows():
            # Find the related customer (optional, for displaying name)
            user_df = self.db.load_users()
            cust = user_df[user_df['user_id'] == row['customer_id']]
            cust_name = (
                f"{cust.iloc[0]['first_name']} {cust.iloc[0]['last_name']}"
                if not cust.empty else row['customer_id']
            )

            orders_list.append({
                'order_id': row['order_id'],
                'customer_name': cust_name,
                'date': row['order_date'],
                'status': row['status'],
                'total_amount': float(row['total_amount']),
                'payment_method': row['payment_method']
            })
        return orders_list

    def update_order_status(self, order_id: str, new_status: str):
        """Update order status by admin"""
        # Check if the status is allowed
        allowed_statuses = [
            Order.STATUS_PENDING,
            Order.STATUS_PAID,
            Order.STATUS_SENT,
            Order.STATUS_CANCELLED
        ]
        if new_status not in allowed_statuses:
            raise ValueError("Invalid order status")
            
        self.db.update_order_status(order_id, new_status)

    # -------------------------------------------------------
    # Food Menu Management
    # -------------------------------------------------------
    def add_new_food(
        self,
        name: str,
        category: str,
        selling_price: float,
        cost_price: float,
        ingredients: str,
        description: str,
        stock: int,
        available_dates_list: List[date],
        restaurant_id: str = str 
    ):
        """Admin adds a new food item to the menu"""
        new_food = Food(
            food_id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            name=name,
            category=category,
            selling_price=selling_price,
            cost_price=cost_price,
            ingredients=ingredients,
            description=description,
            stock=stock,
            available_dates=available_dates_list
        )
        self.db.save_food(new_food)
        return new_food

    def update_food_info(self, food_id: str, **kwargs):
        """
        Update food information (price, stock, description, etc.).
        This is a simple implementation (since pandas does not easily update rows in place).
        A more professional approach would be:
        load → update in memory → save the entire DataFrame.
        """
        df = self.db.load_foods()
        index = df[df['food_id'] == food_id].index
        
        if len(index) == 0:
            raise ValueError("Food not found")
            
        # Update provided fields
        for key, value in kwargs.items():
            if key in df.columns:
                # available_dates must be formatted properly
                if key == 'available_dates':
                    df.at[index[0], key] = self.db._format_dates(value)
                else:
                    df.at[index[0], key] = value
        
        # Save the entire DataFrame again
        df.to_csv(self.db.foods_file, index=False)

    def delete_food(self, food_id: str):
        """Remove a food item from the menu"""
        df = self.db.load_foods()
        df = df[df['food_id'] != food_id]
        df.to_csv(self.db.foods_file, index=False)

    # -------------------------------------------------------
    # Financial & Sales Reports
    # -------------------------------------------------------
    def get_sales_report(self, start_date: date, end_date: date) -> dict:
        """
        Generate sales and profit report for a given time range.
        Sales calculation: sum of sold prices
        Profit calculation: sum of (selling price - cost price) * quantity
        """
        orders_df = pd.read_csv(self.db.orders_file)
        items_df = pd.read_csv(self.db.order_items_file)
        foods_df = self.db.load_foods()

        # Filter orders based on order_date
        # Convert order_date column to datetime
        orders_df['order_date_parsed'] = pd.to_datetime(orders_df['order_date'])
        
        mask = (
            (orders_df['order_date_parsed'].dt.date >= start_date) &
            (orders_df['order_date_parsed'].dt.date <= end_date)
        )
        
        filtered_orders = orders_df[mask]
        
        if filtered_orders.empty:
            return {"total_sales": 0, "total_profit": 0, "order_count": 0}

        relevant_order_ids = filtered_orders['order_id'].tolist()
        
        # Find items related to these orders
        filtered_items = items_df[items_df['order_id'].isin(relevant_order_ids)]
        
        total_sales = 0.0
        total_profit = 0.0
        
        for _, item_row in filtered_items.iterrows():
            fid = str(item_row['food_id'])
            qty = item_row['quantity']
            unit_price = float(item_row['unit_price'])  # Selling price at order time
            
            total_sales += (unit_price * qty)
            
            # Profit calculation:
            # Should we use cost price at order time or current cost price?
            # Typically, profit reports use current or average cost prices.
            # Here, we use the current cost price from the database.
            food_row = foods_df[foods_df['food_id'].astype(str) == fid] 
            if not food_row.empty:
                cost_price = float(food_row.iloc[0]['cost_price'])
                total_profit += (unit_price - cost_price) * qty

        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "order_count": len(filtered_orders),
            "total_sales": total_sales,
            "total_profit": total_profit
        }

    # -------------------------------------------------------
    # Discount Code Management (Admin-issued)
    # -------------------------------------------------------
    def create_discount_for_customer(self, customer_id: str, discount_percentage: float):
        """Admin creates a special discount code for a specific customer"""
        if discount_percentage <= 0 or discount_percentage > 100:  
            raise ValueError("Discount percentage must be between 0 and 100")
        code = f"ADMIN-{uuid.uuid4().hex[:6].upper()}"
        
        discount = DiscountCode(
            code=code,
            discount_percentage=discount_percentage,
            expiry_date=datetime.now() + timedelta(days=30),
            customer_id=customer_id  # This code is assigned to a specific user
        )
        
        self.db.save_discount_code(discount)
        return discount
