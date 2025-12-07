# Config loader tolerates missing/invalid values and normalizes types.
from config import load_config

def test_config_loader_defaults_and_normalization():
    cfg = load_config()
    # basic shape & types
    assert isinstance(cfg["screen_width"], int)
    assert isinstance(cfg["screen_height"], int)
    assert isinstance(cfg["fullscreen"], bool)

    audio = cfg.get("audio") or {}
    assert isinstance(audio.get("enabled", True), bool)
    assert 0.0 <= float(audio.get("master_volume", 0.8)) <= 1.0
    assert isinstance(audio.get("num_channels", 8), int)
    # dicts coerced
    assert isinstance(audio.get("sounds", {}), dict)
    assert isinstance(audio.get("volumes", {}), dict)
