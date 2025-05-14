import os
import argparse
from sqlalchemy import create_engine
from . import Base, init_db
from . import models

def create_tables(connection_string=None):
    """Create all database tables defined in the models"""

    if connection_string is None:
        connection_string = os.environ.get(
            "DATABASE_URL",
            "sqlite:///voice_transcripts.db"
        )

    engine, _ = init_db(connection_string)

    Base.metadata.create_all(bind=engine)
    print(f"Tables created successfully on {connection_string}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create database tables for the application")
    parser.add_argument("--connection", type=str, help="Database connection string")
    args = parser.parse_args()

    create_tables(args.connection)
