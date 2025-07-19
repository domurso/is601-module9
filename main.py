from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from fastapi.exceptions import RequestValidationError
from app.operations import add, subtract, multiply, divide
from app.models import User, UserCreate, UserRead, Calculation, CalculationCreate, CalculationRead, hash_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
import logging
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Setup templates directory
templates = Jinja2Templates(directory="templates")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/fastapi_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
User.metadata.create_all(bind=engine)
Calculation.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for calculator operations
class OperationRequest(BaseModel):
    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")
    user_id: int | None = Field(None, description="ID of the user performing the calculation")

    @classmethod
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

# Healthcheck endpoint
@app.get("/health")
async def health():
    """
    Healthcheck endpoint for Docker HEALTHCHECK.
    Returns a simple status to indicate the application is running.
    """
    return {"status": "healthy"}

# Calculator routes
@app.get("/")
async def read_root(request: Request):
    """
    Serve the index.html template.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/add", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def add_route(operation: OperationRequest, db: Session = Depends(get_db)):
    """
    Add two numbers and optionally store the calculation.
    """
    try:
        result = add(operation.a, operation.b)
        if operation.user_id:
            user = db.query(User).filter(User.id == operation.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            calc = Calculation(
                operation="add",
                operand_a=operation.a,
                operand_b=operation.b,
                result=result,
                user_id=operation.user_id
            )
            db.add(calc)
            db.commit()
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Add Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/subtract", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def subtract_route(operation: OperationRequest, db: Session = Depends(get_db)):
    """
    Subtract two numbers and optionally store the calculation.
    """
    try:
        result = subtract(operation.a, operation.b)
        if operation.user_id:
            user = db.query(User).filter(User.id == operation.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            calc = Calculation(
                operation="subtract",
                operand_a=operation.a,
                operand_b=operation.b,
                result=result,
                user_id=operation.user_id
            )
            db.add(calc)
            db.commit()
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Subtract Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/multiply", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def multiply_route(operation: OperationRequest, db: Session = Depends(get_db)):
    """
    Multiply two numbers and optionally store the calculation.
    """
    try:
        result = multiply(operation.a, operation.b)
        if operation.user_id:
            user = db.query(User).filter(User.id == operation.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            calc = Calculation(
                operation="multiply",
                operand_a=operation.a,
                operand_b=operation.b,
                result=result,
                user_id=operation.user_id
            )
            db.add(calc)
            db.commit()
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Multiply Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/divide", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def divide_route(operation: OperationRequest, db: Session = Depends(get_db)):
    """
    Divide two numbers and optionally store the calculation.
    """
    try:
        result = divide(operation.a, operation.b)
        if operation.user_id:
            user = db.query(User).filter(User.id == operation.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            calc = Calculation(
                operation="divide",
                operand_a=operation.a,
                operand_b=operation.b,
                result=result,
                user_id=operation.user_id
            )
            db.add(calc)
            db.commit()
        return OperationResponse(result=result)
    except ValueError as e:
        logger.error(f"Divide Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Divide Operation Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# User routes
@app.post("/users", response_model=UserRead, responses={400: {"model": ErrorResponse}})
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user with hashed password.
    """
    try:
        if db.query(User).filter(User.username == user.username).first():
            raise HTTPException(status_code=400, detail="Username already exists")
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email already exists")
        
        hashed_password = hash_password(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            password_hash=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return UserRead.from_orm(db_user)
    except Exception as e:
        logger.error(f"Create User Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}", response_model=UserRead, responses={404: {"model": ErrorResponse}})
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a user by ID.
    """
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserRead.from_orm(db_user)
    except Exception as e:
        logger.error(f"Get User Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Calculation routes
@app.post("/calculations", response_model=CalculationRead, responses={400: {"model": ErrorResponse}})
async def create_calculation(calc: CalculationCreate, db: Session = Depends(get_db)):
    """
    Create a new calculation record.
    """
    try:
        user = db.query(User).filter(User.id == calc.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        operation_funcs = {
            "add": add,
            "subtract": subtract,
            "multiply": multiply,
            "divide": divide
        }
        result = operation_funcs[calc.operation](calc.operand_a, calc.operand_b)
        
        db_calc = Calculation(
            operation=calc.operation,
            operand_a=calc.operand_a,
            operand_b=calc.operand_b,
            result=result,
            user_id=calc.user_id
        )
        db.add(db_calc)
        db.commit()
        db.refresh(db_calc)
        return CalculationRead.from_orm(db_calc)
    except Exception as e:
        logger.error(f"Create Calculation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/calculations/{calc_id}", response_model=CalculationRead, responses={404: {"model": ErrorResponse}})
async def get_calculation(calc_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a calculation by ID.
    """
    try:
        db_calc = db.query(Calculation).filter(Calculation.id == calc_id).first()
        if not db_calc:
            raise HTTPException(status_code=404, detail="Calculation not found")
        return CalculationRead.from_orm(db_calc)
    except Exception as e:
        logger.error(f"Get Calculation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}/calculations", response_model=list[CalculationRead], responses={404: {"model": ErrorResponse}})
async def get_user_calculations(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all calculations for a specific user.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        calculations = db.query(Calculation).filter(Calculation.user_id == user_id).all()
        return [CalculationRead.from_orm(calc) for calc in calculations]
    except Exception as e:
        logger.error(f"Get User Calculations Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
