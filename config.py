# config.py
import json
import os

DEFAULT_CONFIG = {
    "screen_width": 1500,
    "screen_height": 1000,
    "fullscreen": False,
    "audio": {
        "enabled": True,
        "master_volume": 0.8,
        "num_channels": 8,
        "sounds": {
            "pellet_drop": [
                "assets/audio/shake1.wav",
                "assets/audio/shake2.wav",
                "assets/audio/shake3.wav"
            ],
            "bite": [                        # ← add this bank
                    "assets/audio/bite1.wav"
            ],
            "death": [                          # ← add this block
                    "assets/audio/death.wav"
            ]
        },
        "volumes": {
            "pellet_drop": 1.0,
            "bite": 1.0,
            "death": 1.0

        }
    }
}

# File next to config.py
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "settings.json")


# [config.py] — validate/normalize user config; keep defaults on bad values
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        final = DEFAULT_CONFIG.copy()
        final.update({k: v for k, v in data.items() if k in DEFAULT_CONFIG})
        # force types
        final["screen_width"]  = int(final["screen_width"])
        final["screen_height"] = int(final["screen_height"])
        final["fullscreen"]    = bool(final["fullscreen"])
        a = final.get("audio", {}) or {}
        a["enabled"]       = bool(a.get("enabled", True))
        a["master_volume"] = float(a.get("master_volume", 0.8))
        a["num_channels"]  = int(a.get("num_channels", 8))
        # normalize 'sounds' to dict[str, list[str]]
        sounds = a.get("sounds") or {}
        a["sounds"] = {str(k): list(v or []) for k, v in sounds.items()}
        # normalize 'volumes' to dict[str, float]
        vols = a.get("volumes") or {}
        a["volumes"] = {str(k): float(v) for k, v in vols.items()}
        final["audio"] = a
        return final
    except Exception as exc:
        print(f"⚠ Failed to load settings.json — using defaults. ({exc})")
        return DEFAULT_CONFIG.copy()



def save_config(config):
    """Write changes back to settings.json."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)
