# ecs/systems/ui/keyboard_system.py
from __future__ import annotations
import pygame
from typing import Optional
from ecs.systems.ui.debug import debug_controller as dbg

class KeyboardSystem:
    """
    Dispatcher-only:
      SPACE  -> pause/unpause
      L      -> begin label edit (if provided)
      F1     -> dbg.select_tab(ctx, "legend")
      F2     -> dbg.select_tab(ctx, "motion")
      F3     -> dbg.select_tab(ctx, "food")      # keeps target ON while active
      F4     -> dbg.select_tab(ctx, "behavior")
      F5     -> dbg.select_tab(ctx, "swim")
    """
    def __init__(self, context):
        self.context = context
        self._tank_eid: Optional[int] = None
        dbg.ensure_defaults(self.context)

    def set_world_ref(self, world): pass
    def set_tank(self, tank_entity: int): self._tank_eid = tank_entity
    def handle_textinput(self, event): pass
    def handle_keydown(self, event): self.handle_event(event)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        k = event.key

        if k == pygame.K_SPACE:
            tp = getattr(self.context, "toggle_pause", None)
            tp() if callable(tp) else setattr(self.context, "paused",
                   not bool(getattr(self.context, "paused", False)))
            return

        if k == pygame.K_l:
            begin = getattr(self.context, "begin_label_edit", None)
            if callable(begin): begin()
            else: setattr(self.context, "edit_tank_label",
                          not bool(getattr(self.context, "edit_tank_label", False)))
            return

        if   k == pygame.K_F1: dbg.select_tab(self.context, "legend");   return
        elif k == pygame.K_F2: dbg.select_tab(self.context, "motion");   return
        elif k == pygame.K_F3: dbg.select_tab(self.context, "food");     return
        elif k == pygame.K_F4: dbg.select_tab(self.context, "behavior"); return
        elif k == pygame.K_F5: dbg.select_tab(self.context, "swim");     return

    def update(self, world, dt): return
