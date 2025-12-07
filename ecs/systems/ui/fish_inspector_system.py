# ecs/systems/ui/fish_inspector_system.py
from __future__ import annotations
import pygame
from typing import Optional

from ecs.systems.ui.widgets.thumb_provider import ThumbProvider
from ecs.components.fish.species_component import Species
from ecs.components.core.sprite_component import Sprite
from ecs.components.fish.age_component import Age
from ecs.components.fish.brain_component import Brain
from ecs.components.fish.health_component import Health
from ecs.components.fish.hunger_component import Hunger


class FishInspectorSystem:
    """
    Simple, non-modal inspector for a single fish:
    - Opens when MouseSystem sets: context.show_fish_inspector = True and context.fish_inspector_entity = <eid>
    - Small top-left panel; uses ThumbProvider.card_thumb(...) for the portrait.
    - RMB close is handled in MouseSystem (global cancel); we simply hide if flag is False.
    """
    THUMB_BOX = 72
    W = 260
    H = 160
    PAD = 12

    def __init__(self, screen: pygame.Surface, assets, context):
        self.screen = screen
        self.assets = assets
        self.ctx = context
        self.thumbs = ThumbProvider(assets, context)

    def update(self, world, dt: float) -> None:
        if not getattr(self.ctx, "show_fish_inspector", False):
            return
        eid = getattr(self.ctx, "fish_inspector_entity", None)
        if not isinstance(eid, int):
            return

        # Anchor (top-left), or at a point provided by the mouse
        at = getattr(self.ctx, "fish_inspector_at", None)
        x = 12 if not at else max(8, int(at[0]) - self.W // 2)
        y = 12 if not at else max(8, int(at[1]) - self.H // 2)

        r = pygame.Rect(x, y, self.W, self.H)
        self._draw_panel_bg(r)
        self._draw_body(world, eid, r)

    # ---- internals ----
    def _draw_panel_bg(self, r: pygame.Rect) -> None:
        surf = self.screen
        # rounded bg + stroke
        pygame.draw.rect(surf, (22, 26, 32), r, border_radius=12)
        pygame.draw.rect(surf, (62, 70, 84), r, width=2, border_radius=12)

        # title
        font = pygame.font.SysFont(None, 18)
        title = font.render("Inspector", True, (235, 240, 245))
        surf.blit(title, (r.x + self.PAD, r.y + self.PAD))

        # close hint (visual only; RMB is actual close)
        hint = font.render("RMB to close", True, (150, 160, 170))
        surf.blit(hint, (r.right - hint.get_width() - self.PAD, r.y + self.PAD))

    def _draw_body(self, world, eid: int, r: pygame.Rect) -> None:
        surf = self.screen
        body = pygame.Rect(r.x + self.PAD, r.y + self.PAD + 22, r.w - 2 * self.PAD, r.h - (self.PAD + 22 + self.PAD))

        # Portrait uses the SAME pipeline as Fish Window (and tank cards)
        thumb = self.thumbs.card_thumb(world, eid, self.THUMB_BOX)
        tw, th = thumb.get_size()
        tx = body.x
        ty = body.y + max(0, (self.THUMB_BOX - th) // 2)
        surf.blit(thumb, (tx, ty))

        # Info column
        info_x = body.x + self.THUMB_BOX + 10
        info_w = max(0, body.w - self.THUMB_BOX - 10)
        info = pygame.Rect(info_x, body.y, info_w, body.h)

        font = pygame.font.SysFont(None, 14)

        sp: Optional[Species] = world.get_component(eid, Species)
        age: Optional[Age] = world.get_component(eid, Age)
        br: Optional[Brain] = world.get_component(eid, Brain)
        hp: Optional[Health] = world.get_component(eid, Health)
        hg: Optional[Hunger] = world.get_component(eid, Hunger)

        def _pct(v, mx) -> str:
            try:
                return f"{int(round(100.0 * float(v) / max(1.0, float(mx))))}%"
            except Exception:
                return "-"

        lines = [
            f"Species: {getattr(sp, 'display_name', 'Unknown')}",
            f"Stage:   {getattr(age, 'stage', 'Unknown')}",
            f"Age:     {int(getattr(age, 'age', 0.0))}/{int(getattr(age, 'lifespan', 0.0))}",
            f"Health:  {int(getattr(hp, 'value', 0.0))}/{int(getattr(hp, 'max_value', 0.0))}",
            f"Hunger:  {int(getattr(hg, 'hunger', 0.0))}/{int(getattr(hg, 'hunger_max', 100.0))} ({_pct(getattr(hg,'hunger',0.0), getattr(hg,'hunger_max',100.0))})",
            f"Brain:   {getattr(br, 'state', 'Unknown')}",
        ]

        y = info.y
        for s in lines:
            surf.blit(font.render(s, True, (230, 235, 245)), (info.x, y))
            y += 18
