import pytest
from fastapi.testclient import TestClient
from main import app
from app.models import Base, User, Calculation
from app.schemas import UserCreate
from app.security import hash_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import get_db

@pytest.fixture
def test_db():
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/fastapi_db")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture
def test_user(test_db):
    user = User(username="testuser", email="test@example.com", password_hash=hash_password("password123"))
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

# User endpoint tests
def test_create_user(client):
    """
    Test the User Creation API Endpoint.
    """
    response = client.post(
        "/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "password_hash" not in data

def test_create_user_duplicate_username(client, test_db):
    """
    Test the User Creation API Endpoint with duplicate username.
    """
    user = User(username="duplicate", email="user1@example.com", password_hash=hash_password("password123"))
    test_db.add(user)
    test_db.commit()
    response = client.post(
        "/users/",
        json={"username": "duplicate", "email": "user2@example.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

def test_read_users(client, test_db, test_user):
    """
    Test the User List API Endpoint.
    """
    response = client.get("/users/")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert any(user["username"] == "testuser" for user in response.json())

# Calculation endpoint tests
def test_create_calculation(client, test_db, test_user):
    """
    Test the Calculation Creation API Endpoint.
    """
    response = client.post(
        "/calculations/",
        json={"operation": "add", "operand_a": 5, "operand_b": 3},
        headers={"user-id": str(test_user.id)}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["operation"] == "add"
    assert data["operand_a"] == 5
    assert data["operand_b"] == 3
    assert data["result"] == 8
    assert data["user_id"] == test_user.id

def test_create_calculation_invalid_user(client):
    """
    Test the Calculation Creation API Endpoint with invalid user.
    """
    response = client.post(
        "/calculations/",
        json={"operation": "add", "operand_a": 5, "operand_b": 3},
        headers={"user-id": "999"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_read_calculations(client, test_db, test_user):
    """
    Test the Calculation List API Endpoint.
    """
    calc = Calculation(operation="add", operand_a=5, operand_b=3, result=8, user_id=test_user.id)
    test_db.add(calc)
    test_db.commit()
    response = client.get("/calculations/", headers={"user-id": str(test_user.id)})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["operation"] == "add"

# Arithmetic endpoint tests
def test_add_api(client, test_user):
    """
    Test the Addition API Endpoint.
    """
    response = client.post("/add", json={"a": 10, "b": 5}, headers={"user-id": str(test_user.id)})
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert response.json()["result"] == 15, f"Expected result 15, got {response.json()['result']}"

def test_subtract_api(client, test_user):
    """
    Test the Subtraction API Endpoint.
    """
    response = client.post("/subtract", json={"a": 10, "b": 5}, headers={"user-id": str(test_user.id)})
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert response.json()["result"] == 5, f"Expected result 5, got {response.json()['result']}"

def test_multiply_api(client, test_user):
    """
    Test the Multiplication API Endpoint.
    """
    response = client.post("/multiply", json={"a": 10, "b": 5}, headers={"user-id": str(test_user.id)})
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert response.json()["result"] == 50, f"Expected result 50, got {response.json()['result']}"

def test_divide_api(client, test_user):
    """
    Test the Division API Endpoint.
    """
    response = client.post("/divide", json={"a": 10, "b": 2}, headers={"user-id": str(test_user.id)})
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert response.json()["result"] == 5, f"Expected result 5, got {response.json()['result']}"

def test_divide_by_zero_api(client, test_user):
    """
    Test the Division by Zero API Endpoint.
    """
    response = client.post("/divide", json={"a": 10, "b": 0}, headers={"user-id": str(test_user.id)})
    assert response.status_code == 400, f"Expected status code 400, got {response.status_code}"
    assert "error" in response.json(), "Response JSON does not contain 'error' field"
    assert "Cannot divide by zero!" in response.json()["error"], \
        f"Expected error message 'Cannot divide by zero!', got '{response.json()['error']}'"

# Health check test
def test_health_check(client):
    """
    Test the Health Check API Endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
