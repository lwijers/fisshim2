# ecs/systems/renderers/overlay_food.py
import pygame
from ecs.components.core.position_component import Position
from ecs.components.core.sprite_component import Sprite
from ecs.components.tags.food_pellet_component import FoodPellet

from .geometry import (
    mouth_radius_from_tuning, vision_radius_from_tuning
)
from utils.geometry import get_mouth_logical

def _pellet_center_and_radius_render(world, pellet_id, *,
                                     radius_scale: float = 1.0,
                                     off_x: float = 0.0, off_y: float = 0.0):
    """Same math the FSM uses, but local to the renderer to avoid imports."""
    comps = getattr(world, "_components", {})
    if pellet_id not in comps:
        return None, None, None
    p = world.get_component(pellet_id, Position)
    s = world.get_component(pellet_id, Sprite)
    if not p or not s:
        return None, None, None
    cx = p.x + s.base_w * 0.5 + float(off_x)
    cy = p.y + s.base_h * 0.5 + float(off_y)
    base_r = max(s.base_w, s.base_h) * 0.5
    pr = base_r * float(radius_scale)
    return cx, cy, pr


# ecs/systems/renderers/overlay_food.py  (replace the whole draw_food_debug function)

def draw_food_debug(screen, world, context,
                    pos, spr, brain, tuning,
                    face_right: bool,
                    tank_pos, scale,
                    draw_x: int, draw_y: int, screen_w: int, screen_h: int):

    # Only run if the overlay is on AND this entity is a fish (has a Brain)
    if not (context.show_fish_vision or context.show_pellet_radius or context.show_food_links):
        return
    if brain is None or tank_pos is None:
        return

    # ---------- fish center / vision ----------
    fcx = draw_x + screen_w // 2
    fcy = draw_y + screen_h // 2
    if context.show_fish_vision:
        vision = vision_radius_from_tuning(tuning, 200.0)
        pygame.draw.circle(screen, (0, 200, 255), (fcx, fcy), max(1, int(vision * scale)), 1)

    # ---------- mouth marker ----------
    mx, my = get_mouth_logical(pos, spr, face_right=face_right)  # logical
    mcx = int(round(tank_pos.x + mx * scale))
    mcy = int(round(tank_pos.y + my * scale))
    mouth_r_logical = mouth_radius_from_tuning(spr, tuning)
    pygame.draw.circle(screen, (255, 0, 255), (mcx, mcy), max(1, int(mouth_r_logical * scale)), 2)

    # ---------- targeted pellet: draw the *actual* collision circle (pr) ----------
    pe = getattr(brain, "_target_pellet", None)
    if pe is None:
        return

    ppos = world.get_component(pe, Position)
    pspr = world.get_component(pe, Sprite)
    pcmp = world.get_component(pe, FoodPellet)
    if not (ppos and pspr):
        return

    # Match the sprite blit rounding exactly
    draw_px = int(round(tank_pos.x + ppos.x * scale))
    draw_py = int(round(tank_pos.y + ppos.y * scale))
    pw = int(round(pspr.base_w * scale))
    ph = int(round(pspr.base_h * scale))

    scx = draw_px + pw // 2
    scy = draw_py + ph // 2

    # pr (logical) is exactly what the FSM uses: base half-size * radius_scale
    base_r_logical = max(pspr.base_w, pspr.base_h) * 0.5
    radius_scale = float(getattr(pcmp, "radius_scale", 1.0)) if pcmp else 1.0
    pr_screen = int(base_r_logical * radius_scale * scale)

    if context.show_pellet_radius:
        # Collision circle around pellet (this is the one compared to the mouth)
        pygame.draw.circle(screen, (80, 200, 255), (scx, scy), max(1, pr_screen), 2)

        # Optional: also show the actual eat threshold (pr + mouth_r + margin)
        eat_margin = float(tuning.get("eat_extra_margin", 6.0))
        eat_screen = int((base_r_logical * radius_scale + mouth_r_logical + eat_margin) * scale)
        pygame.draw.circle(screen, (120, 230, 255), (scx, scy), max(1, eat_screen), 1)

    if context.show_food_links:
        pygame.draw.line(
            screen, (255, 200, 0),
            (mcx, mcy), (scx, scy),
            max(1, int(context.ui.get("ui_target_line_width", 1)))
        )





def draw_target_line_from_mouth(screen, context,
                                pos, spr, brain,
                                face_right, tank_pos, scale,
                                draw_x: int, draw_y: int, screen_w: int, screen_h: int):
    if not (context.show_target_lines and brain and tank_pos is not None):
        return
    mx, my = get_mouth_logical(pos, spr, face_right=face_right)  # logical
    sx0 = int(round(tank_pos.x + mx * scale))
    sy0 = int(round(tank_pos.y + my * scale))
    sx1 = int(round(tank_pos.x + brain.tx * scale))
    sy1 = int(round(tank_pos.y + brain.ty * scale))
    pygame.draw.line(
        screen, (255, 200, 0), (sx0, sy0), (sx1, sy1),
        max(1, int(context.ui.get("ui_target_line_width", 1)))
    )

