from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create the SQLite database file locally
SQLALCHEMY_DATABASE_URL = "sqlite:///./inventory.db"

# check_same_thread=False is required for SQLite in FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency generator to open and close DB connections per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()