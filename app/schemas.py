from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Literal

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class CalculationCreate(BaseModel):
    operation: Literal["add", "subtract", "multiply", "divide"] = Field(..., description="The arithmetic operation")
    operand_a: float = Field(..., description="The first operand")
    operand_b: float = Field(..., description="The second operand")

class CalculationRead(BaseModel):
    id: int
    operation: str
    operand_a: float
    operand_b: float
    result: float
    timestamp: datetime
    user_id: int

    class Config:
        from_attributes = True
