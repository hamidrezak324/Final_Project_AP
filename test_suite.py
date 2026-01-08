import unittest
import os
import uuid
from datetime import date, datetime, timedelta
from model import Customer, Admin, Food, Cart, Order, OrderItem, DiscountCode, Review
from database import Database
from auth import AuthManager
from food_service import FoodService
from customer_service import CustomerService
from order_service import OrderService
from admin_service import AdminService


class TestAuthManager(unittest.TestCase):
    """تست‌های مربوط به احراز هویت و مدیریت کاربران"""

    def setUp(self):
        """راه‌اندازی اولیه قبل از هر تست"""
        self._cleanup_test_files()
        self.auth = AuthManager()

    def tearDown(self):
        """پاکسازی بعد از هر تست"""
        self._cleanup_test_files()

    def _cleanup_test_files(self):
        """حذف فایل‌های CSV تستی"""
        files = ['users.csv', 'foods.csv', 'orders.csv', 'order_items.csv', 
                 'reviews.csv', 'discount_codes.csv']
        for f in files:
            if os.path.exists(f):
                os.remove(f)

    def test_register_customer_success(self):
        """تست ثبت‌نام موفق مشتری"""
        success, msg = self.auth.register_customer(
            first_name="علی",
            last_name="محمدی",
            email="ali@example.com",
            phone="09123456789",
            national_code="1234567890",
            password="Test@1234",
            confirm_password="Test@1234"
        )
        self.assertTrue(success)
        self.assertIn("successfully", msg.lower())

    def test_register_duplicate_email(self):
        """تست ثبت‌نام با ایمیل تکراری - Test 1 از فایل قدیمی"""
        self.auth.register_customer(
            "علی", "محمدی", "test@example.com", "09123456789",
            "1234567890", "Test@1234", "Test@1234"
        )
        success, msg = self.auth.register_customer(
            "رضا", "احمدی", "test@example.com", "09987654321",
            "0987654321", "Test@1234", "Test@1234"
        )
        self.assertFalse(success)
        self.assertIn("email already exists", msg.lower())

    def test_register_invalid_email(self):
        """تست ثبت‌نام با ایمیل نامعتبر"""
        success, msg = self.auth.register_customer(
            first_name="علی",
            last_name="محمدی",
            email="invalid-email",
            phone="09123456789",
            national_code="1234567890",
            password="Test@1234",
            confirm_password="Test@1234"
        )
        self.assertFalse(success)
        self.assertIn("email", msg.lower())

    def test_register_weak_password(self):
        """تست ثبت‌نام با رمز عبور ضعیف - Test 2 از فایل قدیمی"""
        success, msg = self.auth.register_customer(
            first_name="علی",
            last_name="محمدی",
            email="ali@example.com",
            phone="09123456789",
            national_code="1234567890",
            password="weak",
            confirm_password="weak"
        )
        self.assertFalse(success)
        self.assertIn("password", msg.lower())

    def test_register_password_mismatch(self):
        """تست عدم تطابق رمز عبور"""
        success, msg = self.auth.register_customer(
            first_name="علی",
            last_name="محمدی",
            email="ali@example.com",
            phone="09123456789",
            national_code="1234567890",
            password="Test@1234",
            confirm_password="Test@5678"
        )
        self.assertFalse(success)
        self.assertIn("match", msg.lower())

    def test_login_success(self):
        """تست ورود موفق - Test 3 از فایل قدیمی"""
        self.auth.register_customer(
            "علی", "محمدی", "ali@example.com", "09123456789",
            "1234567890", "Test@1234", "Test@1234"
        )
        success, msg, user = self.auth.login_user("ali@example.com", "Test@1234")
        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "ali@example.com")

    def test_login_wrong_password(self):
        """تست ورود با رمز عبور اشتباه"""
        self.auth.register_customer(
            "علی", "محمدی", "ali@example.com", "09123456789",
            "1234567890", "Test@1234", "Test@1234"
        )
        success, msg, user = self.auth.login_user("ali@example.com", "WrongPass@123")
        self.assertFalse(success)
        self.assertIsNone(user)

    def test_account_lock_after_three_attempts(self):
        """تست قفل شدن حساب بعد از 3 تلاش ناموفق - Test 4 از فایل قدیمی"""
        self.auth.register_customer(
            "علی", "محمدی", "ali@example.com", "09123456789",
            "1234567890", "Test@1234", "Test@1234"
        )

        # تلاش اول
        self.auth.login_user("ali@example.com", "wrong1")
        # تلاش دوم
        self.auth.login_user("ali@example.com", "wrong2")
        # تلاش سوم
        self.auth.login_user("ali@example.com", "wrong3")

        # حساب باید قفل شده باشد
        success, msg, user = self.auth.login_user("ali@example.com", "Test@1234")
        self.assertFalse(success)
        self.assertIn("locked", msg.lower())
        self.assertIsNone(user)

    def test_admin_login_not_found(self):
        """تست ورود ادمین با شناسه پرسنلی نامعتبر - Test 5 از فایل قدیمی"""
        success, msg, user = self.auth.login_user("9999", "adminpass", is_admin=True)
        self.assertFalse(success)
        self.assertIsNone(user)


