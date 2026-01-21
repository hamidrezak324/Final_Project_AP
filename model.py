from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, date
import uuid

# -------------------------------------------------------
# Discount Code
# -------------------------------------------------------

@dataclass
class DiscountCode:
    """Discount code for customers"""
    code: str
    discount_percentage: float  
    expiry_date: datetime
    is_used: bool = False
    customer_id: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if discount code is still valid"""
        return not self.is_used and datetime.now() < self.expiry_date

# -------------------------------------------------------
# User Classes
# -------------------------------------------------------

class User(ABC):
    """Base class for all users"""
    def __init__(self, user_id: str, first_name: str, last_name: str, email: str, password: str):
        self._user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self._password = password

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
        pass

    def verify_password(self, input_password: str) -> bool:
        return self._password == input_password
    
    def update_email(self, new_email: str): self.email = new_email
    def update_password(self, new_password: str): self._password = new_password
    def update_name(self, first_name: str, last_name: str): 
        self.first_name = first_name
        self.last_name = last_name    

class Customer(User):
    def __init__(self, user_id: str, first_name: str, last_name: str, email: str, password: str, 
                 phone: str, national_code: str, address: str = "", loyalty_points: int = 0):
        super().__init__(user_id, first_name, last_name, email, password)
        self.phone = phone
        self.national_code = national_code
        self.address = address
        self.loyalty_points = loyalty_points
        self._cart: Optional['Cart'] = Cart()

    def get_role(self) -> str: return "Customer"
    def add_to_loyalty(self, points: int): self.loyalty_points += points

class Admin(User):
    def __init__(self, user_id: str, first_name: str, last_name: str, email: str, password: str, personnel_id: str):
        super().__init__(user_id, first_name, last_name, email, password)
        self.personnel_id = personnel_id
    def get_role(self) -> str: return "Admin"

# -------------------------------------------------------
# Food & Order Classes
# -------------------------------------------------------

@dataclass
class Food:
    food_id: str
    restaurant_id: str
    name: str
    category: str
    selling_price: float
    cost_price: float
    ingredients: str
    description: str
    stock: int
    available_dates: List[date] = field(default_factory=list)
    image_path: Optional[str] = None

    def is_available(self, requested_quantity: int = 1) -> bool:
        return self.stock >= requested_quantity
    def decrease_stock(self, quantity: int):
        if self.stock >= quantity: self.stock -= quantity
        else: raise ValueError("Not enough stock")
    def increase_stock(self, quantity: int):
        self.stock += quantity

class OrderItem:
    def __init__(self, food: Food, quantity: int):
        self.food = food
        self.quantity = quantity
        self.unit_price = food.selling_price

    @property
    def total_price(self) -> float:
        return self.unit_price * self.quantity

class Order:
    STATUS_PENDING = "Pending"
    STATUS_PAID = "Paid"
    STATUS_SENT = "Sent"
    STATUS_CANCELLED = "Cancelled"
    PAYMENT_ONLINE = "Online"
    PAYMENT_CASH = "Cash on Delivery"

    def __init__(self,  restaurant_id: str, order_id: str, customer_id: str, items: List[OrderItem], delivery_date: date ,payment_method: str = PAYMENT_ONLINE):
        self.restaurant_id = restaurant_id
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

    def apply_discount(self, discount_code_obj: 'DiscountCode'):
        if discount_code_obj.is_valid():
            self.discount_code = discount_code_obj.code
            # calculating discount due to base price
            self.discount_amount = self._total_amount * discount_code_obj.discount_percentage / 100

    def update_status(self, new_status: str):
        self.status = new_status

class Cart:
    def __init__(self):
        self.items: List[OrderItem] = []

    def add_item(self, food: Food, quantity: int):
        if food.is_available(quantity):
            for item in self.items:
                if item.food.food_id == food.food_id:
                    if food.is_available(item.quantity + quantity):
                        item.quantity += quantity
                        return
                    else:
                        raise ValueError("Stock is not enough")
            self.items.append(OrderItem(food, quantity))
        else:
            raise ValueError("Stock is not enough")

    def remove_item(self, food_id: str):
        self.items = [item for item in self.items if item.food.food_id != food_id]
    def clear(self): self.items = []
    def get_total(self) -> float: return sum(item.total_price for item in self.items)

@dataclass
class Review:
    review_id: str
    customer_id: str
    order_id: str
    rating: int # up to 5
    comment: str
    review_date: datetime = field(default_factory=datetime.now)