# ecs/systems/ui_toolbar_system.py
import pygame

class UIToolbarSystem:
    """
    Draws a bottom-left toolbar with two toggles:
      - Feed (pellet)
      - Egg (egg_icon.png)
    Writes rectangles to context for InputSystem hit-test.
    """
    def __init__(self, screen, assets, context):
        self.screen = screen
        self.assets = assets
        self.context = context

    def _draw_button(self, x, y, size, on, icon_surf):
        rect = pygame.Rect(x, y, size, size)
        bg = (240, 210, 60) if on else (30, 30, 30)
        border = (200, 220, 255) if on else (140, 140, 140)
        pygame.draw.rect(self.screen, bg, rect, border_radius=8)
        pygame.draw.rect(self.screen, border, rect, width=2, border_radius=8)
        if icon_surf:
            pad = max(4, size // 8)
            iw = ih = size - pad * 2
            icon = pygame.transform.smoothscale(icon_surf, (iw, ih))
            self.screen.blit(icon, (x + pad, y + pad))
        return rect

    def update(self, world, dt):
        ui = self.context.ui or {}
        size = int(ui.get("ui_toolbar_button_size", 48))
        mx   = int(ui.get("ui_toolbar_margin_x", 12))
        my   = int(ui.get("ui_toolbar_margin_y", 12))
        sw, sh = self.screen.get_size()

        # Layout: [Feed] [Egg] from left
        x_feed = mx
        y = sh - my - size
        x_egg = x_feed + size + mx // 2

        # Feed button
        feed_on = bool(getattr(self.context, "feeding_enabled", False))
        feed_icon = self.assets.get("pellet")
        feed_rect = self._draw_button(x_feed, y, size, feed_on, feed_icon)
        self.context.toolbar_button_rect = feed_rect

        # Egg button
        egg_on = bool(getattr(self.context, "egging_enabled", False))
        egg_icon = self.assets.get("egg_icon") or self.assets.get("egg")  # fallback
        egg_rect = self._draw_button(x_egg, y, size, egg_on, egg_icon)
        self.context.toolbar_egg_rect = egg_rect
