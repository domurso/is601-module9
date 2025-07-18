import subprocess
import time
import pytest
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User
from app.security import hash_password
from main import app

@pytest.fixture(scope="session")
def fastapi_server():
    """
    Fixture to start the FastAPI server using Docker Compose before E2E tests.
    """
    print("Starting Docker Compose services...")
    subprocess.run(['docker-compose', 'up', '-d'], check=True)
    
    server_url = 'http://localhost:8000/'
    timeout = 30
    start_time = time.time()
    server_up = False
    
    with TestClient(app) as client:
        while time.time() - start_time < timeout:
            try:
                response = client.get('/')
                if response.status_code == 200:
                    server_up = True
                    print("FastAPI server is up and running.")
                    break
            except Exception:
                pass
            time.sleep(1)
    
    if not server_up:
        subprocess.run(['docker-compose', 'down'], check=True)
        raise RuntimeError("FastAPI server failed to start within timeout period.")
    
    yield
    
    print("Shutting down Docker Compose services...")
    subprocess.run(['docker-compose', 'down'], check=True)

@pytest.fixture(scope="session")
def test_db():
    """
    Fixture to set up a test database.
    """
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/fastapi_db")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def test_user(test_db):
    """
    Fixture to create a test user.
    """
    user = User(username="testuser", email="test@example.com", password_hash=hash_password("password123"))
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture(scope="session")
def playwright_instance_fixture():
    """
    Fixture to manage Playwright's lifecycle.
    """
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright_instance_fixture):
    """
    Fixture to launch a browser instance.
    """
    browser = playwright_instance_fixture.chromium.launch(headless=True)
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def page(browser):
    """
    Fixture to create a new page for each test.
    """
    page = browser.new_page()
    yield page
    page.close()
