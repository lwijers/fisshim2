# ecs/systems/ui/debug/debug_overlay_system.py
import pygame

class DebugOverlaySystem:
    """
    Only draws the Swim Area overlay (visualizes fall floor vs swim bottom).
    Text menus/legend are handled by DebugMenu (F1..F5) elsewhere.
    Controlled by: context.show_swim_floor_debug (bool)
    """
    _CLR_SWIM_WASH    = (80, 240, 120, 28)
    _CLR_EXT_WASH     = (80, 160, 255, 40)
    _CLR_BLOCK_WASH   = (200, 50, 50, 90)
    _CLR_SWIM_OUTLINE = (80, 240, 120)
    _CLR_FALL_FLOOR   = (255, 255, 255)
    _CLR_SWIM_BOTTOM  = (255, 200, 0)

    def __init__(self, screen, context):
        self.screen = screen
        self.context = context

    def _tank_rect_px(self):
        x = int(getattr(self.context, "tank_screen_x", 0))
        y = int(getattr(self.context, "tank_screen_y", 0))
        w = int(getattr(self.context, "tank_screen_w", self.screen.get_width()))
        h = int(getattr(self.context, "tank_screen_h", self.screen.get_height()))
        return x, y, max(0, w), max(0, h)

    def _ratio_or_px(self, px, ratio, y, h):
        if px is not None and px >= 0:
            return int(px)
        r = 1.0 if ratio is None else max(0.0, min(1.0, float(ratio)))
        return int(round(y + h * r))

    def _fall_floor_y(self, x, y, w, h):
        sand_px = getattr(self.context, "sand_top_px", None)
        sand_ratio = getattr(self.context, "sand_top_ratio", 1.0)
        return self._ratio_or_px(sand_px, sand_ratio, y, h)

    def _swim_bottom_y(self, x, y, w, h, fall_floor_y: int):
        sb_px = getattr(self.context, "swim_bottom_px", None)
        sb_ratio = getattr(self.context, "swim_bottom_ratio", None)
        if sb_px is not None or sb_ratio is not None:
            val = self._ratio_or_px(sb_px, sb_ratio, y, h)
        else:
            val = fall_floor_y + int(round(h * 0.06))
        val = max(y, min(y + h, val))
        return max(val, fall_floor_y)

    def update(self, world, dt):
        if not bool(getattr(self.context, "show_swim_floor_debug", False)):
            return

        x, y, w, h = self._tank_rect_px()
        if w <= 0 or h <= 0:
            return

        fall_y = self._fall_floor_y(x, y, w, h)
        swim_y = self._swim_bottom_y(x, y, w, h, fall_y)

        swim_main_h = max(0, fall_y - y)
        swim_ext_h  = max(0, swim_y - fall_y)
        block_h     = max(0, (y + h) - swim_y)

        if swim_main_h > 0:
            pygame.draw.rect(self.screen, self._CLR_SWIM_OUTLINE, pygame.Rect(x, y, w, swim_main_h), width=2)
            wash = pygame.Surface((w, swim_main_h), pygame.SRCALPHA)
            wash.fill(self._CLR_SWIM_WASH)
            self.screen.blit(wash, (x, y))

        if swim_ext_h > 0:
            ext = pygame.Surface((w, swim_ext_h), pygame.SRCALPHA)
            ext.fill(self._CLR_EXT_WASH)
            self.screen.blit(ext, (x, fall_y))

        if block_h > 0:
            blk = pygame.Surface((w, block_h), pygame.SRCALPHA)
            blk.fill(self._CLR_BLOCK_WASH)
            self.screen.blit(blk, (x, swim_y))

        pygame.draw.line(self.screen, self._CLR_FALL_FLOOR, (x, fall_y), (x + w, fall_y), width=1)
        pygame.draw.line(self.screen, self._CLR_SWIM_BOTTOM, (x, swim_y), (x + w, swim_y), width=1)
