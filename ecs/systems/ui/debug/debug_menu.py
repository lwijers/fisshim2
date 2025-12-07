# ecs/systems/ui/debug/debug_menu.py
import pygame

# ---------- Colors aligned with overlay drawers ----------
# Motion overlay
CLR_TARGET   = (255, 200, 0)   # target line
CLR_VELOCITY = (255, 255, 0)   # velocity arrow
CLR_AVOID    = (255, 100, 0)   # avoidance arrow

# Food overlay
CLR_VISION   = (0, 200, 255)   # vision ring
CLR_PELLET_R = (120, 230, 255) # pellet/seek radius
CLR_EAT_R    = (80, 200, 255)  # eat threshold radius

# Behavior overlay (bars)
CLR_BAR_BG   = (60, 60, 60)
CLR_HUNGER   = (255, 210, 80)
CLR_HEALTH   = (100, 255, 120)
# Age gradient endpoints
CLR_AGE_START = (120, 200, 255)
CLR_AGE_END   = (255, 140, 60)


class DebugMenu:
    """
    Small F-key debug panels (F1..F5). Text-only; overlays render elsewhere.

    IMPORTANT: Supports BOTH selection models:
      1) New: context.debug_panel_mode in {"legend","motion","food","behavior","swim", None}
      2) Legacy: show_debug_menu/show_motion_menu/show_food_menu/show_behavior_menu/show_swim_menu

    If debug_panel_mode is present, it takes precedence.
    Otherwise, it derives the mode from legacy flags.
    """

    PAD = 10
    GAP = 6
    LINE_GAP = 6
    BG = (0, 0, 0, 160)
    TXT = (235, 240, 255)

    def __init__(self, screen, context):
        self.screen = screen
        self.context = context
        self._fonts = {}

    # ---- font helpers ----
    def _font(self, px: int) -> pygame.font.Font:
        if px not in self._fonts:
            self._fonts[px] = pygame.font.SysFont("consolas, menlo, courier new, monospace", int(px))
        return self._fonts[px]

    def _ui_sizes(self):
        base = int(getattr(self.context, "ui", {}).get("ui_font_size", 14))
        return base + 2, base + 6  # body, title

    # ---- active mode resolution (new or legacy) ----
    def _active_mode(self):
        # Preferred: unified mode string
        mode = getattr(self.context, "debug_panel_mode", None)
        if mode in ("legend", "motion", "food", "behavior", "swim"):
            return mode

        # Legacy flags fallback (first true wins; you can tweak priority if needed)
        if bool(getattr(self.context, "show_debug_menu", False)):     return "legend"
        if bool(getattr(self.context, "show_motion_menu", False)):    return "motion"
        if bool(getattr(self.context, "show_food_menu", False)):      return "food"
        if bool(getattr(self.context, "show_behavior_menu", False)):  return "behavior"
        if bool(getattr(self.context, "show_swim_menu", False)):      return "swim"
        return None

    # ---- content builders ----
    def _build_items(self):
        mode = self._active_mode()
        if not mode:
            return []

        body_px, title_px = self._ui_sizes()
        f_body = self._font(body_px)
        f_title = self._font(title_px)

        items = []

        def t(text: str):
            return ("text", f_body.render(text, True, self.TXT), self.TXT)

        def title(text: str):
            return ("text", f_title.render(text, True, self.TXT), self.TXT)

        def line(label: str, color):
            return ("line", f_body.render(label, True, self.TXT), color)

        def gradient(label: str, c0, c1, bg=CLR_BAR_BG):
            return ("gradient", f_body.render(label, True, self.TXT), (c0, c1, bg))

        if mode == "legend":
            items += [
                title("F1 - LEGEND"),
                t("SPACE – Pause/Unpause"),
                t("L     – Edit tank label"),
                t("F1    – This Menu"),
                t("F2    – Movement debug (target/velocity/avoidance)"),
                t("F3    – Food debug (vision/pellet/link)"),
                t("F4    – Behavior labels & bars"),
                t("F5    – Toggle swim-area overlay"),
                t("F6    – Breeding (Not Implemented)"),
            ]
        elif mode == "motion":
            items += [
                title("F2 - MOVEMENT DEBUG"),
                line("Target line ----------------", CLR_TARGET),
                line("Velocity arrow -------------", CLR_VELOCITY),
                line("Avoidance arrows -----------", CLR_AVOID),
            ]
        elif mode == "food":
            items += [
                title("F3 - FOOD DEBUG"),
                line("Vision radius --------------", CLR_VISION),
                line("Pellet radius --------------", CLR_PELLET_R),
                line("Eat threshold --------------", CLR_EAT_R),
                line("Target line ----------------", CLR_TARGET),  # kept ON in food mode
            ]
        elif mode == "behavior":
            items += [
                title("F4 - BEHAVIOR OVERLAY"),
                line("Hunger bar -----------------", CLR_HUNGER),
                line("Health bar -----------------", CLR_HEALTH),
                gradient("Age bar --------------------", CLR_AGE_START, CLR_AGE_END, CLR_BAR_BG),
            ]
        elif mode == "swim":
            items += [
                title("F5 - SWIM AREA OVERLAY"),
                t("Visualizes fall floor vs swim bottom; see tank for colors."),
            ]
        return items

    # ---- render ----
    def _render_items(self, items):
        if not items:
            return
        pad = self.PAD
        line_gap = self.LINE_GAP

        # measure
        max_w = 0
        total_h = 0
        for kind, surf, _ in items:
            h = max(16, surf.get_height()) if kind in ("line", "gradient") else surf.get_height()
            total_h += h + line_gap
            max_w = max(max_w, surf.get_width())
        total_h -= line_gap
        box_w = pad * 2 + 16 + 8 + max_w
        box_h = pad * 2 + total_h

        x, y = 10, 10
        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill(self.BG)
        self.screen.blit(bg, (x, y))

        cy = y + pad
        for kind, surf, payload in items:
            if kind == "text":
                self.screen.blit(surf, (x + pad, cy))
                cy += surf.get_height() + line_gap
                continue

            swx = x + pad
            row_h = max(16, surf.get_height())
            swy = cy + (row_h // 2) - 1

            if kind == "line":
                color = payload
                pygame.draw.line(self.screen, color, (swx, swy), (swx + 16, swy), width=3)
                self.screen.blit(surf, (swx + 16 + 8, cy))
                cy += row_h + line_gap
            elif kind == "gradient":
                c0, c1, bgc = payload
                gw, gh = 32, 8
                gsurf = pygame.Surface((gw, gh), pygame.SRCALPHA)
                pygame.draw.rect(gsurf, bgc, (0, 0, gw, gh))
                for i in range(gw):
                    t = i / max(1, gw - 1)
                    r = int(c0[0] + (c1[0] - c0[0]) * t)
                    g = int(c0[1] + (c1[1] - c0[1]) * t)
                    b = int(c0[2] + (c1[2] - c0[2]) * t)
                    pygame.draw.line(gsurf, (r, g, b), (i, 0), (i, gh), 1)
                self.screen.blit(gsurf, (swx, swy - gh // 2))
                self.screen.blit(surf, (swx + gw + 8, cy))
                cy += row_h + line_gap

    # ---- ECS entry ----
    def update(self, world, dt):
        items = self._build_items()
        if not items:
            return
        self._render_items(items)
