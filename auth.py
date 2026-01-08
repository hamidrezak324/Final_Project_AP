import re
import uuid
import pandas as pd
from model import Customer, Admin
from database import Database


class AuthManager:
    """Authentication and user management service"""
    
    def __init__(self):
        self.db = Database()

    # -------------------------------------------------------
    # Private Validators (Helper Methods)
    # -------------------------------------------------------
    
    def _validate_name(self, name: str) -> tuple[bool, str]:
        """Validate that name contains only letters and spaces"""
        if not name or not name.strip():
            return False, "Name cannot be empty"
        
        # Only Persian/English letters and spaces allowed
        pattern = r'^[a-zA-Zآ-ی\s]+$'
        if not re.match(pattern, name):
            return False, "Name cannot contain numbers or special characters"
        
        return True, ""
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format (Z.Y@X)"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _validate_phone(self, phone: str) -> bool:
        """Validate Iranian phone number (09XXXXXXXXX)"""
        pattern = r'^09\d{9}$'
        return re.match(pattern, phone) is not None

    def _validate_national_code(self, code: str) -> bool:
        """Validate Iranian national code (10 digits)"""
        return len(code) == 10 and code.isdigit()

    def _validate_password(self, password: str) -> tuple[bool, str]:
        """
        Validate password strength:
        - At least 8 characters
        - At least one uppercase letter
        - At least one digit
        - At least one special character
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"
        if not re.search(r"[^A-Za-z0-9]", password):
            return False, "Password must contain at least one special character"
        
        return True, ""

    def _send_notification(self, email: str, message: str):
        """Mock method for sending email/SMS notifications"""
        print(f"[SIMULATED EMAIL] To: {email} | Message: {message}")

    # -------------------------------------------------------
    # Registration
    # -------------------------------------------------------
    
    def register_customer(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        national_code: str,
        password: str,
        confirm_password: str,
        address: str = ""
    ) -> tuple[bool, str]:
        """Register a new customer with full validation"""

        # 1. Validate names
        is_valid, msg = self._validate_name(first_name)
        if not is_valid:
            return False, f"First name: {msg}"
        
        is_valid, msg = self._validate_name(last_name)
        if not is_valid:
            return False, f"Last name: {msg}"

        # 2. Format validation
        if not self._validate_email(email):
            return False, "Invalid email format"
        
        if not self._validate_phone(phone):
            return False, "Invalid phone number format (example: 09123456789)"
        
        if not self._validate_national_code(national_code):
            return False, "National code must be exactly 10 digits"

        # 3. Password validation
        is_valid_pwd, pwd_msg = self._validate_password(password)
        if not is_valid_pwd:
            return False, pwd_msg

        if password != confirm_password:
            return False, "Password and confirmation do not match"

        # 4. Create user object
        user_id = str(uuid.uuid4())
        new_customer = Customer(
            user_id, first_name, last_name, email, password,
            phone, national_code, address, 0
        )

        # 5. Save to database (database checks for duplicates)
        try:
            self.db.save_user(new_customer)
            self._send_notification(email, "Your account has been successfully created.")
            return True, "Registration completed successfully"
        except ValueError as e:
            return False, str(e)

    # -------------------------------------------------------
    # Login
    # -------------------------------------------------------
    
    def login_user(
        self,
        identifier: str,  # Email for customer, personnel_id for admin
        password: str,
        is_admin: bool = False
    ) -> tuple[bool, str, object]:
        """
        Login for customer (using email) or admin (using personnel_id).
        Handles account lock after 3 failed attempts.
        """
        
        # Fetch user record
        user_record = None
        if is_admin:
            user_record = self.db.find_admin_by_personnel(identifier)
        else:
            user_record = self.db.find_user_by_email(identifier)

        if user_record is None:
            return False, "User not found with provided credentials", None

        real_email = user_record['email']

        # Check if account is locked
        if user_record['is_locked']:
            return False, "Your account is locked due to multiple failed attempts", None

        # Verify password
        if user_record['password'] == password:
            # Successful login → reset failed attempts
            self.db.update_user_login_state(real_email, 0, False)
            
            # Reconstruct user object
            user_obj = self._create_user_object(user_record)
            return True, "Login successful", user_obj
        else:
            # Failed login attempt
            current_attempts = int(user_record['failed_attempts']) + 1
            is_locked = current_attempts >= 3

            self.db.update_user_login_state(real_email, current_attempts, is_locked)

            if is_locked:
                self._send_notification(
                    real_email,
                    "Your account has been locked after 3 failed login attempts."
                )
                return False, "Your account has been locked. Please contact support.", None
            else:
                return False, f"Incorrect password. {3 - current_attempts} attempts remaining.", None

    # -------------------------------------------------------
    # Profile Management
    # -------------------------------------------------------
    
    def update_profile(
        self,
        email: str,
        first_name: str = None,
        last_name: str = None,
        phone: str = None,
        new_email: str = None,
        new_password: str = None,
        address: str = None
    ) -> tuple[bool, str]:
        """
        Update user profile with validation.
        Only provided fields will be updated.
        """
        updated_fields = {}

        # Validate first name
        if first_name:
            is_valid, msg = self._validate_name(first_name)
            if not is_valid:
                return False, f"First name: {msg}"
            updated_fields['first_name'] = first_name

        # Validate last name
        if last_name:
            is_valid, msg = self._validate_name(last_name)
            if not is_valid:
                return False, f"Last name: {msg}"
            updated_fields['last_name'] = last_name

        # Validate phone
        if phone:
            if not self._validate_phone(phone):
                return False, "Invalid phone number format"
            updated_fields['phone'] = phone

        # Validate new email
        if new_email and new_email != email:
            if not self._validate_email(new_email):
                return False, "Invalid email format"
            
            # Check if new email already exists
            if self.db.find_user_by_email(new_email) is not None:
                return False, "Email already exists"
            
            updated_fields['email'] = new_email

        # Validate new password
        if new_password:
            is_valid, msg = self._validate_password(new_password)
            if not is_valid:
                return False, msg
            updated_fields['password'] = new_password

        # Update address (no validation needed)
        if address is not None:
            updated_fields['address'] = address

        # Apply updates
        if not updated_fields:
            return False, "No fields to update"

        try:
            self.db.update_user_profile(email, updated_fields)
            return True, "Profile updated successfully"
        except ValueError as e:
            return False, str(e)

    def unlock_account(self, email: str) -> tuple[bool, str]:
        """Unlock a user account (e.g., by admin request)"""
        try:
            self.db.update_user_login_state(email, 0, False)
            self._send_notification(email, "Your account has been unlocked.")
            return True, "Account unlocked successfully"
        except Exception as e:
            return False, str(e)

    # -------------------------------------------------------
    # Helper: Create User Object from Database Record
    # -------------------------------------------------------
    
    def _create_user_object(self, record):
        """Reconstruct User object from database record"""
        
        if record['role'] == 'Customer':
            return Customer(
                user_id=record['user_id'],
                first_name=record['first_name'],
                last_name=record['last_name'],
                email=record['email'],
                password=record['password'],
                phone=record['phone'] if pd.notna(record['phone']) else '',
                national_code=record['national_code'] if pd.notna(record['national_code']) else '',
                address=record['address'] if pd.notna(record['address']) else '',
                loyalty_points=int(record['loyalty_points']) if pd.notna(record['loyalty_points']) else 0
            )
        elif record['role'] == 'Admin':
            return Admin(
                user_id=record['user_id'],
                first_name=record['first_name'],
                last_name=record['last_name'],
                email=record['email'],
                password=record['password'],
                personnel_id=record['personnel_id']
            )
        
        return None