from fastapi import FastAPI, Depends, HTTPException, Request, status, Header
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from app.database import SessionLocal, Base, engine
from app.models import User, Calculation
from app.schemas import UserCreate, UserRead, CalculationCreate, CalculationRead
from app.security import hash_password
from app.operations import add, subtract, multiply, divide
from typing import List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Setup templates directory
templates = Jinja2Templates(directory="templates")

# Create database tables
Base.metadata.create_all(bind=engine)

# Pydantic model for arithmetic operations (for compatibility with existing endpoints)
class OperationRequest(BaseModel):
    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")

    @field_validator('a', 'b')
    def validate_numbers(cls, value):
        if not isinstance(value, (int, float)):
            raise ValueError('Both a and b must be numbers.')
        return value

class OperationResponse(BaseModel):
    result: float = Field(..., description="The result of the operation")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")

# Custom Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()])
    logger.error(f"ValidationError on {request.url.path}: {error_messages}")
    return JSONResponse(
        status_code=400,
        content={"error": error_messages},
    )

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Root endpoint
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# User management endpoints
@app.post("/users/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[UserRead])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.get("/users/{user_id}", response_model=UserRead)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Calculation endpoints
@app.post("/calculations/", response_model=CalculationRead, status_code=status.HTTP_201_CREATED)
def create_calculation(calculation: CalculationCreate, user_id: int = Header(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if calculation.operation == "add":
        result = add(calculation.operand_a, calculation.operand_b)
    elif calculation.operation == "subtract":
        result = subtract(calculation.operand_a, calculation.operand_b)
    elif calculation.operation == "multiply":
        result = multiply(calculation.operand_a, calculation.operand_b)
    elif calculation.operation == "divide":
        try:
            result = divide(calculation.operand_a, calculation.operand_b)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Invalid operation")
    
    db_calc = Calculation(
        operation=calculation.operation,
        operand_a=calculation.operand_a,
        operand_b=calculation.operand_b,
        result=result,
        user_id=user_id
    )
    db.add(db_calc)
    db.commit()
    db.refresh(db_calc)
    return db_calc

@app.get("/calculations/", response_model=List[CalculationRead])
def read_calculations(user_id: int = Header(...), skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    calculations = db.query(Calculation).filter(Calculation.user_id == user_id).offset(skip).limit(limit).all()
    return calculations

# Arithmetic endpoints (maintained for compatibility)
@app.post("/add", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def add_route(operation: OperationRequest, user_id: int = Header(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        result = add(operation.a, operation.b)
        db_calc = Calculation(
            operation="add",
            operand_a=operation.a,
            operand_b=operation.b,
            result=result,
            user_id=user_id
        )
        db.add(db_calc)
        db.commit()
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Add Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/subtract", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def subtract_route(operation: OperationRequest, user_id: int = Header(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        result = subtract(operation.a, operation.b)
        db_calc = Calculation(
            operation="subtract",
            operand_a=operation.a,
            operand_b=operation.b,
            result=result,
            user_id=user_id
        )
        db.add(db_calc)
        db.commit()
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Subtract Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/multiply", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def multiply_route(operation: OperationRequest, user_id: int = Header(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        result = multiply(operation.a, operation.b)
        db_calc = Calculation(
            operation="multiply",
            operand_a=operation.a,
            operand_b=operation.b,
            result=result,
            user_id=user_id
        )
        db.add(db_calc)
        db.commit()
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Multiply Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/divide", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def divide_route(operation: OperationRequest, user_id: int = Header(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        result = divide(operation.a, operation.b)
        db_calc = Calculation(
            operation="divide",
            operand_a=operation.a,
            operand_b=operation.b,
            result=result,
            user_id=user_id
        )
        db.add(db_calc)
        db.commit()
        return OperationResponse(result=result)
    except ValueError as e:
        logger.error(f"Divide Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Divide Operation Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
