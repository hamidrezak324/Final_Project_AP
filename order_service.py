import uuid
from datetime import date
from model import Order, Cart
from database import Database
from food_service import FoodService


class OrderService:
    def __init__(self):
        self.db = Database()
        # Used to access food-related logic such as stock control
        self.food_service = FoodService()

    def checkout(
        self,
        cart: Cart,
        customer_id: str,
        delivery_date: date,
        payment_method: str
    ) -> Order:
        """
        Finalize the checkout process:
        - Convert cart into an order
        - Validate and reduce food stock
        - Persist order and order items in the database
        """
        if not cart.items:
            raise ValueError("Cart is empty")

        # 1. Create a new order object
        order_id = str(uuid.uuid4())

        # Convert cart items into order items
        # Note: Food objects inside cart items are in-memory objects.
        # Stock validation and updates are always done using database values.
        new_order = Order(
            order_id=order_id,
            customer_id=customer_id,
            items=cart.items,
            delivery_date=delivery_date,
            payment_method=payment_method
        )

        # 2. Reduce food stock in the database
        for item in cart.items:
            food_id = item.food.food_id
            quantity = item.quantity

            # Fetch the latest stock value from the database
            current_stock_df = self.db.load_foods()
            stock_row = current_stock_df[current_stock_df['food_id'] == food_id]

            if stock_row.empty:
                raise ValueError(f"Food with ID {food_id} not found")

            current_stock = int(stock_row.iloc[0]['stock'])

            if current_stock < quantity:
                raise ValueError(f"Insufficient stock for {item.food.name}")

            # Save updated stock value
            new_stock = current_stock - quantity
            self.db.update_food_stock(food_id, new_stock)

        # 3. Save order and order items in the database
        self.db.save_order(new_order)
        self.db.save_order_items(order_id, cart.items)

        # 4. Clear the shopping cart
        cart.clear()

        return new_order

    def process_payment(self, order_id: str):
        """
        Simulate payment processing.
        In a real-world application, this is where a payment gateway
        integration would take place.
        """
        self.db.update_order_status(order_id, Order.STATUS_PAID)
        return True

    def cancel_order(self, order_id: str):
        """
        Cancel an order and restore food stock quantities.
        Includes additional debug output for troubleshooting.
        """
        # 1. Retrieve order items from the database
        items_df = self.db.get_order_items(order_id)

        if items_df.empty:
            raise ValueError("Order not found or contains no items")

        print(f"DEBUG: Number of items to restore stock for: {len(items_df)}")

        # 2. Restore food stock (increase stock)
        for _, row in items_df.iterrows():
            food_id = str(row['food_id'])
            qty = int(row['quantity'])

            # Read current stock value
            foods_df = self.db.load_foods()
            stock_row = foods_df[foods_df['food_id'] == food_id]

            if not stock_row.empty:
                current_stock = int(stock_row.iloc[0]['stock'])
                new_stock = current_stock + qty

                print(
                    f"DEBUG: Food {food_id} | "
                    f"Stock before: {current_stock} | "
                    f"Added: {qty} | "
                    f"New stock: {new_stock}"
                )

                # Save updated stock value
                self.db.update_food_stock(food_id, new_stock)
            else:
                print(f"DEBUG: Food {food_id} not found in database!")

        # 3. Update order status
        self.db.update_order_status(order_id, Order.STATUS_CANCELLED)
