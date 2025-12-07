# ecs/systems/ui/fish_window_system.py
from __future__ import annotations
import pygame
from typing import Optional, List

from ecs.components.core.sprite_component import Sprite
from ecs.components.fish.species_component import Species
from ecs.components.fish.hunger_component import Hunger
from ecs.components.fish.health_component import Health
from ecs.components.fish.age_component import Age
from ecs.components.fish.brain_component import Brain

from ecs.systems.ui.widgets.modal_window import ModalWindow
from ecs.systems.ui.widgets.scrollbox import ScrollBox
from ecs.systems.ui.widgets.grid_layout import CardGrid
from ecs.systems.ui.widgets.thumb_provider import ThumbProvider


class FishWindowSystem:
    # Button
    BTN_PAD_X = 14
    BTN_PAD_Y = 8
    WIN_MARGIN = 20
    CLR_BTN_BG = (30, 30, 30)
    CLR_BTN_BG_HOVER = (45, 45, 45)
    CLR_BTN_BORDER = (160, 175, 200)
    CLR_BTN_TEXT = (235, 240, 255)

    # Window
    WIN_PAD = 28
    TITLE_GAP = 18

    # Cards
    GRID_GUTTER_X = 40
    GRID_GUTTER_Y = 26
    CARD_W = 300
    CARD_H = 120
    CARD_RADIUS = 12
    CARD_PAD = 14
    SPRITE_BOX = 72
    TEXT_LEFT = 16
    GAP = 10
    CLR_CARD_BG = (28, 34, 48)
    CLR_CARD_BORDER = (90, 110, 150)
    CLR_TEXT = (235, 240, 255)
    CLR_SUB = (180, 195, 215)

    # Bars
    BAR_H = 10
    BAR_GAP = 6
    CLR_BAR_BG = (60, 70, 90)
    CLR_BAR_HUNGER = (255, 220, 80)
    CLR_BAR_HEALTH = (110, 255, 120)

    # Scroll
    SCROLL_W = 10
    SCROLL_PAD = 8

    def __init__(self, screen: pygame.Surface, assets, context):
        self.screen = screen
        self.assets = assets
        self.context = context
        self._fonts: dict[int, pygame.font.Font] = {}

        self.modal = ModalWindow(screen, context)
        self.scroll = ScrollBox()
        self.grid = CardGrid(self.CARD_W, self.CARD_H, self.GRID_GUTTER_X, self.GRID_GUTTER_Y)
        self.thumbs = ThumbProvider(self.assets, self.context)

        self._list_view_rect: Optional[pygame.Rect] = None
        self._scroll_track_rect: Optional[pygame.Rect] = None

    # ---------------- fonts/sizing ----------------
    def _font(self, px: int) -> pygame.font.Font:
        f = self._fonts.get(px)
        if f is None:
            f = pygame.font.SysFont("arial", int(px))
            self._fonts[px] = f
        return f

    def _ui_sizes(self) -> dict:
        base = int((getattr(self.context, "ui", {}) or {}).get("ui_font_size", 14))
        return {"title": base + 10, "name": base + 4, "meta": base}

    # ---------------- lifecycle ----------------
    def update(self, world, dt: float) -> None:
        self._draw_button()

        if bool(getattr(self.context, "show_fish_window", False)):
            self._draw_window(world)
        else:
            if getattr(self.context, "ui_modal_active", False):
                self.context.ui_modal_active = False
                self.context.ui_modal_whitelist = None

    # ---------------- UI: top-right button ----------------
    def _draw_button(self) -> None:
        sizes = self._ui_sizes()
        label = "Fish"
        font = self._font(sizes["name"])

        sw, sh = self.screen.get_size()
        tsurf = font.render(label, True, self.CLR_BTN_TEXT)
        tw, th = tsurf.get_size()

        w = tw + self.BTN_PAD_X * 2
        h = th + self.BTN_PAD_Y * 2
        x = sw - self.WIN_MARGIN - w
        y = self.WIN_MARGIN
        rect = pygame.Rect(x, y, w, h)

        mx, my = pygame.mouse.get_pos()
        hover = rect.collidepoint(mx, my)

        pygame.draw.rect(self.screen, self.CLR_BTN_BG_HOVER if hover else self.CLR_BTN_BG, rect, border_radius=8)
        pygame.draw.rect(self.screen, self.CLR_BTN_BORDER, rect, width=1, border_radius=8)
        self.screen.blit(tsurf, (rect.x + self.BTN_PAD_X, rect.y + self.BTN_PAD_Y))

        self.context.fish_button_rect = rect

    # ---------------- window and contents ----------------
    def _draw_window(self, world) -> None:
        # Modal chrome + strict gating
        win_rect, content_view, close_rect, title_surf = self.modal.open("Fish")
        self.context.ui_modal_active = True
        self.context.ui_modal_whitelist = [win_rect, close_rect]
        self.context.fish_window_rect = win_rect
        self.context.fish_close_rect = close_rect

        self.screen.blit(title_surf, (win_rect.x + self.WIN_PAD, win_rect.y + self.WIN_PAD))

        # list viewport
        raw_view = pygame.Rect(
            content_view.x,
            content_view.y + self.TITLE_GAP,
            content_view.w - self.SCROLL_W - self.SCROLL_PAD,
            content_view.h - self.TITLE_GAP,
        )
        # guard: ensure positive drawing area
        view_w = max(self.CARD_W, raw_view.w)
        view_h = max(self.CARD_H + 1, raw_view.h)
        view = pygame.Rect(raw_view.x, raw_view.y, view_w, view_h)

        track = pygame.Rect(view.right + self.SCROLL_PAD, view.y, self.SCROLL_W, view.h)
        self._list_view_rect = view
        self._scroll_track_rect = track

        fishes = self._collect_fish(world)

        # scroll extent
        cols, rows, grid_x = self.grid.measure(view.w, len(fishes))
        content_h = rows * self.CARD_H + max(0, rows - 1) * self.GRID_GUTTER_Y

        # ScrollBox API (sync + on_wheel)
        self.scroll.sync(content_h, view.h)

        wheel = getattr(self.context, "ui_wheel_event", None)
        if wheel:
            wx, wy = wheel.get("x", 0), wheel.get("y", 0)
            if view.collidepoint(wx, wy) or track.collidepoint(wx, wy):
                dy = int(wheel.get("dy", 0))
                delta_px = -dy * getattr(self.scroll, "wheel_step_px", 60)
                self.scroll.on_wheel(delta_px)
            self.context.ui_wheel_event = None

        # clip to list viewport
        old_clip = self.screen.get_clip()
        self.screen.set_clip(view)
        yoff = -int(self.scroll.scroll_y)

        if not fishes:
            # helpful empty state
            hint = self._font(self._ui_sizes()["meta"]).render("No fish found", True, (150, 160, 180))
            hx = view.x + (view.w - hint.get_width()) // 2
            hy = view.y + (view.h - hint.get_height()) // 2
            self.screen.blit(hint, (hx, hy))
        else:
            for idx, info in enumerate(fishes):
                cx, cy = self.grid.pos(idx, cols, grid_x)
                card_rect = pygame.Rect(view.x + cx, view.y + cy + yoff, self.CARD_W, self.CARD_H)
                self._draw_card(card_rect, info)

        self.screen.set_clip(old_clip)

        # draw scrollbar
        self.scroll.draw_scrollbar(self.screen, track)

    def _collect_fish(self, world) -> list[dict]:
        """Be resilient to different ECS shapes; return list of fish info dicts."""
        infos = []

        # Helper to fetch a component for an entity, across ECS variants
        def _fetch(e, comp):
            # try world.get_component(e, Comp)
            gc = getattr(world, "get_component", None)
            if callable(gc):
                try:
                    got = gc(e, comp)
                    if got is not None:
                        return got
                except Exception:
                    pass
            # try world.components[Comp][e]
            comps = getattr(world, "components", None)
            if isinstance(comps, dict) and comp in comps:
                try:
                    return comps[comp].get(e)
                except Exception:
                    pass
            return None

        # 1) Best path: entities_with(Species, Sprite)
        ew = getattr(world, "entities_with", None)
        if callable(ew):
            try:
                for e in ew(Species, Sprite):
                    sp = _fetch(e, Species)
                    spr = _fetch(e, Sprite)
                    if not (sp and spr):
                        continue
                    infos.append(dict(
                        eid=e,
                        species=sp,
                        sprite=spr,
                        age=_fetch(e, Age),
                        brain=_fetch(e, Brain),
                        hunger=_fetch(e, Hunger),
                        health=_fetch(e, Health),
                    ))
                if infos:
                    return infos
            except Exception:
                pass

        # 2) Fallback: from components maps
        comps = getattr(world, "components", None)
        if isinstance(comps, dict):
            source_ids = None
            if Species in comps and isinstance(comps[Species], dict):
                source_ids = list(comps[Species].keys())
            elif Sprite in comps and isinstance(comps[Sprite], dict):
                source_ids = list(comps[Sprite].keys())
            if source_ids:
                for e in source_ids:
                    sp = _fetch(e, Species)
                    spr = _fetch(e, Sprite)
                    if not (sp and spr):
                        continue
                    infos.append(dict(
                        eid=e,
                        species=sp,
                        sprite=spr,
                        age=_fetch(e, Age),
                        brain=_fetch(e, Brain),
                        hunger=_fetch(e, Hunger),
                        health=_fetch(e, Health),
                    ))
                if infos:
                    return infos

        # 3) Last resort: iterate any entity list the world exposes
        for attr in ("entities", "all_entities", "entity_ids"):
            seq = getattr(world, attr, None)
            if not seq:
                continue
            try:
                for e in list(seq):
                    sp = _fetch(e, Species)
                    spr = _fetch(e, Sprite)
                    if not (sp and spr):
                        continue
                    infos.append(dict(
                        eid=e,
                        species=sp,
                        sprite=spr,
                        age=_fetch(e, Age),
                        brain=_fetch(e, Brain),
                        hunger=_fetch(e, Hunger),
                        health=_fetch(e, Health),
                    ))
            except Exception:
                pass
            if infos:
                return infos

        return infos  # possibly empty, caller will show "No fish found"

    def _draw_card(self, rect: pygame.Rect, info: dict) -> None:
        pygame.draw.rect(self.screen, self.CLR_CARD_BG, rect, border_radius=self.CARD_RADIUS)
        pygame.draw.rect(self.screen, self.CLR_CARD_BORDER, rect, width=1, border_radius=self.CARD_RADIUS)

        tbox = pygame.Rect(rect.x + self.CARD_PAD, rect.y + self.CARD_PAD, self.SPRITE_BOX, self.SPRITE_BOX)

        stage = getattr(info.get("age"), "stage", "Adult") if info.get("age") else "Adult"
        brain = getattr(info.get("brain"), "state", "Cruise") if info.get("brain") else "Cruise"
        dead = (brain == "Dead")

        if stage == "Egg":
            tw, th = 72, 72
            surf = self.thumbs.get(info["sprite"], info.get("age"), info.get("brain"), info.get("health"), self.SPRITE_BOX)
        else:
            if stage == "Juvenile":
                tw, th = 36, 24
            else:
                tw, th = 72, 48
            surf = self.thumbs.get(info["sprite"], info.get("age"), info.get("brain"), info.get("health"), self.SPRITE_BOX)

        # center in box based on returned surf size
        if surf is not None and isinstance(surf, pygame.Surface):
            tw, th = surf.get_width(), surf.get_height()
            sx = tbox.x + (tbox.w - tw) // 2
            sy = tbox.y + (tbox.h - th) // 2
            self.screen.blit(surf, (sx, sy))

        sizes = self._ui_sizes()
        name_font = self._font(sizes["name"])
        meta_font = self._font(sizes["meta"])

        species: Species = info["species"]
        name = species.display_name if getattr(species, "display_name", None) else species.species_id
        name_surf = name_font.render(name, True, self.CLR_TEXT)
        self.screen.blit(name_surf, (rect.x + self.CARD_PAD + self.SPRITE_BOX + self.TEXT_LEFT, rect.y + self.CARD_PAD))

        meta_y = rect.y + self.CARD_PAD + 28
        age: Optional[Age] = info.get("age")
        if age:
            stage_surf = meta_font.render(f"Stage: {age.stage}", True, self.CLR_SUB)
            self.screen.blit(stage_surf, (rect.x + self.CARD_PAD + self.SPRITE_BOX + self.TEXT_LEFT, meta_y))
            meta_y += self.GAP

        bar_x = rect.x + self.CARD_PAD + self.SPRITE_BOX + self.TEXT_LEFT
        bar_y = rect.y + rect.h - self.CARD_PAD - self.BAR_H * 2 - self.BAR_GAP

        self._draw_bar(bar_x, bar_y, rect.w - (bar_x - rect.x) - self.CARD_PAD, self.BAR_H,
                       info.get("hunger"), self.CLR_BAR_HUNGER, key="hunger")
        bar_y += self.BAR_H + self.BAR_GAP
        self._draw_bar(bar_x, bar_y, rect.w - (bar_x - rect.x) - self.CARD_PAD, self.BAR_H,
                       info.get("health"), self.CLR_BAR_HEALTH, key="health")

    def _draw_bar(self, x: int, y: int, w: int, h: int, comp, clr_fill, key: str) -> None:
        pygame.draw.rect(self.screen, self.CLR_BAR_BG, pygame.Rect(x, y, w, h), border_radius=4)
        if comp is None:
            return
        if key == "hunger":
            val, maxv = float(getattr(comp, "hunger", 0.0)), float(getattr(comp, "hunger_max", 1.0))
        else:
            val, maxv = float(getattr(comp, "value", 0.0)), float(getattr(comp, "max_value", 1.0))
        pct = 0.0 if maxv <= 0 else max(0.0, min(1.0, val / maxv))
        fw = int(w * pct)
        if fw > 0:
            pygame.draw.rect(self.screen, clr_fill, pygame.Rect(x, y, fw, h), border_radius=4)
