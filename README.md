FastAPI Calculator Application

This is a FastAPI-based web application that provides a simple calculator with arithmetic operations (addition, subtraction, multiplication, division) and user management with calculation history stored in a PostgreSQL database. The application includes a frontend interface, unit tests, integration tests, and aend-to-end (E2E) tests using Playwright. It is containerized using Docker and Docker Compose for easy setup and deployment.

Features





Calculator API: Perform arithmetic operations via endpoints (/add, /subtract, /multiply, /divide).



User Management: Create and retrieve users with unique usernames and emails, with password hashing using bcrypt.



Calculation History: Store and retrieve user calculations in a PostgreSQL database.



Frontend: A simple web interface (index.html) for performing calculations.



Testing: Comprehensive unit, integration, and E2E tests using pytest, pytest-cov, and Playwright.



Dockerized Setup: Runs with Docker Compose, including FastAPI, PostgreSQL, and pgAdmin.

Prerequisites





Docker: Install Docker and Docker Compose to run the application in containers.



Git: To clone the repository (optional).



Python 3.10 (optional): For running tests locally without Docker.



curl or Postman (optional): For testing API endpoints.

Project Structure

module9/
├── app/
│   ├── operations.py         # Core arithmetic functions
│   └── models.py            # SQLAlchemy models and Pydantic schemas
├── templates/
│   └── index.html           # Frontend interface
├── tests/
│   ├── e2e/
│   │   ├── conftest.py      # Pytest fixtures for E2E tests
│   │   └── test_e2e.py      # E2E tests using Playwright
│   ├── integration/
│   │   ├── test_fastapi_calculator.py  # Integration tests for calculator endpoints
│   │   └── test_users_calculations.py  # Integration tests for user and calculation endpoints
│   └── unit/
│       ├── test_calculator.py  # Unit tests for arithmetic functions
│       └── test_models.py      # Unit tests for password hashing and schema validation
├── .coveragerc              # Coverage configuration
├── .github/
│   └── workflows/
│       └── test.yml         # GitHub Actions workflow for tests
├── Dockerfile               # Docker image for the FastAPI app
├── docker-compose.yml       # Docker Compose configuration
├── main.py                  # FastAPI application
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Python dependencies

Setup and Installation





Clone the Repository (if applicable):

git clone <repository-url>
cd module9



Ensure Docker is Running: Verify Docker and Docker Compose are installed:

docker --version
docker-compose --version



Build and Start the Application: Build the Docker images and start the services (FastAPI, PostgreSQL, pgAdmin):

docker-compose up --build





This creates containers: fastapi_calculator (FastAPI app), postgres_db (PostgreSQL), and pgadmin (pgAdmin interface).



The app is available at http://localhost:8000.



pgAdmin is available at http://localhost:5050.



Access the Application:





Frontend: Open http://localhost:8000 in a browser to use the calculator interface.



API: Test endpoints using curl or Postman (see below).



pgAdmin: Log in at http://localhost:5050 (email: admin@example.com, password: admin). Connect to the PostgreSQL server (host: db, port: 5432, user: postgres, password: postgres).

Using the Application

Frontend





Navigate to http://localhost:8000.



Enter two numbers and select an operation (Add, Subtract, Multiply, Divide).



Click the corresponding button to see the result.



Note: The frontend currently doesn’t store calculations in the database. To enable this, update index.html to include a user_id in requests (contact the developer for assistance).

API Endpoints

Use curl or Postman to interact with the API.

Create a User

curl -X POST "http://localhost:8000/users" -H "Content-Type: application/json" -d '{"username":"testuser","email":"test@example.com","password":"securepassword123"}'

Response:

{"id":1,"username":"testuser","email":"test@example.com","created_at":"2025-07-18T23:20:00.123456+00:00"}

Get a User

curl -X GET "http://localhost:8000/users/1"

Create a Calculation

