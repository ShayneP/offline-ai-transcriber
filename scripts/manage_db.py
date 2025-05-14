#!/usr/bin/env python
"""
Database management script for voice transcript application
"""
import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, init_db
from app.database import models
from app.database.create_tables import create_tables

def reset_database(connection_string):
    """Drop all tables and recreate them"""
    print(f"Connecting to database: {connection_string}")
    engine, _ = init_db(connection_string)

    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)

    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)

    print("Database reset successfully!")

def seed_database(connection_string):
    """Seed the database with sample data"""
    from sqlalchemy.orm import Session
    from datetime import datetime
    import uuid

    print(f"Connecting to database: {connection_string}")
    engine, SessionLocal = init_db(connection_string)

    with SessionLocal() as session:
        user = models.User(
            username="test_user",
            email="test@example.com"
        )
        session.add(user)
        session.flush()

        transcript_session = models.Session(
            user_id=user.id,
            title="Sample Voice Session",
            started_at=datetime.utcnow(),
            session_metadata={"device": "iPhone", "app_version": "1.0.0"}
        )
        session.add(transcript_session)
        session.flush()

        transcript = models.Transcript(
            session_id=transcript_session.id,
            user_id=user.id,
            text="This is a sample voice transcript.",
            confidence=0.95,
            is_final=True,
            language="en-US",
            duration_ms=3500,
            start_time=datetime.utcnow(),
            transcript_metadata={"speaker": "user", "sentiment": "neutral"}
        )
        session.add(transcript)

        session.commit()

    print("Database seeded successfully!")

def main():
    parser = argparse.ArgumentParser(description="Manage the voice transcript database")
    parser.add_argument(
        "--connection",
        type=str,
        default=os.environ.get(
            "DATABASE_URL",
            "sqlite:///voice_transcripts.db"
        ),
        help="Database connection string"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    create_parser = subparsers.add_parser("create", help="Create all database tables")
    reset_parser = subparsers.add_parser("reset", help="Drop and recreate all tables")
    seed_parser = subparsers.add_parser("seed", help="Seed the database with sample data")

    args = parser.parse_args()

    if args.command == "create":
        create_tables(args.connection)
    elif args.command == "reset":
        reset_database(args.connection)
    elif args.command == "seed":
        seed_database(args.connection)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
