# ecs/systems/ui/widgets/scrollbox.py
import pygame
from typing import Optional

class ScrollBox:
    """
    Offscreen content with vertical scrolling + track/thumb drawing + drag handling.
    Supports mouse wheel via on_wheel(delta_px).

    Usage:
      - sync(content_h, view_h)
      - draw_scrollbar(screen, track_rect)
      - handle_mouse(track_rect)          # drag thumb
      - on_wheel(delta_px)                # wheel scroll (+down, -up)
    """
    def __init__(self):
        self.scroll_y = 0.0
        self.content_h = 0
        self.view_h = 0
        self.min_thumb = 24
        self.wheel_step_px = 60  # one wheel notch
        self._drag = False
        self._start_y = 0
        self._start_scroll = 0.0
        self._prev_mb1 = False

    def sync(self, content_h: int, view_h: int):
        self.content_h = int(max(0, content_h))
        self.view_h = int(max(0, view_h))
        self.scroll_y = max(0.0, min(float(max(0, self.content_h - self.view_h)), self.scroll_y))

    def on_wheel(self, delta_px: float):
        """Positive delta scrolls DOWN; negative scrolls UP."""
        if self.content_h <= self.view_h:
            self.scroll_y = 0.0
            return
        max_scroll = float(self.content_h - self.view_h)
        self.scroll_y = max(0.0, min(max_scroll, self.scroll_y + float(delta_px)))

    def thumb_rect(self, track: pygame.Rect) -> pygame.Rect:
        if self.content_h <= self.view_h or self.view_h <= 0:
            return pygame.Rect(track.x, track.y, track.w, track.h)
        ratio = self.view_h / self.content_h
        th = max(self.min_thumb, int(track.h * ratio))
        max_scroll = self.content_h - self.view_h
        t = 0.0 if max_scroll <= 0 else (self.scroll_y / max_scroll)
        travel = track.h - th
        ty = track.y + int(travel * t)
        return pygame.Rect(track.x, ty, track.w, th)

    def draw_scrollbar(self, screen, track: pygame.Rect, track_col=(60,70,90), thumb_col=(160,175,200)):
        pygame.draw.rect(screen, track_col, track, border_radius=5)
        if self.content_h > self.view_h:
            pygame.draw.rect(screen, thumb_col, self.thumb_rect(track), border_radius=5)

    def handle_mouse(self, track: pygame.Rect):
        mb1 = pygame.mouse.get_pressed(num_buttons=3)[0]
        mx, my = pygame.mouse.get_pos()

        if mb1 and not self._prev_mb1 and self.content_h > self.view_h:
            if self.thumb_rect(track).collidepoint(mx, my):
                self._drag = True
                self._start_y = my
                self._start_scroll = self.scroll_y

        if self._drag:
            dy = my - self._start_y
            thumb = self.thumb_rect(track)
            travel = max(1, track.h - thumb.h)
            if travel > 0 and self.content_h > self.view_h:
                ratio = (self.content_h - self.view_h) / travel
                self.scroll_y = self._start_scroll + dy * ratio
                max_scroll = max(0, self.content_h - self.view_h)
                self.scroll_y = max(0.0, min(float(max_scroll), self.scroll_y))

        if not mb1:
            self._drag = False

        self._prev_mb1 = mb1
