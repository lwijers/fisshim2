# [utils/jsonio.py] — safer loads with encoding + defaults + clear errors
import json, io

def load_json(path, default=None):
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if default is not None:
            print(f"⚠ JSON not found, using default for {path}")
            return default
        raise
    except json.JSONDecodeError as e:
        if default is not None:
            print(f"⚠ Bad JSON ({path}): {e}. Using default.")
            return default
        raise

def save_json(path, data):
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def merge_with_defaults(data, defaults):
    out = defaults.copy()
    out.update(data or {})
    return out
