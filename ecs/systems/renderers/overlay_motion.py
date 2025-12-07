import pygame
from ecs.components.core.velocity_component import Velocity
from ecs.components.fish.steering_intent_component import SteeringIntent
def draw_velocity_arrow(screen, context, draw_x, draw_y, screen_w, screen_h, vel: Velocity):
    if not (vel and context.show_velocity_arrows): return
    end_x = draw_x + screen_w / 2 + vel.dx * float(context.ui.get("ui_velocity_arrow_scale", 0.5))
    end_y = draw_y + screen_h / 2 + vel.dy * float(context.ui.get("ui_velocity_arrow_scale", 0.5))
    pygame.draw.line(screen, (255, 255, 0),
        (draw_x + screen_w / 2, draw_y + screen_h / 2),
        (end_x, end_y), 1)
def draw_avoidance_arrow(screen, context, draw_x, draw_y, screen_w, screen_h, intent: SteeringIntent):
    if not (intent and context.show_avoidance_arrows): return
    ax = intent.dx * float(context.ui.get("ui_avoidance_arrow_scale", 40.0))
    ay = intent.dy * float(context.ui.get("ui_avoidance_arrow_scale", 40.0))
    pygame.draw.line(screen, (255, 100, 0),
        (draw_x + screen_w / 2, draw_y + screen_h / 2),
        (draw_x + screen_w / 2 + ax, draw_y + screen_h / 2 + ay), 1)
