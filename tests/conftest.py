import subprocess
import time
import pytest
import os
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
    os.environ["DB_HOST"] = "localhost"
    print("Starting Docker Compose services...")
    subprocess.run(['docker-compose', 'up', '-d'], check=True)
    
    # Wait for database to be ready
    timeout = 30
    start_time = time.time()
    db_ready = False
    
    while time.time() - start_time < timeout:
        try:
            engine = create_engine("postgresql://postgres:postgres@localhost:5432/fastapi_db")
            Base.metadata.create_all(bind=engine)
            db_ready = True
            print("Database is ready.")
            break
        except Exception:
            time.sleep(1)
    
    if not db_ready:
        subprocess.run(['docker-compose', 'down'], check=True)
        raise RuntimeError("Database failed to start within timeout period.")
    
    # Wait for FastAPI server
    server_url = 'http://localhost:8000/'
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
    os.environ["DB_HOST"] = "localhost"
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/fastapi_db")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind
