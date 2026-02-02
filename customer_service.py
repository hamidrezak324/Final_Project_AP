import uuid
from datetime import datetime, timedelta
from typing import List
from model import Review, DiscountCode
from database import Database


class CustomerService:
    def __init__(self):
        self.db = Database()

    # -------------------------------------------------------
    # Order History
    # -------------------------------------------------------
    def get_order_history(self, customer_id: str) -> List[dict]:
        """Retrieve customer's order history with full details"""
        orders_df = self.db.get_customer_orders(customer_id)
        foods_df = self.db.load_foods()
        history = []

        for _, order_row in orders_df.iterrows():
            # Get order items
            items_df = self.db.get_order_items(order_row['order_id'])

            # Build item details list
            items_details = []
            for _, item_row in items_df.iterrows():
                food = foods_df[foods_df['food_id'] == item_row['food_id']]
                food_name = food.iloc[0]['name'] if not food.empty else item_row['food_id']

                items_details.append({
                    'food_name': food_name,
                    'quantity': int(item_row['quantity']),
                    'unit_price': float(item_row['unit_price']),
                    'total': int(item_row['quantity']) * float(item_row['unit_price'])
                })

            history.append({
                'order_id': order_row['order_id'],
                'date': order_row['order_date'],
                'status': order_row['status'],
                # total_amount: original amount before discount (for reference)
                'total_amount': float(order_row['total_amount']) + float(order_row['discount_amount']),
                # final_amount: amount actually paid by customer
                'final_amount': float(order_row['total_amount']),
                'items': items_details
            })

        return history

    # -------------------------------------------------------
    # Reviews
    # -------------------------------------------------------
    def submit_review(self, customer_id: str, order_id: str, rating: int, comment: str):
        """Submit a review for a completed order"""
        order_row = self.db.get_order_by_id(order_id)
        if order_row is None:
            raise ValueError("Order not found")

        if order_row['customer_id'] != customer_id:
            raise ValueError("You can only review your own orders")

        # Validate rating range
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        review = Review(
            review_id=str(uuid.uuid4()),
            customer_id=customer_id,
            order_id=order_id,
            rating=rating,
            comment=comment
        )
        self.db.save_review(review)

        points_for_review = 10 # points for each review
        self.db.add_loyalty_points(customer_id, points_for_review)

    # -------------------------------------------------------
    # Loyalty Points & Discounts
    # -------------------------------------------------------
    def get_user_points(self, customer_id: str) -> int:
        """Get current loyalty points of the customer"""
        df = self.db.load_users()
        user = df[df['user_id'] == customer_id]
        if user.empty:
            return 0
        return int(user.iloc[0]['loyalty_points'])

    def add_purchase_points(self, customer_id: str, total_amount: float):
        """
        Add loyalty points after purchase.
        Rule: every 1000 units of currency equals 1 point
        """
        points = int(total_amount // 1000)
        if points > 0:
            self.db.add_loyalty_points(customer_id, points)

    def generate_discount_code(self, customer_id: str, points_cost: int) -> DiscountCode:
        """
        Convert loyalty points into a discount code.
        Assumption: 100 points = 10% discount
        """
        if points_cost < 100:
            raise ValueError("Minimum required points for a discount code is 100")

        self.db.deduct_loyalty_points(customer_id, points_cost)

        # Generate a 6-character discount code
        code = f"LO-{uuid.uuid4().hex[:6].upper()}"

        discount = DiscountCode(
            code=code,
            discount_percentage=10.0,  # Fixed 10% discount for this project
            expiry_date=datetime.now() + timedelta(days=30)  # Valid for 30 days
        )

        self.db.save_discount_code(discount)
        return discount
