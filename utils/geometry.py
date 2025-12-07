# utils/geometry.py
from typing import Optional, Tuple
from ecs.components.core.position_component import Position
from ecs.components.core.sprite_component import Sprite

def get_mouth_logical(
    pos: Position,
    spr: Sprite,
    *,
    face_right: Optional[bool] = None,
    target_x: Optional[float] = None,
) -> Tuple[float, float]:
    """
    Return the mouth position in *logical* coordinates.

    Args:
        pos: fish Position (logical).
        spr: fish Sprite (must have base_w/base_h, optional mouth_fx/mouth_fy).
        face_right:
            - If provided, use this facing.
            - If None and target_x is provided, infer facing by comparing target_x to fish center.
            - If still None, fall back to spr.faces_right.
        target_x:
            - Optional target x (logical). Used to infer facing if face_right is None.

    Mouth anchor uses per-sprite (mouth_fx, mouth_fy) in the 0..1 range and mirrors X when facing left.
    """
    fx = float(getattr(spr, "mouth_fx", 0.85))
    fy = float(getattr(spr, "mouth_fy", 0.50))

    if face_right is None:
        if target_x is not None:
            center_x = pos.x + spr.base_w * 0.5
            face_right = (target_x >= center_x)
        else:
            face_right = bool(getattr(spr, "faces_right", True))

    if not face_right:
        fx = 1.0 - fx

    mx = pos.x + spr.base_w * fx
    my = pos.y + spr.base_h * fy
    return mx, my
