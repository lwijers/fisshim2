# ecs/systems/ui/widgets/panel.py
from __future__ import annotations
import pygame
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Union

Color = Union[Tuple[int, int, int], Tuple[int, int, int, int]]

@dataclass
class InspectorPanel:
    """Floating panel widget state (reusable, animatable)."""
    id: int
    kind: str            # e.g., "fish"
    title: str
    x: int
    y: int
    w: int
    h: int
    z: int
    entity: Optional[int] = None
    render_body: Optional[Callable[[pygame.Surface, pygame.Rect], None]] = None

    # updated per-frame (exported by renderer)
    close_rect: Optional[pygame.Rect] = None
    header_rect: Optional[pygame.Rect] = None
    body_rect: Optional[pygame.Rect] = None

    # animation targets/state (managed by PanelManagerSystem)
    tx: Optional[int] = None           # target x
    ty: Optional[int] = None           # target y
    ax0: Optional[int] = None          # anim start x
    ay0: Optional[int] = None          # anim start y
    anim_start_ms: Optional[int] = None
    anim_dur_ms: int = 0
    anim_kind: Optional[str] = None    # "drop" | "shift" | None

@dataclass
class PanelTheme:
    radius: int = 10
    pad: int = 12
    gap_rows: int = 6
    gap_cols: int = 12
    line_h: int = 20
    title_pad_h: int = 2
    min_w: int = 200
    max_w: int = 360
    bg: Color = (28, 34, 48, 235)
    border: Color = (180, 195, 215)
    title_color: Color = (235, 240, 255)
    label_color: Color = (180, 190, 210)
    value_color: Color = (235, 240, 255)
    close_bg: Color = (60, 65, 80)
    close_fg: Color = (220, 120, 130)

class PanelRenderer:
    """Draws a rounded floating panel and delegates body to a callback."""
    def __init__(self, screen: pygame.Surface, theme: Optional[PanelTheme] = None):
        self.screen = screen
        self.theme = theme or PanelTheme()
        self._font_cache: dict[int, pygame.font.Font] = {}

    def font(self, px: int) -> pygame.font.Font:
        f = self._font_cache.get(px)
        if f is None:
            f = pygame.font.SysFont("arial", int(px))
            self._font_cache[px] = f
        return f

    def draw(self, panel: InspectorPanel, title_px: int) -> None:
        t = self.theme
        font_title = self.font(title_px)
        ts = font_title.render(panel.title, True, t.title_color)
        title_h = ts.get_height() + t.title_pad_h

        panel_rect = pygame.Rect(panel.x, panel.y, panel.w, panel.h)
        header_rect = pygame.Rect(panel_rect.x + t.pad, panel_rect.y + t.pad,
                                  panel_rect.w - 2 * t.pad, title_h)
        close_size = 18
        close_rect = pygame.Rect(panel_rect.right - t.pad - close_size,
                                 panel_rect.y + t.pad, close_size, close_size)
        body_y = header_rect.bottom + t.gap_rows
        body_rect = pygame.Rect(panel_rect.x + t.pad, body_y,
                                panel_rect.w - 2 * t.pad, panel_rect.bottom - t.pad - body_y)

        # Rounded fill + border
        bg = pygame.Surface((panel_rect.w, panel_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(bg, t.bg, bg.get_rect(), border_radius=t.radius)
        self.screen.blit(bg, (panel_rect.x, panel_rect.y))
        pygame.draw.rect(self.screen, t.border, panel_rect, width=1, border_radius=t.radius)

        # Title and close
        self.screen.blit(ts, (header_rect.x, header_rect.y))
        pygame.draw.rect(self.screen, t.close_bg, close_rect, border_radius=6)
        cx = self.font(max(12, title_px - 4)).render("×", True, t.close_fg)
        self.screen.blit(cx, (close_rect.x + (close_rect.w - cx.get_width()) // 2,
                              close_rect.y + (close_rect.h - cx.get_height()) // 2))

        # Body content
        if callable(panel.render_body):
            panel.render_body(self.screen, body_rect)

        # Export rects
        panel.close_rect = close_rect
        panel.header_rect = header_rect
        panel.body_rect = body_rect

    @staticmethod
    def clamp_to_screen(rect: pygame.Rect, screen_size: Tuple[int, int]) -> None:
        sw, sh = screen_size
        rect.x = min(max(0, rect.x), max(0, sw - rect.w))
        rect.y = min(max(0, rect.y), max(0, sh - rect.h))
