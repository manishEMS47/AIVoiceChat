Seamless and real-time voice interaction with AI.  

> **Hint:** *Anybody interested in state-of-the-art voice solutions please also <strong>have a look at [Linguflex](https://github.com/KoljaB/Linguflex)</strong>. It lets you control your environment by speaking and is one of the most capable and sophisticated open-source assistants currently available.*

Uses faster_whisper and elevenlabs input streaming for low latency responses to spoken input.

**[🎥 Watch a Demo Video](https://www.youtube.com/watch?v=lq_Q6y47iUU)** 
> **Note**: The demo is conducted on a 10Mbit/s connection, so actual performance might be more impressive on faster connections.

`voice_talk_vad.py` - automatically detects speech  

`voice_talk.py` - toggle recording on/off with the spacebar

## 🛠 Setup:

### 1. API Keys:

Set your keys as environment variables (recommended) or replace the placeholders in `tts_providers.py`:

```bash
# OpenAI (used by both scripts)
setx OPENAI_API_KEY "sk-..."

# ElevenLabs (default TTS backend)
setx ELEVENLABS_API_KEY "..."

# 60db (alternative TTS backend)
setx SIXTYDB_API_KEY "..."
```

### 2. Dependencies:

Install the required Python libraries:
```bash
pip install -r requirements.txt
```
(or `pip install openai elevenlabs pyaudio wave keyboard faster_whisper numpy torch websocket-client requests`)

### 3. Choose a TTS backend (ElevenLabs or 60db):

Text-to-speech is provider-switchable via `TTS_PROVIDER` (default: `elevenlabs`). Both
backends stream the GPT reply into the synthesizer token-by-token, so audio starts
before the full reply is generated — behavior is consistent across providers.

```bash
setx TTS_PROVIDER "elevenlabs"   # ElevenLabs (voice via ELEVENLABS_VOICE, default "Nicole")
setx TTS_PROVIDER "60db"         # 60db WebSocket TTS (voice via SIXTYDB_VOICE_ID)
```

To find your 60db `voice_id` values:
```bash
python list_60db_voices.py
```

All backend settings (voice, model, speed, stability, similarity, sample rate) can be
configured at the top of `tts_providers.py` or via the matching environment variables.

### 4. Run the Script:

Execute the main script based on your mode preference:

```bash
python voice_talk_vad.py
```
or
```bash
python voice_talk.py
```
## 🎙 How to Use:

### For `voice_talk_vad.py`:

Talk into your microphone.  
Listen to the reply.

### For `voice_talk.py`:

1. Press the **space bar** to initiate talk.
2. Speak your heart out.
3. Hit the **space bar** again once you're done.
4. Listen to reply.

## 🤝 Contribute

Feel free to fork, improve, and submit pull requests. If you're considering significant changes or additions, please start by opening an issue.

## 💖 Acknowledgements

Huge shoutout to:
- The hardworking developers behind [faster_whisper](https://github.com/guillaumekln/faster-whisper).
- [ElevenLabs](https://www.elevenlabs.io/) for their cutting-edge voice API.
- [OpenAI](https://www.openai.com/) for pioneering with the GPT-4 model.
