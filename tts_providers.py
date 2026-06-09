"""
tts_providers.py - switchable text-to-speech backends for the voice chat loop.

Exposes a single entry point, `speak(text_chunks)`, that consumes an iterator of
text chunks (e.g. the streaming GPT generator in voice_talk*.py) and plays the
synthesized speech in real time. The active backend is chosen by TTS_PROVIDER.

Both backends do *input streaming*: text is fed to the synthesizer as the LLM
produces it, so audio starts before the full reply is generated. This keeps the
two providers behaviorally consistent.

    from tts_providers import speak
    speak(my_text_generator)

Configuration is read from environment variables, falling back to the inline
placeholders below. Replace the placeholders or set the env vars.
"""

import os
import json
import base64
import threading
import uuid

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Which engine speaks: "elevenlabs" or "60db".
TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "elevenlabs").lower()

# --- ElevenLabs ---
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "your_elevenlabs_key")
ELEVENLABS_VOICE   = os.environ.get("ELEVENLABS_VOICE", "Nicole")
ELEVENLABS_MODEL   = os.environ.get("ELEVENLABS_MODEL", "eleven_monolingual_v1")

# --- 60db (WebSocket TTS) ---
SIXTYDB_API_KEY     = os.environ.get("SIXTYDB_API_KEY", "your_60db_key")
SIXTYDB_WS_URL      = os.environ.get("SIXTYDB_WS_URL", "wss://api.60db.ai/ws/tts")
# Default voice from the 60db docs; list yours via GET https://api.60db.ai/myvoices
SIXTYDB_VOICE_ID    = os.environ.get("SIXTYDB_VOICE_ID", "fbb75ed2-975a-40c7-9e06-38e30524a9a1")
SIXTYDB_SAMPLE_RATE = int(os.environ.get("SIXTYDB_SAMPLE_RATE", "24000"))   # 8000/16000/24000/48000
SIXTYDB_SPEED       = float(os.environ.get("SIXTYDB_SPEED", "1.0"))         # 0.5 - 2.0
SIXTYDB_STABILITY   = int(os.environ.get("SIXTYDB_STABILITY", "50"))        # 0 - 100
SIXTYDB_SIMILARITY  = int(os.environ.get("SIXTYDB_SIMILARITY", "75"))       # 0 - 100


# ---------------------------------------------------------------------------
# ElevenLabs backend
# ---------------------------------------------------------------------------
_elevenlabs_client = None


def _speak_elevenlabs(text_chunks):
    """Stream `text_chunks` through ElevenLabs and play the audio (input streaming)."""
    global _elevenlabs_client
    from elevenlabs.client import ElevenLabs
    from elevenlabs import stream

    if _elevenlabs_client is None:
        _elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    stream(_elevenlabs_client.generate(
        text=text_chunks,
        voice=ELEVENLABS_VOICE,
        model=ELEVENLABS_MODEL,
        stream=True,
    ))


# ---------------------------------------------------------------------------
# 60db backend (WebSocket input streaming -> LINEAR16 PCM playback)
# ---------------------------------------------------------------------------
def _speak_60db(text_chunks):
    """Stream `text_chunks` to the 60db WebSocket TTS API and play the audio.

    Protocol: create_context -> send_text (one per LLM chunk) -> flush_context.
    A receiver thread decodes the base64 `audio_chunk` messages and writes the
    raw PCM straight to the speakers, so there is no mpv/ffmpeg dependency.
    """
    import websocket  # pip install websocket-client
    import pyaudio

    ws = websocket.create_connection(f"{SIXTYDB_WS_URL}?apiKey={SIXTYDB_API_KEY}")
    context_id = str(uuid.uuid4())

    # 1) Open a synthesis context and wait until the server confirms it.
    ws.send(json.dumps({"create_context": {
        "context_id": context_id,
        "voice_id": SIXTYDB_VOICE_ID,
        "audio_config": {
            "audio_encoding": "LINEAR16",
            "sample_rate_hertz": SIXTYDB_SAMPLE_RATE,
        },
        "speed": SIXTYDB_SPEED,
        "stability": SIXTYDB_STABILITY,
        "similarity": SIXTYDB_SIMILARITY,
    }}))

    while True:
        msg = json.loads(ws.recv())
        if "context_created" in msg and msg["context_created"]["context_id"] == context_id:
            break
        if "error" in msg:
            ws.close()
            raise RuntimeError(f"60db: {msg['error'].get('message')}")
        # ignore connection_established / unrelated messages during handshake

    # 2) Audio output stream + a receiver thread that plays chunks as they land.
    pa = pyaudio.PyAudio()
    out = pa.open(format=pyaudio.paInt16, channels=1, rate=SIXTYDB_SAMPLE_RATE, output=True)

    def receive():
        while True:
            try:
                msg = json.loads(ws.recv())
            except Exception:
                break
            if "audio_chunk" in msg:
                out.write(base64.b64decode(msg["audio_chunk"]["audioContent"]))
            elif "flush_completed" in msg:
                break
            elif "error" in msg:
                print(f"\n[60db error] {msg['error'].get('message')}", flush=True)
                break

    rx = threading.Thread(target=receive, daemon=True)
    rx.start()

    # 3) Feed the LLM text in as it streams, then flush to finish synthesis.
    for chunk in text_chunks:
        ws.send(json.dumps({"send_text": {"context_id": context_id, "text": chunk}}))
    ws.send(json.dumps({"flush_context": {"context_id": context_id}}))

    rx.join()

    # 4) Tear down.
    try:
        ws.send(json.dumps({"close_context": {"context_id": context_id}}))
    finally:
        ws.close()
        out.stop_stream()
        out.close()
        pa.terminate()


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
_BACKENDS = {
    "elevenlabs": _speak_elevenlabs,
    "60db": _speak_60db,
}


def speak(text_chunks):
    """Synthesize and play `text_chunks` (a string iterator) using TTS_PROVIDER."""
    try:
        backend = _BACKENDS[TTS_PROVIDER]
    except KeyError:
        raise ValueError(
            f"Unknown TTS_PROVIDER {TTS_PROVIDER!r}; expected one of {list(_BACKENDS)}"
        )
    backend(text_chunks)
