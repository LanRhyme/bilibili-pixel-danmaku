import asyncio
import math
import os
import struct
import subprocess
import wave
import threading
from pathlib import Path
from PySide6.QtCore import QObject, Signal

SOUNDS_DIR = Path.home() / "tmp" / "pixel_sounds"

def generate_8bit_wav(filename, freq_list, duration_per_freq=0.08, sample_rate=22050):
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = SOUNDS_DIR / filename
    if filepath.exists():
        return str(filepath)

    num_samples = int(sample_rate * duration_per_freq * len(freq_list))
    wav_file = wave.open(str(filepath), "w")
    wav_file.setnchannels(1)
    wav_file.setsampwidth(1)
    wav_file.setframerate(sample_rate)

    frames = bytearray()
    for freq in freq_list:
        sample_count = int(sample_rate * duration_per_freq)
        for i in range(sample_count):
            if freq == 0:
                val = 128
            else:
                t = i / sample_rate
                val = 200 if (math.sin(2 * math.pi * freq * t) > 0) else 56
            frames.append(val)

    wav_file.writeframes(frames)
    wav_file.close()
    return str(filepath)

class SoundManager(QObject):
    tts_finished_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_playing = False
        self.master_volume = 80

        self.sound_coin = generate_8bit_wav("coin.wav", [987.77, 1318.51], 0.08)
        self.sound_alert = generate_8bit_wav("alert.wav", [523.25, 659.25, 783.99, 1046.50], 0.06)
        self.sound_levelup = generate_8bit_wav("levelup.wav", [440, 554.37, 659.25, 880], 0.07)

    def set_master_volume(self, volume_pct):
        self.master_volume = max(0, min(100, volume_pct))

    def play_sfx(self, sound_name):
        sound_path = None
        if sound_name == "coin":
            sound_path = self.sound_coin
        elif sound_name == "alert":
            sound_path = self.sound_alert
        elif sound_name == "levelup":
            sound_path = self.sound_levelup

        if sound_path and os.path.exists(sound_path):
            try:
                vol = str(int(65536 * (self.master_volume / 100.0)))
                subprocess.Popen(["paplay", "--volume=" + vol, sound_path], stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def play_tts_file(self, file_path):
        if file_path and os.path.exists(file_path):
            self.is_playing = True
            def _play():
                try:
                    vol = str(self.master_volume)
                    subprocess.run(["mpv", "--no-terminal", f"--volume={vol}", file_path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                except Exception:
                    pass
                finally:
                    self.is_playing = False
                    self.tts_finished_signal.emit()
            
            threading.Thread(target=_play, daemon=True).start()
