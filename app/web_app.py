from flask import Flask, render_template, jsonify, request
import datetime
from sqlalchemy import desc, func
from pathlib import Path
import os
from openai import OpenAI # Added import

from app.database.helpers import init_database
from app.database import get_db
from app.database.models import User, Session as DBSession, Transcript

app = Flask(__name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static")
)

init_database()

try:
    client = OpenAI(
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key=os.environ.get("OLLAMA_API_KEY", "ollama"),
    )
except Exception as e:
    print(f"Failed to initialize OpenAI client for Ollama: {e}")
    client = None

@app.route('/')
def index():
    """Main page showing all sessions"""
    db = next(get_db())
    try:
        sessions = db.query(
            DBSession,
            func.count(Transcript.id).label('transcript_count')
        ).outerjoin(
            Transcript, DBSession.id == Transcript.session_id
        ).group_by(
            DBSession.id
        ).order_by(
            desc(DBSession.started_at)
        ).all()

        session_data = []
        for session, count in sessions:
            session_data.append({
                'id': session.id,
                'title': session.title,
                'started_at': session.started_at,
                'ended_at': session.ended_at,
                'transcript_count': count,
                'room_name': session.session_metadata.get('room_name', 'N/A') if session.session_metadata else 'N/A'
            })

        return render_template('index.html', sessions=session_data)
    finally:
        db.close()

@app.route('/session/<uuid:session_id>')
def session_detail(session_id):
    """View details for a single session with all transcripts"""
    db = next(get_db())
    try:
        session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if not session:
            return "Session not found", 404

        transcripts = db.query(Transcript).filter(
            Transcript.session_id == session_id
        ).order_by(
            Transcript.start_time
        ).all()

        transcript_data = []
        for t in transcripts:
            transcript_data.append({
                'id': t.id,
                'text': t.text,
                'confidence': t.confidence,
                'start_time': t.start_time,
                'duration_ms': t.duration_ms,
                'metadata': t.transcript_metadata
            })

        return render_template(
            'session.html',
            session=session,
            transcripts=transcript_data
        )
    finally:
        db.close()

@app.route('/analyze/<uuid:session_id>')
def analyze_session(session_id):
    """Analyze all transcripts for a session"""
    db = next(get_db())
    try:
        session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if not session:
            return "Session not found", 404

        transcripts = db.query(Transcript).filter(
            Transcript.session_id == session_id
        ).order_by(
            Transcript.start_time
        ).all()

        combined_text = "\n".join([t.text for t in transcripts])
        summary = session.summary # Attempt to get existing summary

        if summary:
            print(f"Using cached summary for session {session_id}")
        elif client and combined_text:
            print(f"No cached summary found for session {session_id}. Generating new summary.")
            try:
                ollama_model = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
                print(f"Attempting to summarize with Ollama model: {ollama_model} using base_url: {client.base_url}")

                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that summarizes text concisely.",
                        },
                        {
                            "role": "user",
                            "content": f"Please summarize the following transcript:\n\n{combined_text}",
                        },
                    ],
                    model=ollama_model,
                    temperature=0.3,
                )
                if chat_completion.choices:
                    summary = chat_completion.choices[0].message.content.strip()
                    session.summary = summary # Save the new summary
                    db.commit() # Commit the change to the database
                    print(f"New summary saved for session {session_id}")
                else:
                    summary = "LLM returned no choices for summary."
                    print("LLM returned no choices.")
            except Exception as e:
                print(f"Error during LLM summarization: {e}")
                summary = f"Error generating summary: {str(e)}"
        elif not client:
            summary = "LLM client not initialized. Cannot generate summary."
            print("LLM client not initialized, cannot generate summary.")
        elif not combined_text:
            summary = "No text to summarize."
            print("No text provided for summarization.")

        if summary is None: # Ensure summary is not None if it wasn't generated or cached
            summary = "Summary could not be generated or retrieved."

        analysis_result = {
            "session_id": str(session_id),
            "transcript_count": len(transcripts),
            "total_characters": len(combined_text),
            "summary": summary,
        }

        return render_template(
            'analyze.html',
            session=session,
            combined_text=combined_text,
            analysis=analysis_result
        )
    finally:
        db.close()

@app.route('/api/transcripts/<uuid:session_id>')
def api_transcripts(session_id):
    """API endpoint to get transcripts for a session"""
    db = next(get_db())
    try:
        transcripts = db.query(Transcript).filter(
            Transcript.session_id == session_id
        ).order_by(
            Transcript.start_time
        ).all()

        data = [{
            'id': str(t.id),
            'text': t.text,
            'confidence': t.confidence,
            'start_time': t.start_time.isoformat(),
            'duration_ms': t.duration_ms,
            'metadata': t.transcript_metadata
        } for t in transcripts]

        return jsonify(data)
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
