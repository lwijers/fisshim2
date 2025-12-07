# file: ecs/systems/ui/widgets/thumb_provider.py
import pygame
from typing import Optional, Dict, Any, Tuple

from ecs.components.core.sprite_component import Sprite
from ecs.components.fish.age_component import Age
from ecs.components.fish.brain_component import Brain
from ecs.components.fish.health_component import Health
from ecs.systems.renderers.cache import SpriteCache


class ThumbProvider:
    """
    Card thumbnails:
      - Egg: show egg icon.
      - Juvenile: 50% of adult fit (aspect kept).
      - Adult: 100% fit (aspect kept).
      - Senior: desat/tint style (variant="senior").
      - Dead: grayscale + upside-down (dead=True), no hflip.
    """
    def __init__(self, assets, context) -> None:
        self.assets = assets
        self.context = context
        self.cache = SpriteCache.shared()
        # (image_key, stage, dead/alive, box_px) -> Surface
        self._local: Dict[Tuple[str, str, str, int], pygame.Surface] = {}

    def _senior_style_cfg(self) -> Dict[str, Any]:
        aging = getattr(self.context, "aging", {}) or {}
        return {
            "desaturate": float(aging.get("senior_desaturate", 0.6)),
            "tint": tuple(aging.get("senior_tint", [235, 225, 215])),
            "outline": bool(aging.get("senior_outline", True)),
            "outline_px": int(aging.get("senior_outline_px", 1)),
            "outline_color": tuple(aging.get("senior_outline_color", [40, 35, 30, 255])),
        }

    def _fit_aspect(self, bw: int, bh: int, box_px: int) -> Tuple[int, int]:
        # keep aspect; fit the larger dimension to box
        scale = min(float(box_px) / max(1.0, float(bw)),
                    float(box_px) / max(1.0, float(bh)))
        return max(1, int(round(bw * scale))), max(1, int(round(bh * scale)))

    def get(
        self,
        spr: Sprite,
        age: Optional[Age],
        brain: Optional[Brain],
        health: Optional[Health],
        box_px: int
    ) -> Optional[pygame.Surface]:
        stage = (getattr(age, "stage", "Adult") or "Adult").lower()
        is_egg = (stage == "egg")
        is_juvenile = (stage == "juvenile")
        is_senior = (stage == "senior")
        is_dead = (getattr(brain, "state", "") or "").lower() == "dead"

        key_img = spr.image_id if not is_egg else "egg"
        key = (key_img, stage, "dead" if is_dead else "alive", int(box_px))
        if key in self._local:
            return self._local[key]

        # ---- Egg: use egg sprite directly ----
        if is_egg:
            egg_img = self.assets.get("egg")
            if not isinstance(egg_img, pygame.Surface):
                return None
            w, h = egg_img.get_size()
            tw, th = self._fit_aspect(w, h, box_px)
            surf = self.cache.get(
                egg_img, tw, th,
                dead=False, hflip=False,
                variant="normal", senior_style=None
            )
            if surf is not None:
                self._local[key] = surf
            return surf

        # ---- Non-egg: base species sprite ----
        base = self.assets.get(spr.image_id)
        if not isinstance(base, pygame.Surface):
            return None

        # Adult fit inside box with aspect; e.g., 60x40 @ 72px -> 72x48
        adult_w, adult_h = self._fit_aspect(base.get_width(), base.get_height(), box_px)

        # Juvenile is exactly half of adult geometry
        final_w = max(1, adult_w // 2) if is_juvenile else adult_w
        final_h = max(1, adult_h // 2) if is_juvenile else adult_h

        # Senior style only when alive
        variant = "senior" if (is_senior and not is_dead) else "normal"
        style = self._senior_style_cfg() if variant == "senior" else None

        # Single-pass build so the first smoothscale matches expected size
        surf = self.cache.get(
            base,
            final_w, final_h,
            dead=is_dead,
            hflip=False,
            variant=variant,
            senior_style=style
        )
        if surf is not None:
            self._local[key] = surf
        return surf
