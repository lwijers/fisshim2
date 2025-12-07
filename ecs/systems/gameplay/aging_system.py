# ecs/systems/aging_system.py
from ecs.components.fish.age_component import Age
from ecs.components.fish.motion_component import MotionParams
from ecs.components.fish.health_component import Health
from ecs.components.tags.dead_component import DeadFlag
from ecs.components.tags.affected_by_gravity import AffectedByGravity  # used to drop eggs
# NOTE: Do not assign to names like DeadFlag inside functions; we only import & use them.

class AgingSystem:
    """
    - Eggs: accumulate pre-hatch time; lifespan/aging begin at hatching (age=0).
    - Post-hatch: juvenile/adult/senior speed scaling and elder health decay.
    - Optional hard death at lifespan.
    Config (data/aging.json):
      - elder_threshold_ratio
      - juvenile_threshold_ratio
      - elder_speed_multiplier_min
      - juvenile_speed_multiplier_min
      - elder_health_decay_at_max_per_sec
      - hard_death_at_lifespan
      - egg_duration_sec (preferred)
      - egg_threshold_ratio (fallback if no seconds set)
    """
    def __init__(self, context):
        self.context = context
        cfg = context.aging or {}

        # Stage thresholds (post-hatch age/lifespan ratios)
        self.r_elder = float(cfg.get("elder_threshold_ratio", 0.80))
        self.r_juv   = float(cfg.get("juvenile_threshold_ratio", 0.15))

        # Speed multipliers (ramps)
        self.min_elder = float(cfg.get("elder_speed_multiplier_min", 0.70))
        self.min_juv   = float(cfg.get("juvenile_speed_multiplier_min", 0.85))

        # Elder decay & hard death
        self.elder_hdecay = float(cfg.get("elder_health_decay_at_max_per_sec", 0.04))
        self.hard_death   = bool(cfg.get("hard_death_at_lifespan", True))

        # Egg timing
        self.egg_duration_sec_cfg = cfg.get("egg_duration_sec", None)
        self.egg_ratio_cfg = cfg.get("egg_threshold_ratio", None)

    # ---- helpers -------------------------------------------------------------

    def _egg_hatch_seconds(self, lifespan: float) -> float:
        # Prefer absolute seconds
        val = self.egg_duration_sec_cfg
        if val is not None:
            try:
                return max(0.0, float(val))
            except Exception:
                pass
        # Fallback: ratio of lifespan
        r = self.egg_ratio_cfg
        if r is not None:
            try:
                r = max(0.0, min(1.0, float(r)))
                return max(0.0, lifespan * r)
            except Exception:
                pass
        # Default if no config given
        return 8.0

    def _speed_mult_for_ratio(self, r: float) -> float:
        # Juvenile ramp: [0 .. r_juv] => min_juv → 1
        if r <= self.r_juv:
            if self.r_juv <= 1e-6:
                return 1.0
            t = max(0.0, min(1.0, r / self.r_juv))
            return self.min_juv + (1.0 - self.min_juv) * t
        # Elder ramp: [r_elder .. 1] => 1 → min_elder
        if r >= self.r_elder:
            span = max(1e-6, (1.0 - self.r_elder))
            t = max(0.0, min(1.0, (r - self.r_elder) / span))
            return 1.0 + (self.min_elder - 1.0) * t
        # Adult
        return 1.0

    def _elder_health_decay_per_sec(self, r: float, health_max: float) -> float:
        if r < self.r_elder or self.elder_hdecay <= 0.0:
            return 0.0
        span = max(1e-6, (1.0 - self.r_elder))
        t = (r - self.r_elder) / span  # 0..1
        return health_max * (self.elder_hdecay * t)

    def _update_stage_from_ratio(self, age_cmp: Age, ratio: float) -> None:
        if ratio < self.r_juv:
            stage = "Juvenile"
        elif ratio >= self.r_elder:
            stage = "Senior"
        else:
            stage = "Adult"
        if age_cmp.stage != stage:
            age_cmp.stage = stage

    # ---- ECS entry -----------------------------------------------------------

    def update(self, world, dt: float):
        if dt <= 0.0:
            return

        for e in world.entities_with(Age):
            # Skip dead — DeadState/Gravity handles their presentation/motion.
            if world.get_component(e, DeadFlag):
                continue

            age = world.get_component(e, Age)

            # EGG PHASE: accumulate pre-hatch; no lifespan aging yet
            if age.stage == "Egg":
                age.pre_hatch += dt

                # Ensure eggs fall if GravitySystem is in use
                if world.get_component(e, AffectedByGravity) is None:
                    world.add_component(e, AffectedByGravity(speed=float(
                        (self.context.balancing or {}).get("egg_fall_speed", 55.0)
                    )))

                hatch_after = self._egg_hatch_seconds(age.lifespan)
                if age.pre_hatch >= hatch_after:
                    # Hatch now → start real aging from 0
                    age.stage = "Juvenile"
                    age.age = 0.0
                    # Remove gravity so the fish can swim normally
                    world.remove_component(e, AffectedByGravity)
                continue  # nothing else while egg

            # POST-HATCH: advance age & compute ratio
            age.age += dt
            ratio = max(0.0, age.age / max(1e-6, age.lifespan))

            # Stage label
            self._update_stage_from_ratio(age, ratio)

            # Speed scaling by life stage
            mp = world.get_component(e, MotionParams)
            if mp is not None:
                if not hasattr(mp, "base_max_speed"):
                    mp.base_max_speed = float(mp.max_speed)
                mp.max_speed = mp.base_max_speed * self._speed_mult_for_ratio(ratio)

            # Elder health decay
            h = world.get_component(e, Health)
            if h is not None:
                h.value -= self._elder_health_decay_per_sec(ratio, h.max_value) * dt
                if h.value < 0:
                    h.value = 0

            # Optional hard death at lifespan
            if self.hard_death and age.age >= age.lifespan:
                if not world.get_component(e, DeadFlag):
                    world.add_component(e, DeadFlag())
                # NEW: make the biological stage reflect death
                age.stage = "Dead"
