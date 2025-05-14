"""
Database helpers for the voice transcript application
"""
import datetime
import os
from . import init_db, get_db
from .models import User, Session as DBSession, Transcript

_db_initialized = False
_global_session_id = None
_global_user_id = None

def init_database(connection_string=None):
    """Initialize the database connection"""
    if connection_string is None:
        connection_string = os.environ.get(
            "DATABASE_URL",
            "sqlite:///voice_transcripts.db"
        )

    engine, SessionLocal = init_db(connection_string)
    return engine, SessionLocal

def setup_database_session(room_name="console_session"):
    """Initialize database session and user - returns (user_id, session_id)"""
    global _global_user_id, _global_session_id, _db_initialized

    if _db_initialized and _global_session_id and _global_user_id:
        return _global_user_id, _global_session_id

    db = next(get_db())
    try:
        user = db.query(User).filter(User.username == "agent_user").first()
        if not user:
            user = User(
                username="agent_user",
                email="agent@example.com"
            )
            db.add(user)
            db.flush()

        user_id = user.id

        db_session = DBSession(
            user_id=user.id,
            title=f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            session_metadata={"source": "livekit_agent", "room_name": room_name}
        )
        db.add(db_session)
        db.commit()

        _global_user_id = user_id
        _global_session_id = db_session.id
        _db_initialized = True

        print(f"Database initialized. Session ID: {_global_session_id}")
        return user_id, db_session.id

    except Exception as e:
        print(f"Database initialization error: {e}")
        db.rollback()
        return None, None
    finally:
        db.close()

def update_session_room(room_name):
    """Update the room name for the current session"""
    global _global_session_id

    if not _global_session_id:
        return False

    db = next(get_db())
    try:
        db_session = db.query(DBSession).filter(DBSession.id == _global_session_id).first()
        if db_session:
            if db_session.session_metadata is None:
                db_session.session_metadata = {}
            db_session.session_metadata["room_name"] = room_name
            db.commit()
            return True
    except Exception as e:
        print(f"Error updating room name: {e}")
        db.rollback()
    finally:
        db.close()

    return False

def save_transcript(text, confidence=None, is_final=True, duration_ms=None,
                   language="en-US", metadata=None):
    """Save a transcript to the database"""
    global _db_initialized, _global_session_id, _global_user_id

    if not _db_initialized or not _global_session_id or not _global_user_id:
        user_id, session_id = setup_database_session()
        if not session_id:
            print("ERROR: Could not initialize database session for transcript")
            return False

    try:
        db = next(get_db())
        now = datetime.datetime.now()

        if metadata is None:
            metadata = {
                "source": "livekit_agent",
                "type": "user_speech"
            }

        transcript = Transcript(
            session_id=_global_session_id,
            user_id=_global_user_id,
            text=text,
            confidence=confidence,
            is_final=is_final,
            language=language,
            duration_ms=duration_ms,
            start_time=now,
            end_time=now if is_final else None,
            transcript_metadata=metadata
        )
        db.add(transcript)
        db.commit()

        print(f"Saved transcript to database: {text[:30]}{'...' if len(text) > 30 else ''}")
        return True
    except Exception as e:
        print(f"Error saving transcript to database: {e}")
        if db:
            db.rollback()
        return False
    finally:
        if db:
            db.close()

def get_current_session_id():
    """Get the current session ID"""
    return _global_session_id

def get_current_user_id():
    """Get the current user ID"""
    return _global_user_id

def is_database_initialized():
    """Check if the database is initialized"""
    return _db_initialized
