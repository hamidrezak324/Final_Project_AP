import os
import sys
from datetime import date, timedelta
from model import Food, User
from database import Database
from auth import AuthManager
from food_service import FoodService
from order_service import OrderService
from customer_service import CustomerService
from admin_service import AdminService

# --- Initial setup and utilities ---
def reset_database():
    """Delete all CSV files to start with a clean test environment"""
    files = [
        "users.csv", "foods.csv", "orders.csv", "order_items.csv",
        "reviews.csv", "discount_codes.csv"
    ]
    for f in files:
        if os.path.exists(f):
            os.remove(f)

def setup_data():
    """Create initial data required for tests"""
    reset_database()
    db = Database()

    # Create a test user
    user_data = {
        'user_id': 'test_user',
        'role': 'Customer',
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@example.com',
        'password': 'StrongPass1',
        'phone': '09123456789',
        'national_code': '1234567890',
        'address': 'Tehran',
        'personnel_id': '',
        'loyalty_points': 0,
        'failed_attempts': 0,
        'is_locked': False
    }

    cols = [
        'user_id', 'role', 'first_name', 'last_name', 'email', 'password',
        'phone', 'national_code', 'address', 'personnel_id',
        'loyalty_points', 'failed_attempts', 'is_locked'
    ]

    import pandas as pd
    pd.DataFrame([user_data], columns=cols).to_csv('users.csv', index=False)

    # Create a food item with limited stock
    today = date.today()
    food = Food(
        food_id="test_food_1",
        name="Test Burger",
        category="Fast Food",
        selling_price=100000,
        cost_price=50000,
        ingredients="Meat",
        description="Test",
        stock=5,
        available_dates=[today]
    )
    db.save_food(food)

    # Create a food item with zero stock (Edge Case)
    food_zero = Food(
        food_id="test_food_zero",
        name="Empty Stock",
        category="Drink",
        selling_price=20000,
        cost_price=10000,
        ingredients="Air",
        description="None",
        stock=0,
        available_dates=[today]
    )
    db.save_food(food_zero)

print("=" * 60)
print("Starting Phase 7 Tests (Unit Tests)")
print("=" * 60)

# --- Section 1: User and Authentication Tests (5 tests) ---
print("\n--- Section 1: User and Authentication Tests ---")
auth_mgr = AuthManager()

# Test 1: Registration with duplicate email
try:
    setup_data()
    auth_mgr.register_customer(
        "Test", "User", "test@example.com",
        "09123456789", "1234567890",
        "StrongPass1", "StrongPass1"
    )
    assert False, "Test 1 failed: Duplicate email error was expected"
except ValueError as e:
    if "Email already exists" in str(e):
        print("✅ Test 1 (Duplicate Email): Passed")
    else:
        print(f"❌ Test 1 (Duplicate Email): Wrong error - {e}")

# Test 2: Registration with weak password
try:
    setup_data()
    auth_mgr.register_customer(
        "Test", "User2", "new@test.com",
        "09123456789", "1234567890",
        "weak", "weak"
    )
    assert False, "Test 2 failed: Weak password error was expected"
except ValueError as e:
    if "8" in str(e) or "minimum" in str(e).lower():
        print("✅ Test 2 (Password Validation): Passed")
    else:
        print(f"❌ Test 2 (Password Validation): Wrong error - {e}")

# Test 3: Successful login with correct credentials
try:
    setup_data()
    status, msg, user_obj = auth_mgr.login_user(
        "test@example.com", "StrongPass1", is_admin=False
    )
    assert status is True and user_obj is not None
    print("✅ Test 3 (Successful Login): Passed")
except Exception as e:
    print(f"❌ Test 3 (Successful Login): Failed - {e}")

# Test 4: Account lock after 3 failed login attempts
try:
    setup_data()
    auth_mgr.login_user("test@example.com", "wrong1", is_admin=False)
    auth_mgr.login_user("test@example.com", "wrong2", is_admin=False)
    auth_mgr.login_user("test@example.com", "wrong3", is_admin=False)

    # Attempt login with correct password (should fail because account is locked)
    status, msg, _ = auth_mgr.login_user(
        "test@example.com", "StrongPass1", is_admin=False
    )
    assert status is False and ("locked" in msg.lower())
    print("✅ Test 4 (Account Lock): Passed")
