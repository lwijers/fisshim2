# ecs/systems/ui/widgets/panel_manager_system.py
from __future__ import annotations
import pygame
from typing import List, Optional, Tuple, Dict, Any

from ecs.systems.ui.widgets.panel import InspectorPanel, PanelRenderer, PanelTheme
from ecs.systems.ui.widgets.thumb_provider import ThumbProvider
from ecs.systems.renderers.cache import SpriteCache  # same cache used elsewhere

# Components (normal runtime imports)
from ecs.components.core.sprite_component import Sprite
from ecs.components.fish.age_component import Age
from ecs.components.fish.brain_component import Brain
from ecs.components.fish.health_component import Health
from ecs.components.fish.species_component import Species
from ecs.components.fish.hunger_component import Hunger


class PanelManagerSystem:
    """
    Floating inspector panels manager (non-modal):
    - Panels snap to a compact top-left grid.
    - Drop/shift animation is visual-only; logical (x,y) stays on the grid.
    - **Portraits are cached per entity by stage**; on stage transition we rebuild once via ThumbProvider.
    - RMB close (top-most) supported via close_top_panel(); LMB hits handled by consume_click().
    """
    THUMB_BOX = 72

    def __init__(self, screen: pygame.Surface, assets, context):
        self.screen = screen
        self.assets = assets
        self.context = context
        self.theme = PanelTheme()
        self.renderer = PanelRenderer(screen, self.theme)
        self.thumbs = ThumbProvider(self.assets, self.context)

        if not hasattr(self.context, "ui_panels"):
            self.context.ui_panels: List[InspectorPanel] = []

        self._z_next = 1

        # Grid geometry
        self._grid_cell_w = max(self.theme.min_w, 260)
        self._grid_cell_h = 160
        self._grid_gap_x = 10
        self._grid_gap_y = 10
        self._grid_margin_x = 12
        self._grid_margin_y = 12
        self._grid_cols: Optional[int] = None
        self._grid_rows: Optional[int] = None

        # ---- NEW: portrait cache keyed by entity id ----
        # value: {"stage": str|None, "surf": pygame.Surface}
        self._portrait_cache: Dict[int, Dict[str, Any]] = {}

    # ---------- Public API ----------
    def open_fish(self, world, entity: int, at: Optional[Tuple[int, int]] = None) -> None:
        # Focus if already open
        for p in self.context.ui_panels:
            if p.kind == "fish" and p.entity == entity:
                p.z = self._z_alloc()
                return

        title = self._fish_title(world, entity)
        idx = len(self.context.ui_panels)
        tx, ty = self._grid_slot_xy(idx)

        panel = InspectorPanel(
            id=self._z_next, kind="fish", entity=entity, title=title,
            x=tx, y=ty, w=self._grid_cell_w, h=self._grid_cell_h, z=self._z_alloc(),
            render_body=lambda surf, body: self._render_fish_body(world, entity, surf, body),
        )
        panel.tx, panel.ty = tx, ty

        # Visual drop (logical x,y already snapped for tests)
        now = pygame.time.get_ticks()
        panel.anim_kind = "drop"
        panel.ax0, panel.ay0 = tx, ty - 28
        panel.anim_start_ms = now
        panel.anim_dur_ms = 220

        self.context.ui_panels.append(panel)

        # Seed cache on open (so first draw is correct without waiting a frame)
        self._ensure_portrait(world, entity)

    def consume_click(self, mx: int, my: int) -> bool:
        if not self.context.ui_panels:
            return False
        for p in sorted(self.context.ui_panels, key=lambda p: p.z, reverse=True):
            rect = pygame.Rect(p.x, p.y, p.w, p.h)
            if rect.collidepoint(mx, my):
                if p.close_rect and p.close_rect.collidepoint(mx, my):
                    self._remove_panel(p)
                    return True
                p.z = self._z_alloc()
                return True
        return False

    def close_top_panel(self) -> bool:
        if not self.context.ui_panels:
            return False
        top = max(self.context.ui_panels, key=lambda p: p.z)
        self._remove_panel(top)
        return True

    # Optional external invalidation if some system wants to force-refresh
    def invalidate_thumb(self, eid: int) -> None:
        self._portrait_cache.pop(int(eid), None)

    # ---------- Internal: Grid ----------
    def _z_alloc(self) -> int:
        self._z_next += 1
        return self._z_next

    def _compute_grid_dims(self) -> None:
        sw, sh = self.screen.get_size()
        usable_w = max(0, sw - self._grid_margin_x * 2)
        usable_h = max(0, sh - self._grid_margin_y * 2)
        cols = max(1, (usable_w + self._grid_gap_x) // (self._grid_cell_w + self._grid_gap_x))
        rows = max(1, (usable_h + self._grid_gap_y) // (self._grid_cell_h + self._grid_gap_y))
        self._grid_cols = int(cols)
        self._grid_rows = int(rows)

    def _grid_slot_xy(self, idx: int) -> Tuple[int, int]:
        if self._grid_cols is None or self._grid_rows is None:
            self._compute_grid_dims()
        col = idx % self._grid_cols
        row = idx // self._grid_cols
        x = self._grid_margin_x + col * (self._grid_cell_w + self._grid_gap_x)
        y = self._grid_margin_y + row * (self._grid_cell_h + self._grid_gap_y)
        return int(x), int(y)

    def _reflow_grid(self) -> None:
        if not self.context.ui_panels:
            return
        self._compute_grid_dims()
        ordered = sorted(self.context.ui_panels, key=lambda p: p.id)
        now = pygame.time.get_ticks()
        for i, p in enumerate(ordered):
            tx, ty = self._grid_slot_xy(i)
            moved = (getattr(p, "tx", p.x) != tx) or (getattr(p, "ty", p.y) != ty)
            if moved:
                p.anim_kind = "shift"
                p.ax0, p.ay0 = p.x, p.y
                p.anim_start_ms = now
                p.anim_dur_ms = 200
            p.tx, p.ty = tx, ty
            p.x, p.y = tx, ty
        self.context.ui_panels[:] = ordered

    # ---------- Render ----------
    def update(self, world, dt: float) -> None:
        if not self.context.ui_panels:
            return

        base = int((getattr(self.context, "ui", {}) or {}).get("ui_font_size", 14))
        title_px = base + 6
        now = pygame.time.get_ticks()

        for p in sorted(self.context.ui_panels, key=lambda p: p.z):
            eff_x, eff_y = p.x, p.y
            if getattr(p, "anim_kind", None) and getattr(p, "anim_start_ms", None) is not None:
                t = (now - p.anim_start_ms) / max(1, getattr(p, "anim_dur_ms", 1))
                if t >= 1.0:
                    p.anim_kind = None
                    p.ax0 = p.ay0 = None
                    p.anim_start_ms = None
                    p.anim_dur_ms = 0
                else:
                    u = 1.0 - (1.0 - t) ** 3
                    ax0 = getattr(p, "ax0", p.x)
                    ay0 = getattr(p, "ay0", p.y)
                    eff_x = int(ax0 + (p.tx - ax0) * u)
                    eff_y = int(ay0 + (p.ty - ay0) * u)

            r = pygame.Rect(eff_x, eff_y, p.w, p.h)
            self.renderer.clamp_to_screen(r, self.screen.get_size())

            ox, oy = p.x, p.y
            p.x, p.y = r.x, r.y
            self.renderer.draw(p, title_px)
            p.x, p.y = ox, oy

    # ---------- Helpers & Body Rendering ----------
    def _remove_panel(self, p: InspectorPanel) -> None:
        try:
            self.context.ui_panels.remove(p)
        except ValueError:
            return
        # drop portrait cache entry so reopening starts clean
        self._portrait_cache.pop(int(getattr(p, "entity", -1)), None)
        self._reflow_grid()

    def _fish_title(self, world, eid: int) -> str:
        sp: Optional[Species] = world.get_component(eid, Species)
        return str(sp.display_name) if sp and getattr(sp, "display_name", None) else "Fish"

    def _fit_aspect(self, w: int, h: int, box_px: int) -> Tuple[int, int]:
        if w <= 0 or h <= 0 or box_px <= 0:
            return box_px, box_px
        scale = min(box_px / float(w), box_px / float(h))
        return int(w * scale), int(h * scale)

    # ---- Portrait cache keyed by stage -------------------------------------
    def _current_stage_and_brain(self, world, eid: int) -> Tuple[Optional[str], Optional[str]]:
        age: Optional[Age] = world.get_component(eid, Age)
        brain: Optional[Brain] = world.get_component(eid, Brain)
        stage = getattr(age, "stage", None)
        brain_state = getattr(brain, "state", None)
        return stage, brain_state

    def _ensure_portrait(self, world, eid: int) -> pygame.Surface:
        """
        Ensure we have a portrait surface cached for the entity's **current stage**.
        If stage changed versus cache, rebuild once via ThumbProvider to mirror card rules.
        """
        stage, brain_state = self._current_stage_and_brain(world, eid)
        cached = self._portrait_cache.get(int(eid))

        if cached and cached.get("stage") == stage:
            return cached["surf"]

        # Build through ThumbProvider to match your card behavior.
        # Try the most specific signature first; fall back gracefully.
        surf: Optional[pygame.Surface] = None
        try:
            surf = self.thumbs.card_thumb(world, eid, self.THUMB_BOX, stage=stage, brain_state=brain_state)
        except TypeError:
            try:
                surf = self.thumbs.card_thumb(world, eid, self.THUMB_BOX)
            except Exception:
                surf = None
        except Exception:
            surf = None

        # If ThumbProvider doesn't have card_thumb, try common alternates
        if surf is None and hasattr(self.thumbs, "build_fish_thumb"):
            try:
                surf = self.thumbs.build_fish_thumb(world, eid, self.THUMB_BOX, stage=stage, brain_state=brain_state)
            except TypeError:
                try:
                    surf = self.thumbs.build_fish_thumb(world, eid, self.THUMB_BOX)
                except Exception:
                    surf = None
            except Exception:
                surf = None

        if surf is None and hasattr(self.thumbs, "thumb_for_entity"):
            try:
                surf = self.thumbs.thumb_for_entity(world, eid, self.THUMB_BOX, stage=stage, brain_state=brain_state)
            except TypeError:
                try:
                    surf = self.thumbs.thumb_for_entity(world, eid, self.THUMB_BOX)
                except Exception:
                    surf = None
            except Exception:
                surf = None

        # Final fallback: scale species/sprite base so we always show something.
        if surf is None:
            sp: Optional[Species] = world.get_component(eid, Species)
            spr: Optional[Sprite] = world.get_component(eid, Sprite)
            key = getattr(spr, "image", None) or getattr(sp, "species_id", None)
            base = self.assets.get(key) if key else None
            if not isinstance(base, pygame.Surface):
                base = pygame.Surface((self.THUMB_BOX, self.THUMB_BOX), pygame.SRCALPHA)
                base.fill((60, 60, 60, 255))
            bw, bh = base.get_size()
            tw, th = self._fit_aspect(bw, bh, self.THUMB_BOX)
            surf = pygame.transform.smoothscale(base, (tw, th))

        # Store/replace cache
        self._portrait_cache[int(eid)] = {"stage": stage, "surf": surf}
        return surf

    def _render_fish_body(self, world, eid: int, surf: pygame.Surface, body: pygame.Rect) -> None:
        """
        Left column: 72x72 portrait (cached by stage, rebuilt via ThumbProvider on change).
        Right column: quick facts.
        """
        # Portrait (cached by stage)
        thumb = self._ensure_portrait(world, eid)
        tw, th = thumb.get_size()
        thumb_x = body.x
        thumb_y = body.y + max(0, (self.THUMB_BOX - th) // 2)
        surf.blit(thumb, (thumb_x, thumb_y))

        # Info column
        pad = 10
        info_x = body.x + self.THUMB_BOX + pad
        info_w = max(0, body.w - self.THUMB_BOX - pad)
        info_rect = pygame.Rect(info_x, body.y, info_w, body.h)

        base = int((getattr(self.context, "ui", {}) or {}).get("ui_font_size", 14))
        font = self.renderer.font(base)

        sp: Optional[Species] = world.get_component(eid, Species)
        age: Optional[Age] = world.get_component(eid, Age)
        br: Optional[Brain] = world.get_component(eid, Brain)
        hp: Optional[Health] = world.get_component(eid, Health)
        hg: Optional[Hunger] = world.get_component(eid, Hunger)

        def _fmt_pct(v, mx) -> str:
            try:
                return f"{int(round(100.0 * float(v) / max(1.0, float(mx))))}%"
            except Exception:
                return "-"

        lines = [
            f"Species: {getattr(sp, 'display_name', 'Unknown')}",
            f"Stage:   {getattr(age, 'stage', 'Unknown')}",
            f"Age:     {int(getattr(age, 'age', 0.0))}/{int(getattr(age, 'lifespan', 0.0))}",
            f"Health:  {int(getattr(hp, 'value', 0.0))}/{int(getattr(hp, 'max_value', 0.0))}",
            f"Hunger:  {int(getattr(hg, 'hunger', 0.0))}/{int(getattr(hg, 'hunger_max', 100.0))} ({_fmt_pct(getattr(hg,'hunger',0.0), getattr(hg,'hunger_max',100.0))})",
            f"Brain:   {getattr(br, 'state', 'Unknown')}",
        ]

        y = info_rect.y
        for text in lines:
            s = font.render(text, True, (230, 235, 245))
            surf.blit(s, (info_rect.x, y))
            y += s.get_height() + 4
