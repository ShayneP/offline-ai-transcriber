from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# Will be set by the app initialization
engine = None
SessionLocal = None

def init_db(connection_string):
    """Initialize the database connection and session factory"""
    global engine, SessionLocal

    engine = create_engine(connection_string)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Import models to ensure they're registered with Base
    from . import models

    return engine, SessionLocal

def get_db():
    """Get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()