except Exception as e:
    print(f"❌ Test 4 (Account Lock): Failed - {e}")

# Test 5: Admin login with personnel ID (not registered)
try:
    setup_data()
    status, _, _ = auth_mgr.login_user("9999", "adminpass", is_admin=True)
    assert status is False
    print("✅ Test 5 (Admin Not Found): Passed")
except Exception as e:
    print(f"❌ Test 5 (Admin Not Found): Failed - {e}")

# --- Section 2: Order Logic and Inventory Tests (5 tests + Edge Cases) ---
print("\n--- Section 2: Order Logic and Inventory Tests ---")
food_svc = FoodService()
order_svc = OrderService()

# Test 6: Edge Case - Add zero-stock item to cart
try:
    setup_data()
    from model import Cart
    cart = Cart()
    try:
        food_svc.add_to_cart(cart, "test_food_zero", 1)
        assert False, "Test 6 failed: Should not allow adding zero-stock item"
    except ValueError:
        print("✅ Test 6 (Edge Case - Zero Stock): Passed")
except Exception as e:
    print(f"❌ Test 6 (Edge Case - Zero Stock): Failed - {e}")

# Test 7: Edge Case - Purchase more than available stock
try:
    setup_data()
    cart = Cart()
    food_svc.add_to_cart(cart, "test_food_1", 3)  # Stock is 5
    try:
        food_svc.add_to_cart(cart, "test_food_1", 3)  # Total becomes 6 > 5
        assert False, "Test 7 failed: Should not allow purchase beyond stock"
    except ValueError:
        print("✅ Test 7 (Edge Case - Exceed Stock): Passed")
except Exception as e:
    print(f"❌ Test 7 (Edge Case - Exceed Stock): Failed - {e}")

# Test 8: Stock reduction after checkout
try:
    setup_data()
    cart = Cart()
    food_svc.add_to_cart(cart, "test_food_1", 2)
    order = order_svc.checkout(cart, "test_user", date.today(), "Online")

    db = Database()
    foods_df = db.load_foods()
    stock = int(foods_df[foods_df['food_id'] == "test_food_1"].iloc[0]['stock'])

    assert stock == 3, f"Test 8 failed: Stock should be 3 but is {stock}"
    print("✅ Test 8 (Stock Reduction on Checkout): Passed")
except Exception as e:
    print(f"❌ Test 8 (Stock Reduction on Checkout): Failed - {e}")

# Test 9: Edge Case - Checkout empty cart
try:
    setup_data()
    cart = Cart()
    try:
        order_svc.checkout(cart, "test_user", date.today(), "Online")
        assert False, "Test 9 failed: Should not checkout empty cart"
    except ValueError:
        print("✅ Test 9 (Edge Case - Empty Cart): Passed")
except Exception as e:
    print(f"❌ Test 9 (Edge Case - Empty Cart): Failed - {e}")

# Test 10: Edge Case - Cancel order and restore stock
try:
    setup_data()
    cart = Cart()
    food_svc.add_to_cart(cart, "test_food_1", 2)
    order = order_svc.checkout(cart, "test_user", date.today(), "Online")

    # Cancel the order
    order_svc.cancel_order(order.order_id)

    db = Database()
    foods_df = db.load_foods()
    stock = int(foods_df[foods_df['food_id'] == "test_food_1"].iloc[0]['stock'])

    assert stock == 5, f"Test 10 failed: Stock should return to 5 but is {stock}"
    print("✅ Test 10 (Edge Case - Stock Restore on Cancel): Passed")
except Exception as e:
    print(f"❌ Test 10 (Edge Case - Stock Restore on Cancel): Failed - {e}")

print("\n" + "=" * 60)
print("All tests completed.")
print("=" * 60)
