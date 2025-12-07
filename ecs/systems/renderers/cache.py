# ecs/systems/renderers/cache.py
"""
Lightweight sprite/label surface caches with optional variants:
- dead=True: grayscale + vertical flip (your existing "Dead" look)
- hflip=True: horizontal flip (ignored when dead=True)
- variant="senior": partial desaturate + warm tint (+ optional 1px outline)
All heavy pixel work happens once per unique cache key.

This version also publishes the final, already-transformed surface that the
sprite renderer blitted for each entity so the Fish window can reuse it
(eggs, juvenile scale, senior tint, dead flip+grey, etc.).
"""
from __future__ import annotations
from typing import Dict, Tuple, Any
import pygame

__all__ = ["SpriteCache", "LabelCache"]


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


class SpriteCache:
    """Cache scaled/variant sprite surfaces + share final blits to other systems."""
    _shared = None  # singleton holder

    def __init__(self, cache_limit: int = 256) -> None:
        self.cache_limit = int(cache_limit)
        # key: (id(img), w, h, dead, hflip, variant_key) -> Surface
        self._cache: Dict[Tuple[int, int, int, bool, bool, Tuple[Any, ...]], pygame.Surface] = {}
        # NEW: what the renderer actually blitted last for each entity
        self._final_by_entity: Dict[int, pygame.Surface] = {}

    @classmethod
    def shared(cls) -> "SpriteCache":
        """Access a shared SpriteCache instance for cross-system sharing."""
        if cls._shared is None:
            cls._shared = cls()
        return cls._shared

    # ---- "final surface" sharing API -----------------------------------------
    def put_final(self, entity_id: int, surf: pygame.Surface) -> None:
        self._final_by_entity[entity_id] = surf

    def get_final(self, entity_id: int):
        return self._final_by_entity.get(entity_id)

    # ---- maintenance ---------------------------------------------------------
    def clear(self) -> None:
        self._cache.clear()
        # also clear finals when scale/atlas changes so thumbs refresh
        self._final_by_entity.clear()

    # --- transforms -----------------------------------------------------------
    def _to_grayscale_and_vflip(self, surf: pygame.Surface) -> pygame.Surface:
        """Dead look: grayscale + vertical flip (once)."""
        gs = surf.copy().convert_alpha()
        width, height = gs.get_size()
        for x in range(width):
            for y in range(height):
                r, g, b, a = gs.get_at((x, y))
                if a:
                    lum = (r * 299 + g * 587 + b * 114) // 1000  # ITU-R 601-2
                    gs.set_at((x, y), (lum, lum, lum, a))
        return pygame.transform.flip(gs, False, True)

    def _apply_senior_style(
        self,
        base: pygame.Surface,
        *,
        desaturate: float,
        tint_rgb: Tuple[int, int, int],
        outline: bool,
        outline_px: int,
        outline_color: Tuple[int, int, int, int],
    ) -> pygame.Surface:
        """
        Senior look: partial desat toward grayscale, then warm tint.
        Optionally add a small outline (1 px) using a mask.
        """
        desaturate = _clamp01(float(desaturate))
        # 1) partial desaturation (per-pixel mix toward luminance)
        img = base.copy().convert_alpha()
        w, h = img.get_size()
        if desaturate > 0.0:
            for x in range(w):
                for y in range(h):
                    r, g, b, a = img.get_at((x, y))
                    if a:
                        lum = (r * 299 + g * 587 + b * 114) // 1000
                        r = int(r + (lum - r) * desaturate)
                        g = int(g + (lum - g) * desaturate)
                        b = int(b + (lum - b) * desaturate)
                        img.set_at((x, y), (r, g, b, a))
        # 2) warm tint (fast per-pixel multiply)
        tr, tg, tb = [max(0, min(255, int(v))) for v in tint_rgb]
        if (tr, tg, tb) != (255, 255, 255):
            for x in range(w):
                for y in range(h):
                    r, g, b, a = img.get_at((x, y))
                    if a:
                        r = (r * tr) // 255
                        g = (g * tg) // 255
                        b = (b * tb) // 255
                        img.set_at((x, y), (r, g, b, a))
        if not outline or outline_px <= 0:
            return img
        # 3) tiny outline via mask (cached once per key)
        outline_px = max(1, int(outline_px))
        oc = outline_color if len(outline_color) == 4 else (outline_color[0], outline_color[1], outline_color[2], 255)
        # Build a mask off the *desat+tinted* image alpha
        mask = pygame.mask.from_surface(img)
        edge = mask.to_surface(setcolor=oc, unsetcolor=(0, 0, 0, 0))
        final = pygame.Surface((w, h), pygame.SRCALPHA)
        # Four-neighbor "dilate" look
        final.blit(edge, (-outline_px, 0))
        final.blit(edge, ( outline_px, 0))
        final.blit(edge, (0, -outline_px))
        final.blit(edge, (0,  outline_px))
        # Foreground
        final.blit(img, (0, 0))
        return final

    # --- cache API ------------------------------------------------------------
    def _variant_key(self, variant: str, style: Dict[str, Any] | None) -> Tuple[Any, ...]:
        if variant != "senior":
            return ("normal",)
        style = style or {}
        des = float(style.get("desaturate", 0.6))
        tint = tuple(int(c) for c in style.get("tint", (235, 225, 215)))
        outline = bool(style.get("outline", True))
        opx = int(style.get("outline_px", 1))
        ocol = style.get("outline_color", (40, 35, 30, 255))
        if len(ocol) == 3:
            ocol = (int(ocol[0]), int(ocol[1]), int(ocol[2]), 255)
        else:
            ocol = tuple(int(c) for c in ocol)
        return ("senior", round(des, 3), tint, outline, opx, ocol)

    def get(
        self,
        img: pygame.Surface,
        w: int,
        h: int,
        *,
        dead: bool = False,
        hflip: bool = False,
        variant: str = "normal",
        senior_style: Dict[str, Any] | None = None,
    ) -> pygame.Surface:
        """
        Return a (possibly transformed) surface:
        - scaled to (w, h)
        - dead=True: grayscale + vertical flip
        - hflip=True: horizontal flip (ignored if dead=True)
        - variant="senior": partial desat + tint + optional outline
        """
        vkey = self._variant_key(variant, senior_style)
        key = (id(img), int(w), int(h), bool(dead), bool(hflip), vkey)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        # Base scale first
        scaled = pygame.transform.smoothscale(img, (int(w), int(h)))
        if dead:
            transformed = self._to_grayscale_and_vflip(scaled)
        else:
            # optional hflip relative to the base art
            base = pygame.transform.flip(scaled, True, False) if hflip else scaled
            if vkey[0] == "senior":
                # unpack style with defaults
                _, des, tint, outline, opx, ocol = vkey
                transformed = self._apply_senior_style(
                    base,
                    desaturate=des,
                    tint_rgb=tint,
                    outline=outline,
                    outline_px=opx,
                    outline_color=ocol,
                )
            else:
                transformed = base
        # Simple LRU-ish eviction
        if len(self._cache) >= self.cache_limit and self._cache:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = transformed
        return transformed


class LabelCache:
    """Cache rendered text surfaces for a given pygame Font."""
    def __init__(self, font) -> None:
        self.font = font
        self._cache: Dict[Tuple[str, Tuple[int, int, int]], pygame.Surface] = {}

    def clear(self) -> None:
        self._cache.clear()

    def get(self, text: str, color=(255, 255, 255)) -> pygame.Surface:
        key = (text, tuple(color))
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        surf = self.font.render(text, True, color)
        self._cache[key] = surf
        return surf
