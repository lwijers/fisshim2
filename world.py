# world.py
from __future__ import annotations

from collections import defaultdict
from typing import Any, DefaultDict, Dict, Generator, Iterable, List, Optional, Set, Tuple, Type


class World:
    # Small enum-like aliases avoid magic strings in call sites
    PHASE_UPDATE = "update"
    PHASE_RENDER = "render"

    def __init__(self) -> None:
        # Monotonic entity id source
        self._next_entity_id: int = 1

        # Per-entity component storage:
        # {entity_id: {ComponentClass: component_instance}}
        self._components: Dict[int, Dict[Type[Any], Any]] = {}

        # Creation order of entities; used to produce stable iteration order
        self.entities: List[int] = []

        # Reverse index for fast queries:
        # {ComponentClass: set(entity_id, ...)}
        self._component_index: DefaultDict[Type[Any], Set[int]] = defaultdict(set)

        # Systems are callables with `update(world, dt)`; separated by phase
        self._update_systems: List[Any] = []
        self._render_systems: List[Any] = []

    # -------------------------------------------------------------------------
    # Entity management
    # -------------------------------------------------------------------------
    def create_entity(self) -> int:
        """Create an empty entity and return its id."""
        eid = self._next_entity_id
        self._next_entity_id += 1
        self.entities.append(eid)
        self._components[eid] = {}  # empty component map
        return eid

    def destroy_entity(self, entity: int) -> None:
        """Remove an entity, all its components, and update indices."""
        comps = self._components.pop(entity, None)
        if comps:
            # Remove the entity from all component indices it participated in
            for ctype in comps:
                idx = self._component_index.get(ctype)
                if idx is not None:
                    idx.discard(entity)
                    if not idx:
                        # Keep the reverse index tidy (optional)
                        self._component_index.pop(ctype, None)
        # Remove from stable order list
        try:
            self.entities.remove(entity)
        except ValueError:
            # Already absent (defensive)
            pass

    # -------------------------------------------------------------------------
    # Component management
    # -------------------------------------------------------------------------
    def add_component(self, entity: int, component: Any) -> None:
        """Attach/replace a component and update the reverse index."""
        bucket = self._components.get(entity)
        if bucket is None:
            # Unknown entity: ignore (or raise if you prefer strictness)
            return
        ctype = type(component)
        bucket[ctype] = component
        self._component_index[ctype].add(entity)

    def remove_component(self, entity: int, component_type: Type[Any]) -> None:
        """Detach a component and update the reverse index (if present)."""
        bucket = self._components.get(entity)
        if not bucket or component_type not in bucket:
            return
        del bucket[component_type]
        idx = self._component_index.get(component_type)
        if idx is not None:
            idx.discard(entity)
            if not idx:
                self._component_index.pop(component_type, None)

    def get_component(self, entity: int, component_type: Type[Any]) -> Optional[Any]:
        """Fetch a single component; returns None if missing."""
        bucket = self._components.get(entity)
        return None if bucket is None else bucket.get(component_type)

    def has_components(self, entity: int, *component_types: Type[Any]) -> bool:
        """Quick check that an entity has all of the given components."""
        bucket = self._components.get(entity)
        if not bucket:
            return False
        return all(ct in bucket for ct in component_types)

    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------
    def entities_with(self, *component_types: Type[Any]) -> Generator[int, None, None]:
        """
        Yield entity ids that have all requested component types.
        Uses the reverse index to intersect sets (fast), then yields
        in entity creation order (stable updates).
        """
        if not component_types:
            # No filter — rare but supported
            yield from self.entities
            return

        # Pull the per-component index sets; short-circuit on missing/empty
        sets: List[Set[int]] = []
        get = self._component_index.get
        for ct in component_types:
            s = get(ct)
            if not s:
                return  # nothing matches at all
            sets.append(s)

        # Intersect smallest → largest for speed
        sets.sort(key=len)
        result: Set[int]
        if len(sets) == 1:
            # Single-component fast path: avoid copying into a new set
            result = sets[0]
        else:
            result = sets[0].intersection(*sets[1:])

        # Yield in deterministic creation order (important for stability)
        for eid in self.entities:
            if eid in result:
                yield eid

    # -------------------------------------------------------------------------
    # Systems
    # -------------------------------------------------------------------------
    def add_system(self, system: Any, phase: str = PHASE_UPDATE) -> None:
        """Register a system for the given phase ('update' or 'render')."""
        if phase == self.PHASE_RENDER:
            self._render_systems.append(system)
        else:
            # Default / anything else routes to update phase
            self._update_systems.append(system)

    def update(self, dt: float) -> None:
        """Run all update-phase systems."""
        for system in self._update_systems:
            system.update(self, dt)

    def render(self) -> None:
        """Run all render-phase systems (dt usually unused → pass 0.0)."""
        for system in self._render_systems:
            system.update(self, 0.0)
