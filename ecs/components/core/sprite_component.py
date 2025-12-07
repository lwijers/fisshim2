# ecs/components/sprite_component.py
from dataclasses import dataclass

@dataclass
class Sprite:
    image_id: str      # key to look up in AssetManager
    base_w: int        # logical/base width (e.g. species["width"])
    base_h: int        # logical/base height
    z: int = 1         # layer depth if needed later
    faces_right: bool = True  # base art faces right by default

    # Mouth anchor (fractions of sprite width/height).
    # When facing right, mouth is at (mouth_fx * base_w, mouth_fy * base_h).
    # When facing left, the X anchor is mirrored automatically in code.
    mouth_fx: float = 0.85
    mouth_fy: float = 0.50
