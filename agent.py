from pathlib import Path
from dotenv import load_dotenv
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent as VoiceAgent, AgentSession
from livekit.plugins import silero, openai
import datetime
import os

from app.database.helpers import (
    init_database,
    setup_database_session,
    update_session_room,
    save_transcript
)

load_dotenv()

init_database()

class TranscriptionAgent(VoiceAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

async def entrypoint(ctx: JobContext):
    await ctx.connect()
    agent_session = AgentSession()

    setup_database_session()

    if ctx and hasattr(ctx, 'room') and ctx.room:
        update_session_room(ctx.room)

    @agent_session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            save_transcript(
                text=transcript.transcript,
                confidence=None,
                is_final=True,
                duration_ms= None
            )

    my_agent = TranscriptionAgent(
        instructions="You are a helpful assistant that transcribes user speech to text.",
        stt=openai.STT(
            base_url="http://localhost:5002/v1",
            model="Systran/faster-whisper-small"
        ),
        vad=silero.VAD.load()
    )

    await agent_session.start(
        agent=my_agent,
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
