import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db  # Updated import
from app.models import Base, User, Calculation
import os
import time
import psycopg2

# Fixture to set up a test database
@pytest.fixture(scope="function")
def test_db():
    """
    Set up a temporary PostgreSQL database for testing.
    """
    # Use the same DATABASE_URL as in docker-compose.yml
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/fastapi_db")
    
    # Wait for the database to be ready
    max_attempts = 10
    attempt = 0
    while attempt < max_attempts:
        try:
            conn = psycopg2.connect(
                dbname="fastapi_db",
                user="postgres",
                password="postgres",
                host="db",
                port="5432"
            )
            conn.close()
            break
        except psycopg2.OperationalError:
            attempt += 1
            time.sleep(1)
    else:
        pytest.fail("Could not connect to PostgreSQL after multiple attempts")
    
    engine = create_engine(DATABASE_URL)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Override the get_db dependency to use the test session
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal()
    
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)

# Fixture to provide TestClient
@pytest.fixture(scope="function")
def client(test_db):
    """
    Provide a TestClient for the FastAPI app with the test database.
    """
    return TestClient(app)

# Integration Tests for User Endpoints
def test_create_user(client):
    """
    Test creating a user with valid data.
    """
    response = client.post(
        "/users",
        json={"username": "testuser", "email": "test@example.com", "password": "securepassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data

def test_create_user_duplicate_username(client):
    """
    Test that creating a user with a duplicate username fails.
    """
    # Create first user
    client.post(
        "/users",
        json={"username": "testuser", "email": "test1@example.com", "password": "securepassword123"}
    )
    # Try creating another user with the same username
    response = client.post(
        "/users",
        json={"username": "testuser", "email": "test2@example.com", "password": "securepassword123"}
    )
    assert response.status_code == 400
    assert "Username already exists" in response.json()["error"]

def test_create_user_duplicate_email(client):
    """
    Test that creating a user with a duplicate email fails.
    """
    # Create first user
    client.post(
        "/users",
        json={"username": "testuser1", "email": "test@example.com", "password": "securepassword123"}
    )
    # Try creating another user with the same email
    response = client.post(
        "/users",
        json={"username": "testuser2", "email": "test@example.com", "password": "securepassword123"}
    )
    assert response.status_code == 400
    assert "Email already exists" in response.json()["error"]

def test_create_user_invalid_email(client):
    """
    Test that creating a user with an invalid email fails.
    """
    response = client.post(
        "/users",
        json={"username": "testuser", "email": "invalid-email", "password": "securepassword123"}
    )
    assert response.status_code == 400
    assert "value is not a valid email address" in response.json()["error"]

# Integration Tests for Calculation Endpoints
def test_create_calculation(client, test_db):
    """
    Test creating a calculation for a valid user.
    """
    # Create a user
    user_response = client.post(
        "/users",
        json={"username": "testuser", "email": "test@example.com", "password": "securepassword123"}
    )
    user_id = user_response.json()["id"]
    
    # Create a calculation
    response = client.post(
        "/calculations",
        json={"operation": "add", "operand_a": 10.0, "operand_b": 5.0, "user_id": user_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["operation"] == "add"
    assert data["operand_a"] == 10.0
    assert data["operand_b"] == 5.0
    assert data["result"] == 15.0
    assert data["user_id"] == user_id
    assert "timestamp" in data

def test_create_calculation_invalid_user(client):
    """
    Test that creating a calculation with an invalid user_id fails.
    """
    response = client.post(
        "/calculations",
        json={"operation": "add", "operand_a": 10.0, "operand_b": 5.0, "user_id": 999}
    )
    assert response.status_code == 404
    assert "User not found" in response.json()["error"]

def test_get_user_calculations(client, test_db):
    """
    Test retrieving all calculations for a user.
    """
    # Create a user
    user_response = client.post(
        "/users",
        json={"username": "testuser", "email": "test@example.com", "password": "securepassword123"}
    )
    user_id = user_response.json()["id"]
    
    # Create two calculations
    client.post(
        "/calculations",
        json={"operation": "add", "operand_a": 10.0, "operand_b": 5.0, "user_id": user_id}
    )
    client.post(
        "/calculations",
        json={"operation": "subtract", "operand_a": 10.0, "operand_b": 5.0, "user_id": user_id}
    )
    
    # Retrieve calculations
    response = client.get(f"/users/{user_id}/calculations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["operation"] == "add"
    assert data[0]["result"] == 15.0
    assert data[1]["operation"] == "subtract"
    assert data[1]["result"] == 5.0

def test_get_calculation(client, test_db):
    """
    Test retrieving a single calculation by ID.
    """
    # Create a user
    user_response = client.post(
        "/users",
        json={"username": "testuser", "email": "test@example.com", "password": "securepassword123"}
    )
    user_id = user_response.json()["id"]
    
    # Create a calculation
    calc_response = client.post(
        "/calculations",
        json={"operation": "multiply", "operand_a": 10.0, "operand_b": 5.0, "user_id": user_id}
    )
    calc_id = calc_response.json()["id"]
    
    # Retrieve the calculation
    response = client.get(f"/calculations/{calc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["operation"] == "multiply"
    assert data["result"] == 50.0
    assert data["user_id"] == user_id
