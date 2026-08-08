import asyncio
import os
import tempfile
from pathlib import Path
import edge_tts

TTS_CACHE_DIR = Path.home() / "tmp" / "pixel_tts"

class EdgeTTS:
    def __init__(self):
        TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    async def generate_speech(self, text, voice="zh-CN-XiaoxiaoNeural", rate="+0%", volume="+0%", pitch="+0Hz"):
        if not text.strip():
            return None

        # Clean text
        text = text.replace("\n", " ").strip()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir=str(TTS_CACHE_DIR))
        temp_file.close()

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch
        )
        await communicate.save(temp_file.name)
        return temp_file.name
