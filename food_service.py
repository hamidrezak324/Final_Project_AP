import uuid
from datetime import date, datetime
from typing import List, Optional
from model import Food, Cart, OrderItem
from database import Database

class FoodService:
    def __init__(self):
        self.db = Database()

    def get_menu_for_date(self, selected_date: date) -> List[Food]:
        """
        return the list of foods for a specific date.
        the past dates should not be selected (checked in the input).
        """
        df = self.db.load_foods()
        foods_list = []
        
        for _, row in df.iterrows():
            # convert the dictionary or series to a Food object
            available_dates = row['available_dates']
            
            # check if the food is available for the selected date
            if selected_date in available_dates:
                food = Food(
                    food_id=row['food_id'],
                    name=row['name'],
                    category=row['category'],
                    selling_price=row['selling_price'],
                    cost_price=row['cost_price'],
                    ingredients=row['ingredients'],
                    description=row['description'],
                    stock=row['stock'],
                    available_dates=row['available_dates'],
                    image_path=row['image_path']
                )
                foods_list.append(food)
        return foods_list

    def add_to_cart(self, cart: Cart, food_id: str, quantity: int):
        """
        add the food to the cart with the stock control.
        """
        df = self.db.load_foods()
        food_row = df[df['food_id'] == food_id]

        if food_row.empty:
            raise ValueError("Food not found")

        # create a temporary food object to check the stock
        # note: we don't update the database directly, we only check the stock
        # the real stock update is done when the order is finalized (phase 4)
        stock = int(food_row.iloc[0]['stock'])
        
        # calculate the number of items in the cart for this food (if it was already added)
        current_in_cart = 0
        for item in cart.items:
            if item.food.food_id == food_id:
                current_in_cart = item.quantity
                break
        
        if stock < (current_in_cart + quantity):
            raise ValueError(f"Stock is not enough. Current stock: {stock}")
        
        # create a complete food object to add to the cart
        # (since Food is a dataclass, it's easy to create it)
        f_data = food_row.iloc[0]
        food_obj = Food(
            food_id=f_data['food_id'],
            name=f_data['name'],
            category=f_data['category'],
            selling_price=f_data['selling_price'],
            cost_price=f_data['cost_price'],
            ingredients=f_data['ingredients'],
            description=f_data['description'],
            stock=f_data['stock'], # current stock in the database
            available_dates=f_data['available_dates']
        )
        
        try:
            cart.add_item(food_obj, quantity)
        except ValueError as e:
            raise e

    def remove_from_cart(self, cart: Cart, food_id: str):
        cart.remove_item(food_id)

    def get_cart_total(self, cart: Cart) -> float:
        return cart.get_total()