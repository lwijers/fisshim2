# ecs/systems/ui/widgets/modal_window.py
import pygame
from typing import Tuple

class ModalWindow:
    """
    Simple modal shell used by FishWindowSystem.

    Contract:
      - open(title) draws the panel and returns:
          (win_rect, content_view_rect, close_rect, title_surface)
      - Sets context.ui_modal_active and ui_modal_whitelist = [close_rect]
      - Exposes rects back on context for MouseSystem strict-modal gating:
          context.fish_window_rect, context.fish_close_rect

    WHY this shape: FishWindowSystem expects this API and immediately unpacks
    the 4-tuple to layout its scrollable content and wire the close hitbox.
    """

    def __init__(self, screen: pygame.Surface, ctx) -> None:
        self.screen = screen
        self.ctx = ctx
        self._fonts: dict[int, pygame.font.Font] = {}

        # Visual style
        self.margin = 20
        self.pad = 28
        self.title_gap = 18
        self.bg_rgba = (10, 15, 22, 200)
        self.border = (220, 230, 255)
        self.close_size = 32
        self.close_pad = 14

    # --- font helpers ---
    def _font(self, px: int) -> pygame.font.Font:
        f = self._fonts.get(px)
        if f is None:
            f = pygame.font.SysFont("arial", int(px))
            self._fonts[px] = f
        return f

    def _ui_title_px(self) -> int:
        # WHY: keep title size tied to global UI base for consistency
        base = int((getattr(self.ctx, "ui", {}) or {}).get("ui_font_size", 14))
        return base + 10

    # --- public API expected by FishWindowSystem ---
    def open(self, title: str) -> Tuple[pygame.Rect, pygame.Rect, pygame.Rect, pygame.Surface]:
        sw, sh = self.screen.get_size()

        # Outer window rect (full-screen inset)
        win_rect = pygame.Rect(self.margin, self.margin, sw - self.margin * 2, sh - self.margin * 2)

        # Panel background
        panel = pygame.Surface((win_rect.w, win_rect.h), pygame.SRCALPHA)
        panel.fill(self.bg_rgba)
        self.screen.blit(panel, (win_rect.x, win_rect.y))
        pygame.draw.rect(self.screen, self.border, win_rect, width=2)

        # Title
        title_font = self._font(self._ui_title_px())
        title_surf = title_font.render(title, True, (235, 240, 255))
        self.screen.blit(title_surf, (win_rect.x + self.pad, win_rect.y + self.pad))

        # Close button rect (top-right inside the panel)
        close_rect = pygame.Rect(
            win_rect.x + win_rect.w - self.close_pad - self.close_size,
            win_rect.y + self.close_pad,
            self.close_size,
            self.close_size,
        )
        self._draw_close(close_rect)

        # Client/content viewport (below title)
        inner_x = win_rect.x + self.pad
        inner_y = win_rect.y + self.pad + title_surf.get_height() + self.title_gap
        inner_w = win_rect.w - self.pad * 2
        inner_h = win_rect.h - (inner_y - win_rect.y) - self.pad
        content_view = pygame.Rect(inner_x, inner_y, inner_w, max(0, inner_h))

        # Strict modal lock for MouseSystem (only allow clicks on close/X while open)
        self.ctx.ui_modal_active = True
        self.ctx.ui_modal_whitelist = [close_rect]

        # Expose rects back to context so MouseSystem can hit-test and toggle the flag
        self.ctx.fish_window_rect = win_rect
        self.ctx.fish_close_rect = close_rect

        return win_rect, content_view, close_rect, title_surf

    # --- chrome ---
    def _draw_close(self, rect: pygame.Rect) -> None:
        mx, my = pygame.mouse.get_pos()
        hover = rect.collidepoint(mx, my)
        bg = (40, 45, 60) if not hover else (55, 60, 80)
        xcol = (240, 90, 100)

        pygame.draw.rect(self.screen, bg, rect, border_radius=8)
        # Draw an "X"
        pad = 9
        x1, y1 = rect.x + pad, rect.y + pad
        x2, y2 = rect.right - pad, rect.bottom - pad
        pygame.draw.line(self.screen, xcol, (x1, y1), (x2, y2), width=3)
        pygame.draw.line(self.screen, xcol, (x1, y2), (x2, y1), width=3)
