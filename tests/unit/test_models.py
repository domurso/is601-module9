import pytest
from app.models import hash_password, verify_password, UserCreate, CalculationCreate
from pydantic import ValidationError

# Unit Tests for Password Hashing and Verification
def test_hash_password():
    """
    Test that hash_password generates a valid bcrypt hash.
    """
    password = "securepassword123"
    hashed = hash_password(password)
    assert isinstance(hashed, str)
    assert hashed.startswith("$2b$")  # bcrypt hash prefix
    assert len(hashed) > 50  # Typical bcrypt hash length

def test_verify_password_correct():
    """
    Test that verify_password correctly verifies a matching password.
    """
    password = "securepassword123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    """
    Test that verify_password returns False for an incorrect password.
    """
    password = "securepassword123"
    wrong_password = "wrongpassword"
    hashed = hash_password(password)
    assert verify_password(wrong_password, hashed) is False

# Unit Tests for UserCreate Schema Validation
@pytest.mark.parametrize(
    "username,email,password,should_raise",
    [
        ("testuser", "test@example.com", "secure123", False),  # Valid input
        ("test_user", "test@example.com", "secure123", True),  # Non-alphanumeric username
        ("tu", "test@example.com", "secure123", True),  # Username too short
        ("a" * 51, "test@example.com", "secure123", True),  # Username too long
        ("testuser", "invalid-email", "secure123", True),  # Invalid email
        ("testuser", "test@example.com", "short", True),  # Password too short
    ],
    ids=[
        "valid_user",
        "non_alphanumeric_username",
        "username_too_short",
        "username_too_long",
        "invalid_email",
        "password_too_short",
    ]
)
def test_user_create_validation(username, email, password, should_raise):
    """
    Test UserCreate schema validation for username, email, and password.
    """
    data = {"username": username, "email": email, "password": password}
    if should_raise:
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        assert exc_info.type is ValidationError
    else:
        user = UserCreate(**data)
        assert user.username == username
        assert user.email == email
        assert user.password == password

# Unit Tests for CalculationCreate Schema Validation
@pytest.mark.parametrize(
    "operation,operand_a,operand_b,user_id,should_raise",
    [
        ("add", 10.0, 5.0, 1, False),  # Valid input
        ("invalid", 10.0, 5.0, 1, True),  # Invalid operation
        ("subtract", "invalid", 5.0, 1, True),  # Invalid operand_a type
        ("multiply", 10.0, "invalid", 1, True),  # Invalid operand_b type
        ("divide", 10.0, 5.0, "invalid", True),  # Invalid user_id type
    ],
    ids=[
        "valid_calculation",
        "invalid_operation",
        "invalid_operand_a_type",
        "invalid_operand_b_type",
        "invalid_user_id_type",
    ]
)
def test_calculation_create_validation(operation, operand_a, operand_b, user_id, should_raise):
    """
    Test CalculationCreate schema validation for operation, operands, and user_id.
    """
    data = {"operation": operation, "operand_a": operand_a, "operand_b": operand_b, "user_id": user_id}
    if should_raise:
        with pytest.raises(ValidationError) as exc_info:
            CalculationCreate(**data)
        assert exc_info.type is ValidationError
    else:
        calc = CalculationCreate(**data)
        assert calc.operation == operation
        assert calc.operand_a == operand_a
        assert calc.operand_b == operand_b
        assert calc.user_id == user_id
