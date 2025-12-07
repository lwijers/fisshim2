# ecs/systems/cursor_system.py
import pygame

class CursorSystem:
    """
    Switches the mouse cursor based on selected tool:
      - feeding_enabled -> pellet.png
      - egging_enabled  -> egg.png
      - else            -> default arrow
    """
    def __init__(self, screen, assets, context):
        self.screen = screen
        self.assets = assets
        self.context = context
        self._last_state = None
        self._last_cursor_ok = None

    def _set_image_cursor(self, key, hotspot="center", max_dim=48):
        surf = self.assets.get(key)
        if surf is None:
            if self._last_cursor_ok is not False:
                print(f"⚠ cursor asset '{key}' not found; using default cursor")
                self._last_cursor_ok = False
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            return
        w, h = surf.get_width(), surf.get_height()
        if max(w, h) > max_dim:
            s = max_dim / max(w, h)
            surf = pygame.transform.smoothscale(surf, (int(w * s), int(h * s)))
            w, h = surf.get_width(), surf.get_height()
        hs = (w // 2, h // 2) if hotspot == "center" else (0, 0)
        try:
            cursor = pygame.cursors.Cursor(hs, surf)
            pygame.mouse.set_cursor(cursor)
            pygame.mouse.set_visible(True)
            self._last_cursor_ok = True
        except Exception as exc:
            if self._last_cursor_ok is not False:
                print(f"⚠ Could not set custom cursor ({exc}); defaulting")
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            self._last_cursor_ok = False

    def _apply_cursor(self):
        if getattr(self.context, "feeding_enabled", False):
            self._set_image_cursor("pellet")
        elif getattr(self.context, "egging_enabled", False):
            self._set_image_cursor("egg")
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            pygame.mouse.set_visible(True)

    def update(self, world, dt):
        state = (
            bool(getattr(self.context, "feeding_enabled", False)),
            bool(getattr(self.context, "egging_enabled", False)),
        )
        if state == self._last_state:
            return
        self._last_state = state
        self._apply_cursor()
