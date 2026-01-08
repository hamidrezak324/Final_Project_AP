import uuid
from datetime import date, datetime
from typing import Optional
import pandas as pd
from model import Order, Cart, DiscountCode
from database import Database
from food_service import FoodService
from customer_service import CustomerService


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
        payment_method: str,
        discount_code_str: Optional[str] = None
    ) -> Order:
        """
        Finalize the checkout process:
        - Convert cart into an order
        - Apply discount code if provided
        - Validate and reduce food stock
        - Persist order and order items
        """
        if not cart.items:
            raise ValueError("Cart is empty")

        # 1. Create a new order
        order_id = str(uuid.uuid4())

        new_order = Order(
            order_id=order_id,
            customer_id=customer_id,
            items=cart.items,
            delivery_date=delivery_date,
            payment_method=payment_method
        )

        # 2. Apply discount code if provided
        if discount_code_str:
            discount_data = self.db.find_discount_code(discount_code_str)

            if discount_data is None:
                raise ValueError("Discount code not found")

            discount = DiscountCode(
                code=discount_data["code"],
                discount_percentage=float(discount_data["discount_percentage"]),
                expiry_date=datetime.strptime(
                    discount_data["expiry_date"], "%Y-%m-%d %H:%M:%S"
                ),
                is_used=bool(discount_data["is_used"]),
                customer_id=discount_data["customer_id"]
                if discount_data["customer_id"] else None
            )

            if not discount.is_valid():
                raise ValueError("Invalid or expired discount code")

            new_order.apply_discount(discount)
            self.db.mark_discount_code_used(discount_code_str)

        # 3. Reduce food stock
        for item in cart.items:
            food_id = item.food.food_id
            quantity = item.quantity

            foods_df = self.db.load_foods()
            stock_row = foods_df[foods_df["food_id"] == food_id]

            if stock_row.empty:
                raise ValueError(f"Food with ID {food_id} not found")

            current_stock = int(stock_row.iloc[0]["stock"])

            if current_stock < quantity:
                raise ValueError(f"Insufficient stock for {item.food.name}")

            self.db.update_food_stock(food_id, current_stock - quantity)

        # 4. Save order and order items
        self.db.save_order(new_order)
        self.db.save_order_items(order_id, cart.items)

        # 5. Clear cart
        cart.clear()

        return new_order

    def process_payment(self, order_id: str) -> bool:
        """
        Simulate payment processing.
        In a real application, this would integrate with a payment gateway.
        """
        #1. change the situation of the order
        self.db.update_order_status(order_id, Order.STATUS_PAID)
        #2. read user id to find total amount
        orders_df = pd.read_csv(self.db.orders_file)
        order_row = orders_df[orders_df['order_id'] == order_id]
        if order_row.empty:
            raise ValueError(f"Order with ID {order_id} not found")

        order_data = order_row.iloc[0]
        customer_id = order_data['customer_id']   
        total_before_discount = float(order_data['total_amount']) + float(order_data['discount_amount'])
        customer_service = CustomerService()  
        customer_service.add_purchase_points(customer_id, total_before_discount)
        print(f"Payment successful. Loyalty points added to {customer_id}.")
        return True      


    def cancel_order(self, order_id: str):
        """
        Cancel an order and restore food stock quantities.
        """
        # 1. Retrieve order items
        items_df = self.db.get_order_items(order_id)

        if items_df.empty:
            raise ValueError("Order not found or contains no items")

        # 2. Restore food stock
        for _, row in items_df.iterrows():
            food_id = str(row["food_id"])
            quantity = int(row["quantity"])

            foods_df = self.db.load_foods()
            stock_row = foods_df[foods_df["food_id"] == food_id]

            if stock_row.empty:
                continue

            current_stock = int(stock_row.iloc[0]["stock"])
            new_stock = current_stock + quantity

            self.db.update_food_stock(food_id, new_stock)

        # 3. Update order status
        self.db.update_order_status(order_id, Order.STATUS_CANCELLED)
