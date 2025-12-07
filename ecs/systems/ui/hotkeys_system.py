# ecs/systems/ui/hotkeys_system.py
import pygame

class HotkeysSystem:
    """
    Handles *only* key presses that toggle state or pause the sim.
    (No text entry and no spawning here.)
    """
    def __init__(self, context):
        self.context = context

    # InputRouter will call this
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        k = event.key

        if k == pygame.K_SPACE:
            self.context.toggle_pause()

        elif k == pygame.K_t:
            self.context.show_target_lines = not self.context.show_target_lines

        elif k == pygame.K_f:
            any_on = (self.context.show_fish_vision
                      or self.context.show_pellet_radius
                      or self.context.show_food_links)
            turn_on = not any_on
            self.context.show_fish_vision = turn_on
            self.context.show_pellet_radius = turn_on
            self.context.show_food_links = turn_on

        elif k == pygame.K_v:
            self.context.show_velocity_arrows = not self.context.show_velocity_arrows

        elif k == pygame.K_a:
            self.context.show_avoidance_arrows = not self.context.show_avoidance_arrows

        elif k == pygame.K_b:
            self.context.show_behavior_labels = not self.context.show_behavior_labels
            self.context.show_stats_bars = self.context.show_behavior_labels

        elif k == pygame.K_F1:
            self.context.show_debug_overlay = not self.context.show_debug_overlay

        elif k == pygame.K_o:
            # Swim-area overlay (drawn even if F1 panel is off)
            self.context.show_swim_floor_debug = not bool(
                getattr(self.context, "show_swim_floor_debug", False)
            )

        elif k == pygame.K_ESCAPE:
            # Respect debug_escape_quit like before (window close is handled in game.py)
            if getattr(self.context, "debug_escape_quit", False):
                self.context.running = False

    def update(self, world, dt: float) -> None:
        return
