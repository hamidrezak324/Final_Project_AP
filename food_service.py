from datetime import date
from typing import List, Optional
from model import Food, Cart
from database import Database


class FoodService:
    def __init__(self):
        self.db = Database()

    # -------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------

    def _parse_food_from_row(self, row) -> Food:
        """
        Convert a pandas DataFrame row into a Food object.
        Since the database layer already parses available_dates
        into a list of date objects, we can use it directly here.
        """
        return Food(
            food_id=row['food_id'],
            restaurant_id=row['restaurant_id'],
            name=row['name'],
            category=row['category'],
            selling_price=float(row['selling_price']),
            cost_price=float(row['cost_price']),
            ingredients=row['ingredients'],
            description=row['description'],
            stock=int(row['stock']),
            # available_dates is already parsed as List[date] by the database
            available_dates=row['available_dates'],
            image_path=row['image_path']
        )

    # -------------------------------------------------------
    # Methods for Displaying Food
    # -------------------------------------------------------

    def get_menu_for_date(self, selected_date: date) -> List[Food]:
        """
        Return a list of foods that are available on a specific date.
        """
        df = self.db.load_foods()
        foods_list = []

        for _, row in df.iterrows():
            # Check whether the food is available on the selected date
            # (available_dates is a list of date objects)
            if selected_date in row['available_dates']:
                foods_list.append(self._parse_food_from_row(row))

        return foods_list

    def search_foods(self, query: str, selected_date: Optional[date] = None) -> List[Food]:
        """
        Search foods by name, ingredients, or description.
        Optionally filters results by availability date.
        """
        df = self.db.load_foods()
        foods_list = []
        query_lower = query.lower()

        for _, row in df.iterrows():
            # Date filtering (only if a date is provided)
            if selected_date and selected_date not in row['available_dates']:
                continue

            # Text-based search fields
            name = str(row['name']).lower()
            ingredients = str(row['ingredients']).lower()
            description = str(row['description']).lower()

            if (
                query_lower in name or
                query_lower in ingredients or
                query_lower in description
            ):
                foods_list.append(self._parse_food_from_row(row))

        return foods_list

    def get_all_foods(self) -> List[Food]:
        """
        Retrieve all foods (e.g. for admin panel usage).
        """
        df = self.db.load_foods()
        foods_list = []

        for _, row in df.iterrows():
            foods_list.append(self._parse_food_from_row(row))

        return foods_list

    def get_food_by_id(self, food_id: str) -> Optional[Food]:
        """
        Retrieve a single food by its ID.
        Used for food details or editing.
        """
        row = self.db.find_food_by_id(food_id)
        if row is None:
            return None
        return self._parse_food_from_row(row)

    # -------------------------------------------------------
    # Methods for Cart Management
    # -------------------------------------------------------

    def add_to_cart(self, cart: Cart, food_id: str, quantity: int):
        """
        Add a food item to the cart with smart stock validation.
        Stock is checked against the database, and if the item
        already exists in the cart, quantities are accumulated.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        # Fetch the most up-to-date food data from the database
        food_obj = self.get_food_by_id(food_id)
        if not food_obj:
            raise ValueError("Food not found")

        # Calculate how many units of this food are already in the cart
        current_in_cart = 0
        for item in cart.items:
            if item.food.food_id == food_id:
                current_in_cart = item.quantity
                break

        # Validate stock availability
        # (database stock >= quantity already in cart + requested quantity)
        if food_obj.stock < (current_in_cart + quantity):
            raise ValueError(
                f"Insufficient stock. Current stock: {food_obj.stock}"
            )

        # Add item to cart (Cart class handles update vs new item)
        try:
            cart.add_item(food_obj, quantity)
        except ValueError as e:
            raise e

    def remove_from_cart(self, cart: Cart, food_id: str):
        """
        Remove an item completely from the cart.
        """
        cart.remove_item(food_id)

    def update_cart_item_quantity(self, cart: Cart, food_id: str, new_quantity: int):
        """
        Update the quantity of an existing cart item.
        If the new quantity is zero or negative, the item is removed.
        """
        if new_quantity <= 0:
            self.remove_from_cart(cart, food_id)
            return

        food_obj = self.get_food_by_id(food_id)
        if not food_obj:
            raise ValueError("Food not found")

        # Check stock availability against the database
        if food_obj.stock < new_quantity:
            raise ValueError(
                f"Insufficient stock. Current stock: {food_obj.stock}"
            )

        # Find the item in the cart and update its quantity
        for item in cart.items:
            if item.food.food_id == food_id:
                item.quantity = new_quantity
                return  # Update completed

        # If the item does not exist in the cart, add it as a new item
        self.add_to_cart(cart, food_id, new_quantity)

    def get_cart_total(self, cart: Cart) -> float:
        """
        Calculate and return the total price of the cart.
        """
        return cart.get_total()
