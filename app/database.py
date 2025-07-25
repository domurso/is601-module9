import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DB_HOST = os.getenv("DB_HOST", "db")
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql://postgres:postgres@{DB_HOST}:5432/fastapi_db")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
