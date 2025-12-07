# # ecs/systems/ui/fish_info_system.py
# import pygame
# from typing import Optional
#
# from ecs.systems.ui.widgets.modal_window import ModalWindow
# from ecs.components.fish.age_component import Age
# from ecs.components.fish.health_component import Health
# from ecs.components.fish.species_component import Species
#
# class FishInfoSystem:
#     """
#     Opens a modal info card when `context.show_fish_info` is True and
#     `context.selected_entity` is set. Closes via RMB/ESC (handled by ModalWindow).
#     """
#     PAD_X = 18
#     PAD_Y = 10
#     LINE = 26
#
#     def __init__(self, screen: pygame.Surface, assets, context):
#         self.screen = screen
#         self.assets = assets
#         self.context = context
#         self.modal = ModalWindow(screen, context)
#         self._font_small = pygame.font.SysFont("arial", 16)
#         self._font_med = pygame.font.SysFont("arial", 18)
#
#     def _get(self, world, ent, comp_type):
#         try:
#             return world.get_component(ent, comp_type)
#         except Exception:
#             try:
#                 return world.components.get(comp_type, {}).get(ent)
#             except Exception:
#                 return None
#
#     def update(self, world, dt: float) -> None:
#         if not getattr(self.context, "show_fish_info", False):
#             return
#         ent = getattr(self.context, "selected_entity", None)
#         if ent is None:
#             return
#
#         species: Optional[Species] = self._get(world, ent, Species)
#         age: Optional[Age] = self._get(world, ent, Age)
#         health: Optional[Health] = self._get(world, ent, Health)
#
#         title = (species.display_name if (species and getattr(species, "display_name", None)) else "Fish")
#         win_rect, content_view, close_rect, title_surf = self.modal.open(title)
#
#         x = content_view.x + self.PAD_X
#         y = content_view.y + self.PAD_Y
#
#         lines = []
#         if species:
#             lines.append(("Species ID:", species.species_id))
#         if age:
#             lines.append(("Stage:", getattr(age, "stage", "Unknown")))
#             lines.append(("Age:", f"{getattr(age, 'age', 0.0):.1f} / {getattr(age, 'lifespan', 0.0):.1f}"))
#         if health:
#             lines.append(("Health:", f"{getattr(health, 'value', 0.0):.0f}/{getattr(health, 'max_value', 0.0):.0f}"))
#
#         for label, value in lines:
#             lbl = self._font_small.render(str(label), True, (180, 190, 210))
#             val = self._font_med.render(str(value), True, (235, 240, 255))
#             self.screen.blit(lbl, (x, y))
#             self.screen.blit(val, (x + 120, y))
#             y += self.LINE
#
#         # Mirror modal state to show flag
#         if not self.modal.is_open():
#             self.context.show_fish_info = False
#
#     def handle_event(self, event: pygame.event.Event) -> None:
#         self.modal.handle_event(event)
