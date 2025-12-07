# render/audio_manager.py
import os
import random
import pygame
from typing import Dict, List, Optional

class AudioManager:
    """
    Minimal, settings-driven SFX manager.

    Settings structure (in settings.json):
    {
      "audio": {
        "enabled": true,
        "master_volume": 0.8,
        "num_channels": 8,
        "sounds": {
          "pellet_drop": ["assets/audio/shake1.wav", "assets/audio/shake2.wav", "assets/audio/shake3.wav"],
          "ui_click": ["assets/audio/click1.wav", "assets/audio/click2.wav"]
        },
        "volumes": {
          "pellet_drop": 1.0,     // optional per-sound volume multiplier
          "ui_click": 0.6
        }
      }
    }

    Usage:
        audio.play("pellet_drop")
        audio.play("ui_click", volume=0.4)
    """
    def __init__(self, settings: dict):
        self._settings = settings or {}
        a = (self._settings.get("audio") or {})
        self.enabled       = bool(a.get("enabled", True))
        self.master_volume = float(a.get("master_volume", 0.8))
        self.num_channels  = int(a.get("num_channels", 8))

        # sounds: name -> list[file paths]
        self._bank_files: Dict[str, List[str]] = dict(a.get("sounds") or {})
        # per-sound volume multipliers (optional)
        self._volumes: Dict[str, float] = {k: float(v) for k, v in (a.get("volumes") or {}).items()}

        self._bank: Dict[str, List[pygame.mixer.Sound]] = {}
        self._ready = False

        self._init_mixer()
        self._load_bank()

    # -------- internal ----------
    def _init_mixer(self):
        if not self.enabled:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(self.num_channels)
            self._ready = True
        except Exception as exc:
            print(f"⚠ Audio disabled (mixer init failed): {exc}")
            self.enabled = False
            self._ready = False

    def _load_bank(self):
        if not (self.enabled and self._ready):
            return
        for name, files in self._bank_files.items():
            sounds: List[pygame.mixer.Sound] = []
            for path in files:
                try:
                    if not os.path.isfile(path):
                        print(f"⚠ Missing audio file: {path}")
                        continue
                    s = pygame.mixer.Sound(path)
                    sounds.append(s)
                except Exception as exc:
                    print(f"⚠ Failed to load sound '{path}': {exc}")
            if not sounds:
                print(f"⚠ No audio clips loaded for '{name}'")
            self._bank[name] = sounds

    def _resolve_volume(self, name: str, volume: Optional[float]) -> float:
        # final = master * per-sound * call-time
        per_sound = float(self._volumes.get(name, 1.0))
        call = 1.0 if volume is None else float(volume)
        return max(0.0, min(1.0, self.master_volume * per_sound * call))

    # -------- public API ----------
    def play(self, name: str, *, volume: Optional[float] = None):
        """Play a random clip from the named sound bank (if available)."""
        if not (self.enabled and self._ready):
            return
        clips = self._bank.get(name)
        if not clips:
            # Silent fail is fine in games; keep logs minimal
            # print(f"⚠ Sound '{name}' not found or empty.")
            return
        clip = random.choice(clips)
        try:
            clip.set_volume(self._resolve_volume(name, volume))
            clip.play()
        except Exception as exc:
            print(f"⚠ Failed to play '{name}': {exc}")

    # Backwards-compat alias for any existing calls
    def play_shake(self):
        self.play("pellet_drop")