curl -X POST "http://localhost:8000/calculations" -H "Content-Type: application/json" -d '{"operation":"add","operand_a":10,"operand_b":5,"user_id":1}'

Response:

{"id":1,"operation":"add","operand_a":10.0,"operand_b":5.0,"result":15.0,"timestamp":"2025-07-18T23:20:00.123456+00:00","user_id":1}

Get a Calculation

curl -X GET "http://localhost:8000/calculations/1"

Get User Calculations

curl -X GET "http://localhost:8000/users/1/calculations"

Calculator Operations

Perform calculations without storing (compatible with frontend):

curl -X POST "http://localhost:8000/add" -H "Content-Type: application/json" -d '{"a":10,"b":5}'

Response:

{"result":15.0}

Supported endpoints: /add, /subtract, /multiply, /divide. To store calculations, include "user_id":1 in the request body.

Health Check

curl -X GET "http://localhost:8000/health"

Response:

{"status":"healthy"}

Running Tests

The application includes unit, integration, and E2E tests.





Ensure Docker Compose is Running:

cd module9
docker-compose up --build



Run Unit Tests: Test password hashing and schema validation:

docker-compose exec web pytest tests/unit -vv

Tests: test_calculator.py (arithmetic functions), test_models.py (hashing, schemas).



Run Integration Tests: Test API endpoints with PostgreSQL:

docker-compose exec web pytest tests/integration -vv

Tests: test_fastapi_calculator.py (calculator endpoints), test_users_calculations.py (user and calculation endpoints).



Run E2E Tests: Test the frontend using Playwright:

docker-compose exec web pytest tests/e2e/test_e2e.py -vv

Tests: test_hello_world, test_calculator_add, test_calculator_divide_by_zero.



View Coverage Report: Coverage reports are generated in /app/coverage:

docker-compose exec web ls -l /app/coverage
docker cp fastapi_calculator:/app/coverage/html ./coverage

Open module9/coverage/html/index.html in a browser.

Troubleshooting





Tests Fail with PermissionError or Missing Coverage:





Check volume permissions:

docker-compose exec web ls -ld /app/coverage /app/.pytest_cache /home/appuser/.cache/ms-playwright

Ensure ownership by appuser:appgroup with drwxr-xr-x or drwxrwxr-x.



Run tests without coverage:

docker-compose exec web pytest tests/unit -vv --no-cov



Check logs:

docker-compose logs web



Database Connection Issues:





Verify postgres_db is healthy:

docker-compose ps



Ensure DATABASE_URL matches docker-compose.yml (postgresql://postgres:postgres@db:5432/fastapi_db).



Playwright Errors:





Confirm browser binaries:

docker-compose exec web ls -l /home/appuser/.cache/ms-playwright



Rebuild if missing:

docker-compose up --build



Reset Environment:





Stop and remove containers:

cd module9
docker-compose down



Remove volumes:

docker volume rm module9_postgres_data module9_pgadmin_data module9_coverage_data module9_pytest_cache_data module9_playwright_data || true



Remove image:

docker rmi module9_web



Rebuild:

docker-compose up --build

Security Notes





Credentials: The docker-compose.yml uses default credentials (postgres:postgres, admin@example.com:admin). Update these for production:





Edit docker-compose.yml environment variables.



Use environment files or secrets management.



Authentication: The /users and /calculations endpoints lack authentication. Consider adding JWT or session-based authentication for production.

GitHub Actions

The .github/workflows/test.yml runs unit and integration tests with a PostgreSQL container on push or pull requests. Check GitHub Actions logs for results and download coverage reports.

Development Notes





Frontend: To store calculations in the database, update index.html JavaScript to include user_id in API requests.



Additional Features: Contact the developer for adding authentication, more endpoints, or visualizations (e.g., calculation history charts).



Deployment: For production deployment (e.g., AWS, Render), update credentials and remove development settings (e.g., pgadmin service).

Contact

For issues or feature requests, contact the developer or open an issue in the repository.
