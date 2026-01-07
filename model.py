from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, date

# -------------------------------------------------------
# 1. User class (Abstraction & Inheritance)
# -------------------------------------------------------

class User(ABC):
    """
    it is the base class for all users in the system.
    """
    def __init__(self, user_id: str, first_name: str, last_name: str, email: str, password: str):
        self._user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self._password = password  # it should get hashed

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def user_id(self) -> str:
        return self._user_id
    
    @property
    def password(self) -> str:
        return self._password    

    @abstractmethod
    def get_role(self) -> str:
        """returns the role of the user"""
        pass

    def verify_password(self, input_password: str) -> bool:
        return self._password == input_password
    
    def update_email(self, new_email: str):
        """Update user email"""
        self.email = new_email
    
    def update_password(self, new_password: str):
        """Update user password (should be hashed)"""
        self._password = new_password
    
    def update_name(self, first_name: str, last_name: str):
        """Update user name"""
        self.first_name = first_name
        self.last_name = last_name    


class Customer(User):
    """
    it is the customer class that inherits from User.
    """
    def __init__(self, user_id: str, first_name: str, last_name: str, email: str, password: str, 
                 phone: str, national_code: str,address: str = "", loyalty_points: int = 0):
        super().__init__(user_id, first_name, last_name, email, password)
        self.phone = phone
        self.national_code = national_code
        self.address = address
        self.loyalty_points = loyalty_points
        self._cart: Optional['Cart'] = Cart()

    def get_role(self) -> str:
        return "Customer"

    def add_to_loyalty(self, points: int):
        self.loyalty_points += points


class Admin(User):
    """
    it is the admin class that inherits from User.
    """
    def __init__(self, user_id: str, first_name: str, last_name: str, email: str, password: str, personnel_id: str):
        super().__init__(user_id, first_name, last_name, email, password)
        self.personnel_id = personnel_id

    def get_role(self) -> str:
        return "Admin"


# -------------------------------------------------------
# 2. Food and Order classes (Composition & Encapsulation)
# -------------------------------------------------------

@dataclass # it is stored only data which is an ability released for python 3.7 version
class Food:
    """
    it is the food class.
    """
    food_id: str
    name: str
    category: str
    selling_price: float   # selling price to the customer
    cost_price: float       # cost price to calculate profit    
    ingredients: str
    description: str
    stock: int              # stock of the food
    available_dates: List[date] = field(default_factory=list) # list of dates when the food is available
    image_path: Optional[str] = None

    def is_available(self, requested_quantity: int = 1) -> bool:
        return self.stock >= requested_quantity

    def decrease_stock(self, quantity: int):
        """Decrease stock after order"""
        if self.stock >= quantity:
            self.stock -= quantity
        else:
            raise ValueError("Not enough stock")
    
    def increase_stock(self, quantity: int):
        """Increase stock (for order cancellation or restock)"""
        self.stock += quantity    


class OrderItem:
    """
    it is the order item class that contains the food and the quantity.
    the price is locked at the time of order placement to prevent future price changes on previous orders.
    """
    def __init__(self, food: Food, quantity: int):
        self.food = food
        self.quantity = quantity
        self.unit_price = food.selling_price  # locking the price at the time of order placement

    @property
    def total_price(self) -> float:
        return self.unit_price * self.quantity


class Order:
    """
    it is the order class that contains multiple order items.
    """
    STATUS_PENDING = "Pending"
    STATUS_PAID = "Paid"
    STATUS_SENT = "Sent"
    STATUS_CANCELLED = "Cancelled"
    PAYMENT_ONLINE = "Online"
    PAYMENT_CASH = "Cash on Delivery"

    def __init__(self, order_id: str, customer_id: str, items: List[OrderItem], delivery_date: date ,payment_method: str = PAYMENT_ONLINE):
        self.order_id = order_id
        self.customer_id = customer_id
        self.items = items
        self.order_date = datetime.now()
        self.delivery_date = delivery_date
        self.status = self.STATUS_PENDING
        self.payment_method = payment_method
        self._total_amount = sum(item.total_price for item in items)
        self.discount_code: Optional[str] = None
        self.discount_amount: float = 0.0

    @property
    def total_amount(self) -> float:
        return self._total_amount - self.discount_amount

    def apply_discount(self, discount_code: "DiscountCode"):
        """Apply discount code to the order"""
        if discount_code.is_valid():
            self.discount_code  = discount_code.code
            self.discount_amount = self.total_amount * discount_code.discount_percentage / 100
    def update_status(self, new_status: str):
        self.status = new_status


class Cart:
    """
    it is the cart class that contains the items for the customer.
    """
    def __init__(self):
        self.items: List[OrderItem] = []

    def add_item(self, food: Food, quantity: int):
        # checking the stock before adding
        if food.is_available(quantity):
            # checking if the item is already in the cart (for updating the quantity)
            for item in self.items:
                if item.food.food_id == food.food_id:
                    if food.is_available(item.quantity + quantity):
                        item.quantity += quantity
                        return
                    else:
                        raise ValueError("Stock is not enough")
            
            # if the item is not already in the cart, create a new item
            self.items.append(OrderItem(food, quantity))
        else:
            raise ValueError("Stock is not enough")

    def remove_item(self, food_id: str):
        self.items = [item for item in self.items if item.food.food_id != food_id]

    def clear(self):
        self.items = []

    def get_total(self) -> float:
        return sum(item.total_price for item in self.items)

@dataclass
class Review:
    """Customer review for an order"""
    review_id: str
    customer_id: str
    order_id: str
    rating: int  #up to 5
    comment: str
    review_date: datetime = field(default_factory=datetime.now)
@dataclass
class DiscountCode:
    """Discount code for customers"""
    code: str
    discount_percentage: float  
    expiry_date: datetime
    is_used: bool = False
    customer_id: Optional[str] = None  # a special code for a customer
    
    def is_valid(self) -> bool:
        """Check if discount code is still valid"""
        return not self.is_used and datetime.now() < self.expiry_date    