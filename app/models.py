from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, Field, validator
import bcrypt
from typing import Optional

# SQLAlchemy setup
Base = declarative_base()

class User(Base):
    """
    SQLAlchemy model for the users table.
    Defines columns for id, username, email, password_hash, and created_at.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    calculations = relationship("Calculation", back_populates="user", cascade="all, delete")

class Calculation(Base):
    """
    SQLAlchemy model for the calculations table.
    Defines columns for id, operation, operand_a, operand_b, result, timestamp, and user_id.
    """
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    operation = Column(String(20), nullable=False)
    operand_a = Column(Float, nullable=False)
    operand_b = Column(Float, nullable=False)
    result = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="calculations")

# Pydantic schemas for User
class UserCreate(BaseModel):
    """
    Pydantic schema for creating a new user.
    Includes username, email, and password (plain text, to be hashed).
    """
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")

    @validator("username")
    def validate_username(cls, value):
        if not value.isalnum():
            raise ValueError("Username must be alphanumeric")
        return value

class UserRead(BaseModel):
    """
    Pydantic schema for reading user data.
    Omits password_hash for security.
    """
    id: int
    username: str
    email: EmailStr
    created_at: str

    class Config:
        orm_mode = True

# Pydantic schemas for Calculation
class CalculationCreate(BaseModel):
    """
    Pydantic schema for creating a new calculation.
    Includes operation, operand_a, operand_b, and user_id.
    """
    operation: str = Field(..., max_length=20, description="Operation type (add, subtract, multiply, divide)")
    operand_a: float = Field(..., description="First operand")
    operand_b: float = Field(..., description="Second operand")
    user_id: int = Field(..., description="ID of the user performing the calculation")

    @validator("operation")
    def validate_operation(cls, value):
        valid_operations = ["add", "subtract", "multiply", "divide"]
        if value not in valid_operations:
            raise ValueError(f"Operation must be one of {valid_operations}")
        return value

class CalculationRead(BaseModel):
    """
    Pydantic schema for reading calculation data.
    Includes all fields for display.
    """
    id: int
    operation: str
    operand_a: float
    operand_b: float
    result: float
    timestamp: str
    user_id: int

    class Config:
        orm_mode = True

# Password hashing and verification functions
def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    
    Args:
        password: Plain-text password to hash.
    Returns:
        Hashed password as a string.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if a plain-text password matches the stored hashed password.
    
    Args:
        plain_password: Plain-text password to verify.
        hashed_password: Stored hashed password.
    Returns:
        True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
