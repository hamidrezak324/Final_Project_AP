from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import uuid

# -------------------------------------------------------
# 1. کلاس کاربر (Abstraction & Inheritance)
# -------------------------------------------------------

class User(ABC):
    """
    کلاس انتزاعی پایه برای تمام کاربران سیستم.
    """
    def __init__(self, user_id: str, first_name: str, last_name: str, email: str, password: str):
        self._user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self._password = password  # باید هش شود، فعلاً به صورت متن ساده نگه میداریم

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @abstractmethod
    def get_role(self) -> str:
        """نقش کاربر را برمی‌گرداند"""
        pass

    def verify_password(self, input_password: str) -> bool:
        return self._password == input_password


class Customer(User):
    """
    کلاس مشتری که از User ارث‌بری می‌کند.
    """
    def __init__(self, user_id: str, first_name: str, last_name: str, email: str, password: str, 
                 phone: str, national_code: str, loyalty_points: int = 0):
        super().__init__(user_id, first_name, last_name, email, password)
        self.phone = phone
        self.national_code = national_code
        self.loyalty_points = loyalty_points
        self._cart: Optional['Cart'] = Cart()

    def get_role(self) -> str:
        return "Customer"

    def add_to_loyalty(self, points: int):
        self.loyalty_points += points


class Admin(User):
    """
    کلاس مدیر که از User ارث‌بری می‌کند.
    """
    def __init__(self, user_id: str, first_name: str, last_name: str, email: str, password: str, personnel_id: str):
        super().__init__(user_id, first_name, last_name, email, password)
        self.personnel_id = personnel_id

    def get_role(self) -> str:
        return "Admin"


# -------------------------------------------------------
# 2. کلاس‌های غذا و سفارش (Composition & Encapsulation)
# -------------------------------------------------------

@dataclass
class Food:
    """
    کلاس مربوط به غذاها.
    """
    food_id: str
    name: str
    category: str
    selling_price: float   # قیمت فروش به مشتری
    cost_price: float       # قیمت تمام شده برای محاسبه سود
    ingredients: str
    description: str
    stock: int              # موجودی
    image_path: Optional[str] = None

    def is_available(self, requested_quantity: int = 1) -> bool:
        return self.stock >= requested_quantity


class OrderItem:
    """
    آیتم‌های داخل یک سفارش (Composition).
    قیمت در لحظه ثبت سفارش ذخیره می‌شود تا تغییرات قیمت آینده روی سفارش‌های قبلی اثر نگذارد.
    """
    def __init__(self, food: Food, quantity: int):
        self.food = food
        self.quantity = quantity
        self.unit_price = food.selling_price  # قفل شدن قیمت در زمان سفارش

    @property
    def total_price(self) -> float:
        return self.unit_price * self.quantity


class Order:
    """
    کلاس سفارش که شامل چندین OrderItem است.
    """
    STATUS_PENDING = "Pending"
    STATUS_PAID = "Paid"
    STATUS_SENT = "Sent"
    STATUS_CANCELLED = "Cancelled"

    def __init__(self, order_id: str, customer_id: str, items: List[OrderItem]):
        self.order_id = order_id
        self.customer_id = customer_id
        self.items = items
        self.order_date = datetime.now()
        self.status = self.STATUS_PENDING
        self._total_amount = sum(item.total_price for item in items)

    @property
    def total_amount(self) -> float:
        return self._total_amount

    def update_status(self, new_status: str):
        self.status = new_status


class Cart:
    """
    سبد خرید موقت مشتری.
    """
    def __init__(self):
        self.items: List[OrderItem] = []

    def add_item(self, food: Food, quantity: int):
        # چک کردن موجودی قبل از افزودن
        if food.is_available(quantity):
            # بررسی وجود قبلی در سبد (برای آپدیت تعداد)
            for item in self.items:
                if item.food.food_id == food.food_id:
                    if food.is_available(item.quantity + quantity):
                        item.quantity += quantity
                        return
                    else:
                        raise ValueError("موجودی کافی نیست")
            
            # اگر قبلاً نبود، آیتم جدید بساز
            self.items.append(OrderItem(food, quantity))
        else:
            raise ValueError("موجودی کافی نیست")

    def remove_item(self, food_id: str):
        self.items = [item for item in self.items if item.food.food_id != food_id]

    def clear(self):
        self.items = []

    def get_total(self) -> float:
        return sum(item.total_price for item in self.items)