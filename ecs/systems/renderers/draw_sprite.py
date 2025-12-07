import pygame
from typing import Optional
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.position_component import Position
from ecs.components.core.velocity_component import Velocity
from ecs.components.fish.brain_component import Brain
from ecs.components.fish.target_intent_component import TargetIntent
from .cache import SpriteCache


def choose_facing(
    spr: Sprite,
    vel: Optional[Velocity],
    target: Optional[TargetIntent],
    pos: Position,
    last_facing: bool
):
    """
    Decide which way the fish *wants* to face (logic-facing) with hysteresis.
    We only flip when there's a clear left/right signal to avoid flicker
    while following vertical lines or sitting nearly still.

    Returns: (face_right, need_hflip_relative_to_art)
    """
    # Tunables (logical units)
    VEL_DEADZONE = 5.0                         # px/s of horizontal speed required to flip by velocity
    # Use the fish's own size to scale the target deadzone, with a floor
    target_deadzone = max(4.0, spr.base_w * 0.10)

    face_right = last_facing  # default: keep the previous facing

    # 1) Strong hint: horizontal velocity
    if vel is not None and abs(vel.dx) > VEL_DEADZONE:
        face_right = (vel.dx >= 0)
    # 2) Secondary hint: target X vs fish *center* X (with deadzone)
    elif target is not None:
        center_x = pos.x + spr.base_w * 0.5
        dx = (target.tx - center_x)
        if abs(dx) > target_deadzone:
            face_right = (dx >= 0)
        # else: keep last_facing

    # If none of the above, we keep last_facing.

    # Determine if we must flip relative to the base art
    need_hflip = (face_right != spr.faces_right)
    return face_right, need_hflip


def draw_sprite(
    screen,
    assets,
    sprite_cache: SpriteCache,
    pos: Position,
    spr: Sprite,
    brain: Optional[Brain],
    face_right: bool,
    need_hflip: bool,
    tank_pos: Optional[Position],
    scale: float,
    *,
    debug_border: bool = False,
    border_w: int = 1
):
    """
    Draw the sprite with correct orientation and dead presentation.

    - Alive: normal color; optional horizontal flip if logic-facing differs
             from the base art.
    - Dead:  grayscale + vertical flip ONLY (no horizontal flip at all).
    """
    img = assets.get(spr.image_id)
    if img is None:
        return None, None, None, None

    # Compute draw rect in screen space
    if tank_pos is not None:
        draw_x = tank_pos.x + pos.x * scale
        draw_y = tank_pos.y + pos.y * scale
        screen_w = int(spr.base_w * scale)
        screen_h = int(spr.base_h * scale)
    else:
        draw_x, draw_y = pos.x, pos.y
        screen_w, screen_h = spr.base_w, spr.base_h

    # Dead look = grayscale + vertical flip, but NEVER horizontal mirroring
    is_dead = bool(brain and brain.state == "Dead")
    apply_hflip = (need_hflip and not is_dead)

    scaled = sprite_cache.get(
        img, screen_w, screen_h,
        dead=is_dead,         # triggers grayscale + vertical flip in cache
        hflip=apply_hflip     # suppress horizontal flip when dead
    )

    ix = int(round(draw_x))
    iy = int(round(draw_y))
    screen.blit(scaled, (ix, iy))

    if debug_border:
        pygame.draw.rect(
            screen, (255, 0, 0),
            pygame.Rect(ix, iy, screen_w, screen_h),
            width=max(1, int(border_w))
        )

    return ix, iy, screen_w, screen_h