class TestFoodService(unittest.TestCase):
    """تست‌های مربوط به مدیریت غذاها و سبد خرید"""

    def setUp(self):
        self._cleanup_test_files()
        self.food_service = FoodService()
        self.test_food = Food(
            food_id="test-food-1",
            name="پیتزا",
            category="فست‌فود",
            selling_price=50000,
            cost_price=30000,
            ingredients="پنیر، گوجه",
            description="پیتزا خوشمزه",
            stock=10,
            available_dates=[date.today()]
        )
        self.food_service.db.save_food(self.test_food)

        # غذا با موجودی صفر برای تست edge case
        self.zero_stock_food = Food(
            food_id="test-food-zero",
            name="نوشابه",
            category="نوشیدنی",
            selling_price=20000,
            cost_price=10000,
            ingredients="آب، قند",
            description="نوشابه",
            stock=0,
            available_dates=[date.today()]
        )
        self.food_service.db.save_food(self.zero_stock_food)

    def tearDown(self):
        self._cleanup_test_files()

    def _cleanup_test_files(self):
        files = ['users.csv', 'foods.csv', 'orders.csv', 'order_items.csv', 
                 'reviews.csv', 'discount_codes.csv']
        for f in files:
            if os.path.exists(f):
                os.remove(f)

    def test_get_food_by_id(self):
        """تست دریافت غذا با شناسه"""
        food = self.food_service.get_food_by_id("test-food-1")
        self.assertIsNotNone(food)
        self.assertEqual(food.name, "پیتزا")

    def test_get_menu_for_date(self):
        """تست دریافت منوی روز"""
        menu = self.food_service.get_menu_for_date(date.today())
        self.assertGreaterEqual(len(menu), 1)

    def test_add_to_cart_success(self):
        """تست افزودن به سبد خرید با موفقیت"""
        cart = Cart()
        self.food_service.add_to_cart(cart, "test-food-1", 2)
        self.assertEqual(len(cart.items), 1)
        self.assertEqual(cart.items[0].quantity, 2)

    def test_add_to_cart_zero_stock(self):
        """تست افزودن محصول با موجودی صفر - Test 6 از فایل قدیمی"""
        cart = Cart()
        with self.assertRaises(ValueError) as context:
            self.food_service.add_to_cart(cart, "test-food-zero", 1)
        self.assertIn("stock", str(context.exception).lower())

    def test_add_to_cart_insufficient_stock(self):
        """تست خرید بیش از موجودی انبار - Test 7 از فایل قدیمی"""
        cart = Cart()
        self.food_service.add_to_cart(cart, "test-food-1", 3)
        with self.assertRaises(ValueError) as context:
            self.food_service.add_to_cart(cart, "test-food-1", 8)
        self.assertIn("stock", str(context.exception).lower())

    def test_search_foods(self):
        """تست جستجوی غذا"""
        results = self.food_service.search_foods("پیتزا")
        self.assertGreaterEqual(len(results), 1)


