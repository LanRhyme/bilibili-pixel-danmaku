import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "bilibili-pixel-danmaku" / "config.json"

DEFAULT_CONFIG = {
    "room_id": 544853,
    "tts": {
        "enabled": True,
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "+0%",
        "volume": "+0%",
        "pitch": "+0Hz",
        "read_danmaku": True,
        "read_gifts": True,
        "read_superchat": True,
        "danmaku_template": "{user}说：{msg}",
        "gift_template": "感谢 {user} 送出的 {gift_name} x {num}",
        "sc_template": "感谢 {user} 的 {price} 元醒目留言：{msg}"
    },
    "audio": {
        "sound_effects_enabled": True,
        "master_volume": 80
    },
    "overlay": {
        "enabled": False,
        "opacity": 90,
        "width": 380,
        "height": 600,
        "font_size": 14,
        "max_danmaku": 30
    },
    "filter": {
        "min_medal_level": 0,
        "min_user_level": 0,
        "blocked_keywords": []
    }
}

class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config = self._merge_dict(DEFAULT_CONFIG, data)
            except Exception as e:
                print(f"[Config] 加载失败，使用默认配置: {e}")
                self.config = DEFAULT_CONFIG.copy()
        else:
            self.save()

    def save(self):
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] 保存失败: {e}")

    def get(self, key_path, default=None):
        keys = key_path.split(".")
        val = self.config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, key_path, value):
        keys = key_path.split(".")
        val = self.config
        for k in keys[:-1]:
            if k not in val or not isinstance(val[k], dict):
                val[k] = {}
            val = val[k]
        val[keys[-1]] = value
        self.save()

    def _merge_dict(self, default, current):
        merged = default.copy()
        for k, v in current.items():
            if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
                merged[k] = self._merge_dict(merged[k], v)
            else:
                merged[k] = v
        return merged
