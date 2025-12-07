# ecs/systems/ui/mouse_system.py
from __future__ import annotations
from typing import Optional, Iterable, Tuple
import pygame

LMB = 1
RMB = 3

class MouseSystem:
    """
    Mouse-up driven + Panels:
    - LMB-up: panels consume first; then toolbar toggles; then fish hit → open a panel.
    - RMB-up: close top-most panel if present, else global cancel for tools & legacy modals.
    """
    def __init__(self, context, screen, assets):
        self.context = context
        self.screen = screen
        self.assets = assets
        self._tank_entity: Optional[int] = None
        self._world = None
        self._placement = None
        self._panels = None  # PanelManagerSystem

    # wiring
    def set_tank(self, entity_id: int) -> None: self._tank_entity = entity_id
    def set_world_ref(self, world) -> None: self._world = world
    def set_placement(self, placement_system) -> None: self._placement = placement_system
    def set_panel_manager(self, panel_manager) -> None: self._panels = panel_manager

    # utils
    def _point_in_tank_screen(self, x: int, y: int) -> bool:
        sx = int(getattr(self.context, "tank_screen_x", 0))
        sy = int(getattr(self.context, "tank_screen_y", 0))
        sw = int(getattr(self.context, "tank_screen_w", self.screen.get_width()))
        sh = int(getattr(self.context, "tank_screen_h", self.screen.get_height()))
        return (sx <= x <= sx + sw) and (sy <= y <= sy + sh)

    def _deactivate_all_tools(self) -> None:
        if getattr(self.context, "feeding_enabled", False): self.context.feeding_enabled = False
        if getattr(self.context, "egging_enabled", False): self.context.egging_enabled = False

    def _clear_cursor_and_selection(self) -> None:
        ctx = self.context
        for name in ("active_tool", "cursor_tool", "selected_entity",
                     "selected_card", "selected_item", "hover_entity",
                     "hover_card", "hover_widget", "tooltip", "pending_action"):
            if hasattr(ctx, name): setattr(ctx, name, None)
        for name in ("dragging", "is_dragging", "is_panning", "rubberband_active"):
            if hasattr(ctx, name): setattr(ctx, name, False)
        if hasattr(ctx, "cursor_mode"): ctx.cursor_mode = "default"
        for name in ("ui_place_egg", "ui_drop_pellets", "ui_click", "ui_drag", "ui_hover"):
            if hasattr(ctx, name): setattr(ctx, name, None)

    def _cancel_all_ui(self, mx: int, my: int) -> None:
        self.context.ui_cancel = {"x": int(mx), "y": int(my), "button": RMB}
        self._deactivate_all_tools()
        self._clear_cursor_and_selection()
        for flag in ("show_fish_window", "show_fish_inspector"):
            if hasattr(self.context, flag): setattr(self.context, flag, False)

    def _hit_test_fish(self, mx: int, my: int) -> Optional[int]:
        rects: Iterable[Tuple[int, pygame.Rect]] = getattr(self.context, "fish_screen_rects", []) or []
        for eid, rect in reversed(list(rects)):
            if rect.collidepoint(mx, my):
                return eid
        return None

    # events
    def handle_mouse_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONUP:
            mx, my = pygame.mouse.get_pos()
            btn = getattr(event, "button", 0)
            if btn == RMB:
                # NEW: prefer closing the top-most panel if present
                if self._panels and hasattr(self._panels, "close_top_panel") and self._panels.close_top_panel():
                    self._deactivate_all_tools()  # why: consistent with cancel semantics
                    return
                self._cancel_all_ui(mx, my)
                return
            self._on_mouse_up(event)
        elif event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            self.context.ui_wheel_event = {"x": int(mx), "y": int(my), "dy": int(event.y)}

    def _on_mouse_up(self, event: pygame.event.Event) -> None:
        mx, my = event.pos
        if event.button != LMB:
            return

        # Panels consume first
        if self._panels and self._panels.consume_click(mx, my):
            return

        # Toolbar toggles
        feed_btn = getattr(self.context, "toolbar_button_rect", None)
        egg_btn  = getattr(self.context, "toolbar_egg_rect", None)
        fish_btn = getattr(self.context, "fish_button_rect", None)

        if feed_btn and feed_btn.collidepoint(mx, my):
            on = not bool(getattr(self.context, "feeding_enabled", False))
            self.context.feeding_enabled = on
            if on: self.context.egging_enabled = False
            return

        if egg_btn and egg_btn.collidepoint(mx, my):
            on = not bool(getattr(self.context, "egging_enabled", False))
            self.context.egging_enabled = on
            if on: self.context.feeding_enabled = False
            return

        if fish_btn and fish_btn.collidepoint(mx, my):
            self._deactivate_all_tools()
            show = bool(getattr(self.context, "show_fish_window", False))
            self.context.show_fish_window = not show
            self.context.show_fish_inspector = False
            return

        # Placement
        tool_on = bool(getattr(self.context, "feeding_enabled", False) or getattr(self.context, "egging_enabled", False))
        if tool_on and self._point_in_tank_screen(mx, my):
            if self._placement and hasattr(self._placement, "enqueue_click"):
                self._placement.enqueue_click(mx, my)
            return

        # Fish pick → open a floating panel
        if not tool_on and self._point_in_tank_screen(mx, my):
            hit = self._hit_test_fish(mx, my)
            if hit is not None and self._panels and self._world:
                self._deactivate_all_tools()
                self.context.show_fish_window = False
                self.context.show_fish_inspector = False
                self._panels.open_fish(self._world, hit, at=(mx, my))
            return

    def update(self, world, dt) -> None:
        return