class TestOrderService(unittest.TestCase):
    """تست‌های مربوط به مدیریت سفارشات"""

    def setUp(self):
        self._cleanup_test_files()
        self.order_service = OrderService()
        self.auth = AuthManager()

        # ثبت مشتری تستی
        self.auth.register_customer(
            "علی", "محمدی", "customer@test.com", "09123456789",
            "1234567890", "Test@1234", "Test@1234"
        )
        _, _, self.customer = self.auth.login_user("customer@test.com", "Test@1234")

        # افزودن غذا
        self.test_food = Food(
            food_id="test-food-1",
            name="پیتزا",
            category="فست‌فود",
            selling_price=50000,
            cost_price=30000,
            ingredients="پنیر",
            description="پیتزا خوشمزه",
            stock=10,
            available_dates=[date.today()]
        )
        self.order_service.db.save_food(self.test_food)

    def tearDown(self):
        self._cleanup_test_files()

    def _cleanup_test_files(self):
        files = ['users.csv', 'foods.csv', 'orders.csv', 'order_items.csv', 
                 'reviews.csv', 'discount_codes.csv']
        for f in files:
            if os.path.exists(f):
                os.remove(f)

    def test_checkout_success(self):
        """تست تسویه حساب موفق"""
        cart = Cart()
        cart.add_item(self.test_food, 2)

        order = self.order_service.checkout(
            cart=cart,
            customer_id=self.customer.user_id,
            delivery_date=date.today() + timedelta(days=1),
            payment_method=Order.PAYMENT_ONLINE
        )

        self.assertIsNotNone(order)
        self.assertEqual(order.status, Order.STATUS_PENDING)
        self.assertEqual(len(order.items), 1)

    def test_checkout_empty_cart(self):
        """تست تسویه حساب با سبد خالی - Test 9 از فایل قدیمی"""
        cart = Cart()
        with self.assertRaises(ValueError) as context:
            self.order_service.checkout(
                cart=cart,
                customer_id=self.customer.user_id,
                delivery_date=date.today() + timedelta(days=1),
                payment_method=Order.PAYMENT_ONLINE
            )
        self.assertIn("empty", str(context.exception).lower())

    def test_stock_reduction_after_checkout(self):
        """تست کاهش موجودی بعد از checkout - Test 8 از فایل قدیمی"""
        cart = Cart()
        cart.add_item(self.test_food, 2)

        # موجودی اولیه
        initial_stock = self.order_service.db.find_food_by_id("test-food-1")['stock']

        # انجام checkout
        order = self.order_service.checkout(
            cart=cart,
            customer_id=self.customer.user_id,
            delivery_date=date.today() + timedelta(days=1),
            payment_method=Order.PAYMENT_ONLINE
        )

        # بررسی موجودی بعد از checkout
        final_stock = self.order_service.db.find_food_by_id("test-food-1")['stock']
        self.assertEqual(final_stock, initial_stock - 2)

    def test_cancel_order_restores_stock(self):
        """تست بازگشت موجودی بعد از لغو سفارش - Test 10 از فایل قدیمی"""
        cart = Cart()
        cart.add_item(self.test_food, 2)

        order = self.order_service.checkout(
            cart=cart,
            customer_id=self.customer.user_id,
            delivery_date=date.today() + timedelta(days=1),
            payment_method=Order.PAYMENT_ONLINE
        )

        # موجودی قبل از لغو
        stock_after_order = self.order_service.db.find_food_by_id("test-food-1")['stock']

        # لغو سفارش
        self.order_service.cancel_order(order.order_id)

        # بررسی بازگشت موجودی
        final_stock = self.order_service.db.find_food_by_id("test-food-1")['stock']
        self.assertEqual(final_stock, stock_after_order + 2)


class TestCustomerService(unittest.TestCase):
    """تست‌های مربوط به خدمات مشتری"""

    def setUp(self):
        self._cleanup_test_files()
        self.customer_service = CustomerService()
        self.auth = AuthManager()

        self.auth.register_customer(
            "علی", "محمدی", "customer@test.com", "09123456789",
            "1234567890", "Test@1234", "Test@1234"
        )
        _, _, self.customer = self.auth.login_user("customer@test.com", "Test@1234")

    def tearDown(self):
        self._cleanup_test_files()

    def _cleanup_test_files(self):
        files = ['users.csv', 'foods.csv', 'orders.csv', 'order_items.csv', 
                 'reviews.csv', 'discount_codes.csv']
        for f in files:
            if os.path.exists(f):
                os.remove(f)

    def test_get_user_points(self):
        """تست دریافت امتیاز وفاداری"""
        points = self.customer_service.get_user_points(self.customer.user_id)
        self.assertEqual(points, 0)

    def test_add_purchase_points(self):
        """تست افزودن امتیاز خرید"""
        self.customer_service.add_purchase_points(self.customer.user_id, 5000)
        points = self.customer_service.get_user_points(self.customer.user_id)
        self.assertEqual(points, 5)

    def test_generate_discount_code(self):
        """تست تولید کد تخفیف"""
        self.customer_service.db.add_loyalty_points(self.customer.user_id, 100)
        discount = self.customer_service.generate_discount_code(self.customer.user_id, 100)

        self.assertIsNotNone(discount)
        self.assertEqual(discount.discount_percentage, 10.0)
        self.assertTrue(discount.is_valid())


