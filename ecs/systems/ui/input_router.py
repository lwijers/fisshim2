# ecs/systems/ui/input_router.py
"""
InputRouter
-----------
Tiny dispatcher that forwards pygame events to keyboard and mouse subsystems.
Critically, it forwards TEXTINPUT while label editing is active so typing works.
"""

import pygame
from typing import Optional


class InputRouter:
    def __init__(self, keyboard_system, mouse_system):
        self.keyboard = keyboard_system
        self.mouse = mouse_system

    def handle_event(self, event: pygame.event.Event) -> None:
        et = event.type

        # --- Keyboard first: it may consume events (e.g., while editing label) ---
        if et == pygame.KEYDOWN:
            self.keyboard.handle_keydown(event)
            return  # nothing else should also “press the key”
        elif et == pygame.TEXTINPUT:
            self.keyboard.handle_textinput(event)
            return

        # --- Mouse events to mouse system ---
        if et in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL):
            self.mouse.handle_mouse_event(event)
            return

        # Everything else is ignored by input stack (resize handled in scene)
        return
