# ecs/systems/tank_render_system.py
import pygame
from ecs.components.core.position_component import Position
from ecs.components.core.bounds_component import Bounds
from ecs.components.core.tank_style_component import TankStyle
from ecs.components.core.tank_label_component import TankLabel

class TankRenderSystem:
    def __init__(self, screen, assets=None, context=None):
        self.screen = screen
        self.assets = assets
        self.context = context
        # lazy init (font may depend on size from ui config)
        self._font_cache = {}

    def _get_font(self, size: int):
        if size not in self._font_cache:
            self._font_cache[size] = pygame.font.SysFont("arial", int(size))
        return self._font_cache[size]

    def update(self, world, dt):
        for e in world.entities_with(Position, Bounds, TankStyle):
            pos = world.get_component(e, Position)
            bounds = world.get_component(e, Bounds)
            style = world.get_component(e, TankStyle)

            x, y = pos.x, pos.y
            w, h = bounds.width, bounds.height

            # ---------- background ----------
            if self.assets is not None and "tank_bg" in self.assets.images:
                bg = self.assets.get("tank_bg")
                scaled = pygame.transform.smoothscale(bg, (w, h))
                self.screen.blit(scaled, (x, y))
            else:
                pygame.draw.rect(self.screen, (10, 20, 40), pygame.Rect(x, y, w, h))

            # ---------- bottom-center label (if present) ----------
            label = world.get_component(e, TankLabel)
            if label and (label.text or label.text == ""):
                ui = (self.context.ui if self.context else {}) or {}
                size   = int(ui.get("ui_tank_label_size",  max(1, label.size)))
                color  = tuple(ui.get("ui_tank_label_color", list(label.color)))
                margin = int(ui.get("ui_tank_label_bottom_margin", 22))
                shadow = bool(ui.get("ui_tank_label_shadow", True))

                font = self._get_font(size)
                surf = font.render(label.text, True, color)
                tx = x + (w - surf.get_width()) // 2
                ty = y + h - margin - surf.get_height()

                # simple shadow for readability on the substrate
                if shadow:
                    shadow_surf = font.render(label.text, True, (0, 0, 0))
                    self.screen.blit(shadow_surf, (tx + 2, ty + 2))

                self.screen.blit(surf, (tx, ty))

            # ---------- border ----------
            pygame.draw.rect(
                self.screen,
                style.border_color,
                pygame.Rect(x, y, w, h),
                style.thickness
            )
