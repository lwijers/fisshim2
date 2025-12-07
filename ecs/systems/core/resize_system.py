# ecs/systems/resize_system.py
from ecs.components.core.bounds_component import Bounds
from ecs.components.core.position_component import Position
from ecs.components.core.tank_component import Tank

class ResizeSystem:
    """
    Handles resizing the tank whenever the window is resized.

    - Uses logical tank size stored in context (logical_tank_w/h)
    - Computes new scale so the tank fits inside the screen
    - Updates tank entity position + size in screen space
    - Stores tank screen rect + scale on context
    """
    def __init__(self, context):
        self.context = context

    def update(self, world, dt):
        # Only do work when a resize was requested
        if not self.context.needs_resize:
            return

        new_w = self.context.new_screen_w
        new_h = self.context.new_screen_h

        logical_w = self.context.logical_tank_w
        logical_h = self.context.logical_tank_h

        # --- Compute scale so logical tank fits inside the window ---
        scale = min(new_w / logical_w, new_h / logical_h)
        self.context.tank_scale = scale

        tank_render_w = int(logical_w * scale)
        tank_render_h = int(logical_h * scale)

        # Center tank on screen
        tank_x = (new_w - tank_render_w) // 2
        tank_y = (new_h - tank_render_h) // 2

        # Store for anyone else who cares
        self.context.tank_screen_x = tank_x
        self.context.tank_screen_y = tank_y
        self.context.tank_screen_w = tank_render_w
        self.context.tank_screen_h = tank_render_h

        # --- Update the actual tank entity ---
        for tank in world.entities_with(Tank, Position, Bounds):
            pos = world.get_component(tank, Position)
            bounds = world.get_component(tank, Bounds)

            pos.x = tank_x
            pos.y = tank_y
            bounds.width = tank_render_w
            bounds.height = tank_render_h

        # Done for this resize event
        self.context.needs_resize = False
