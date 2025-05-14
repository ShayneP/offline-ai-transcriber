from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.sqlite import JSON
import uuid

from . import Base

class User(Base):
    """User model for transcript sources"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="user")
    transcripts = relationship("Transcript", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"

class Session(Base):
    """Session model for grouping transcripts"""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    session_metadata = Column(JSON, nullable=True)

    user = relationship("User", back_populates="sessions")
    transcripts = relationship("Transcript", back_populates="session")

    def __repr__(self):
        return f"<Session {self.id} - {self.title}>"

class Transcript(Base):
    """Transcript model for storing voice transcriptions"""
    __tablename__ = "transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    is_final = Column(Boolean, default=True)
    language = Column(String(10), default="en-US")
    duration_ms = Column(Integer, nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    transcript_metadata = Column(JSON, nullable=True)

    session = relationship("Session", back_populates="transcripts")
    user = relationship("User", back_populates="transcripts")

    __table_args__ = (
        Index('idx_transcript_user_session', user_id, session_id),
        Index('idx_transcript_session_time', session_id, start_time),
        Index('idx_transcript_created_at', created_at),
    )

    def __repr__(self):
        return f"<Transcript {self.id[:8]} - {self.text[:30]}...>"
