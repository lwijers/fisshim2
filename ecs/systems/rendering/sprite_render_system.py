# ecs/systems/rendering/sprite_render_system.py
from __future__ import annotations
import pygame
from typing import Optional

from ecs.components.core.position_component import Position
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.tank_ref_component import TankRef
from ecs.components.core.velocity_component import Velocity
from ecs.components.fish.brain_component import Brain
from ecs.components.fish.target_intent_component import TargetIntent
from ecs.components.fish.age_component import Age
from ecs.systems.renderers import choose_facing
from ecs.systems.renderers.cache import SpriteCache

class SpriteRenderSystem:
    """
    Draw fish sprites and publish per-fish screen rects for click hit-testing.

    WHY: MouseSystem._hit_test_fish reads context.fish_screen_rects.
    If this list is missing or stale, clicks won't open panels.
    """

    def __init__(self, screen, assets, context, cache_limit: int = 256):
        self.screen = screen
        self.assets = assets
        self.context = context

        self.sprite_cache = SpriteCache.shared()
        ui = getattr(context, "ui", {}) or {}
        self.sprite_cache.cache_limit = int(ui.get("render_cache_limit", cache_limit))

        self._last_scale: Optional[float] = None
        self._last_facing: dict[int, bool] = {}

    def _senior_style_cfg(self) -> dict:
        aging = getattr(self.context, "aging", {}) or {}
        return {
            "desaturate": float(aging.get("senior_desaturate", 0.6)),
            "tint": tuple(aging.get("senior_tint", [235, 225, 215])),
            "outline": bool(aging.get("senior_outline", True)),
            "outline_px": int(aging.get("senior_outline_px", 1)),
            "outline_color": tuple(aging.get("senior_outline_color", [40, 35, 30, 255])),
        }

    def update(self, world, dt) -> None:
        # Invalidate cache when tank scale changes
        scale = float(getattr(self.context, "tank_scale", 1.0))
        if self._last_scale != scale:
            self.sprite_cache.clear()
            self._last_scale = scale

        # Rebuild hit rects every frame
        self.context.fish_screen_rects = []  # list[(entity_id, pygame.Rect)]

        for e in world.entities_with(Position, Sprite):
            pos: Position = world.get_component(e, Position)
            spr: Sprite = world.get_component(e, Sprite)
            vel: Optional[Velocity] = world.get_component(e, Velocity)
            brain: Optional[Brain] = world.get_component(e, Brain)
            age: Optional[Age] = world.get_component(e, Age)
            tank_ref: Optional[TankRef] = world.get_component(e, TankRef)
            target: Optional[TargetIntent] = world.get_component(e, TargetIntent)

            if not tank_ref:
                continue
            tank_pos: Optional[Position] = world.get_component(tank_ref.tank_entity, Position)
            if not tank_pos:
                continue

            # Facing/hflip
            last_face = self._last_facing.get(e, spr.faces_right)
            face_right, need_hflip = choose_facing(spr, vel, target, pos, last_face)
            self._last_facing[e] = face_right

            # World → screen
            base_w = int(round(spr.base_w * scale))
            base_h = int(round(spr.base_h * scale))
            draw_x = int(round(tank_pos.x + pos.x * scale))
            draw_y = int(round(tank_pos.y + pos.y * scale))

            # Stage/variant
            stage = getattr(age, "stage", "Adult") if age else "Adult"
            is_dead = (getattr(brain, "state", "") == "Dead")
            is_senior = bool(age and stage == "Senior")
            is_juvenile = bool(age and stage == "Juvenile")
            is_egg = bool(age and stage == "Egg")

            # Base asset
            base_img = self.assets.get(getattr(spr, "image_id", None))
            if is_egg:
                base_img = self.assets.get("egg") or base_img
            if base_img is None:
                continue

            # Size selection (cards are elsewhere; here we render full-size fish w/ juvenile scaling)
            screen_w = base_w
            screen_h = base_h
            if is_juvenile:
                juvenile_scale = float((getattr(self.context, "aging", {}) or {}).get("juvenile_scale", 0.5))
                screen_w = max(1, int(round(base_w * juvenile_scale)))
                screen_h = max(1, int(round(base_h * juvenile_scale)))

            # Variant flags
            variant = "normal"
            senior_style = None
            if (not is_dead) and is_senior:
                variant = "senior"
                senior_style = self._senior_style_cfg()

            # Finals
            surf = self.sprite_cache.get(
                base_img,
                screen_w, screen_h,
                dead=is_dead,
                hflip=(need_hflip and not is_dead),
                variant=variant,
                senior_style=senior_style,
            )

            # Center scaled fish inside its base box so geometry is stable
            ix = int(round(draw_x + (base_w - screen_w) * 0.5))
            iy = int(round(draw_y + (base_h - screen_h) * 0.5))
            self.screen.blit(surf, (ix, iy))

            # Publish clickable rect = drawn rect
            self.context.fish_screen_rects.append((e, pygame.Rect(ix, iy, screen_w, screen_h)))
