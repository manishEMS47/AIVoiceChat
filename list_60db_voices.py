"""
list_60db_voices.py - print the 60db voices available to your account.

Use the printed voice_id values for SIXTYDB_VOICE_ID in tts_providers.py
(or the SIXTYDB_VOICE_ID environment variable).

    python list_60db_voices.py
"""

import os
import requests

API_KEY = os.environ.get("SIXTYDB_API_KEY", "your_60db_key")

resp = requests.get(
    "https://api.60db.ai/myvoices",
    headers={"Authorization": f"Bearer {API_KEY}"},
    timeout=30,
)
resp.raise_for_status()
data = resp.json()

for voice in data.get("data", []):
    labels = voice.get("labels") or {}
    print(f"{voice['voice_id']}  |  {voice['name']}  |  "
          f"{labels.get('language_name', '?')}  |  {voice.get('model', '?')}")