class TestAdminService(unittest.TestCase):
    """تست‌های مربوط به خدمات ادمین"""

    def setUp(self):
        self._cleanup_test_files()
        self.admin_service = AdminService()

    def tearDown(self):
        self._cleanup_test_files()

    def _cleanup_test_files(self):
        files = ['users.csv', 'foods.csv', 'orders.csv', 'order_items.csv', 
                 'reviews.csv', 'discount_codes.csv']
        for f in files:
            if os.path.exists(f):
                os.remove(f)

    def test_add_new_food(self):
        """تست افزودن غذای جدید"""
        food = self.admin_service.add_new_food(
            name="برگر",
            category="فست‌فود",
            selling_price=40000,
            cost_price=25000,
            ingredients="گوشت، نان",
            description="برگر خوشمزه",
            stock=15,
            available_dates_list=[date.today()]
        )

        self.assertIsNotNone(food)
        self.assertEqual(food.name, "برگر")

    def test_update_food_info(self):
        """تست به‌روزرسانی اطلاعات غذا"""
        food = self.admin_service.add_new_food(
            name="برگر",
            category="فست‌فود",
            selling_price=40000,
            cost_price=25000,
            ingredients="گوشت، نان",
            description="برگر خوشمزه",
            stock=15,
            available_dates_list=[date.today()]
        )

        self.admin_service.update_food_info(food.food_id, selling_price=45000)
        updated_food = self.admin_service.food_service.get_food_by_id(food.food_id)
        self.assertEqual(updated_food.selling_price, 45000)

    def test_create_discount_for_customer(self):
        """تست ایجاد کد تخفیف برای مشتری"""
        auth = AuthManager()
        auth.register_customer(
            "علی", "محمدی", "customer@test.com", "09123456789",
            "1234567890", "Test@1234", "Test@1234"
        )
        _, _, customer = auth.login_user("customer@test.com", "Test@1234")

        discount = self.admin_service.create_discount_for_customer(
            customer.user_id, 15.0
        )

        self.assertIsNotNone(discount)
        self.assertEqual(discount.discount_percentage, 15.0)


class TestModels(unittest.TestCase):
    """تست‌های مربوط به مدل‌های داده"""

    def test_food_is_available(self):
        """تست موجودی غذا"""
        food = Food(
            food_id="test-1",
            name="پیتزا",
            category="فست‌فود",
            selling_price=50000,
            cost_price=30000,
            ingredients="پنیر",
            description="پیتزا",
            stock=5
        )

        self.assertTrue(food.is_available(3))
        self.assertFalse(food.is_available(10))

    def test_discount_code_validation(self):
        """تست اعتبار کد تخفیف"""
        valid_code = DiscountCode(
            code="TEST123",
            discount_percentage=10.0,
            expiry_date=datetime.now() + timedelta(days=1)
        )
        self.assertTrue(valid_code.is_valid())

        expired_code = DiscountCode(
            code="EXPIRED",
            discount_percentage=10.0,
            expiry_date=datetime.now() - timedelta(days=1)
        )
        self.assertFalse(expired_code.is_valid())

    def test_cart_total_calculation(self):
        """تست محاسبه کل سبد خرید"""
        cart = Cart()
        food1 = Food("1", "پیتزا", "فست‌فود", 50000, 30000, "پنیر", "توضیحات", 10)
        food2 = Food("2", "برگر", "فست‌فود", 40000, 25000, "گوشت", "توضیحات", 10)

        cart.add_item(food1, 2)
        cart.add_item(food2, 1)

        self.assertEqual(cart.get_total(), 140000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
