# ecs/systems/state_override_system.py
from ecs.components.fish.hunger_component import Hunger
from ecs.components.fish.behavior_tuning import BehaviorTuning
from ecs.components.fish.brain_component import Brain
from ecs.components.tags.dead_component import DeadFlag
from ecs.components.fish.age_component import Age

class StateOverrideSystem:
    """
    Global guardrails / hard overrides for FSM transitions.
    Priority (high → low):
      1) Death: DeadFlag forces/keeps "Dead".
      2) Egg:   Age.stage == 'Egg' forces/keeps "Egg". When it stops being 'Egg',
                push to 'Idle' once to start normal behavior.
      3) Hunger bias: If very hungry, nudge to LookForFood (unless already food-related).
    """

    def update(self, world, proposed_states):
        # ----- 1) Hard override: DeadFlag → "Dead" -----
        dead_entities = set()
        for e in list(proposed_states.keys()):
            brain = world.get_component(e, Brain)
            if brain is None:
                continue
            if world.get_component(e, DeadFlag):
                dead_entities.add(e)
                if brain.state != "Dead":
                    proposed_states[e] = "Dead"
                else:
                    proposed_states[e] = None  # stay
        # ----- 2) Egg lock + exit-on-hatch -----
        for e in list(proposed_states.keys()):
            if e in dead_entities:
                continue
            brain = world.get_component(e, Brain)
            age = world.get_component(e, Age)
            if brain is None or age is None:
                continue
            if age.stage == "Egg":
                # Force/keep Egg state while it's an egg.
                if brain.state != "Egg":
                    proposed_states[e] = "Egg"
                else:
                    proposed_states[e] = None  # keep it there
                continue
            # Just hatched: if currently in Egg, move to Idle once.
            if brain.state == "Egg":
                proposed_states[e] = "Idle"

        # ----- 3) Hunger bias (skip dead or egg) -----
        for e, proposed in list(proposed_states.items()):
            if e in dead_entities:
                continue
            brain = world.get_component(e, Brain)
            age = world.get_component(e, Age)
            if brain is None or (age is not None and age.stage == "Egg") or brain.state == "Dead":
                continue
            hunger = world.get_component(e, Hunger)
            tuning = world.get_component(e, BehaviorTuning)
            if not (hunger and tuning):
                continue
            threshold = float(tuning.get("food_seek_threshold", 0.5))
            ratio = hunger.hunger / max(1e-6, hunger.hunger_max)
            if ratio < threshold:
                if (proposed not in ("ChaseFood", "LookForFood")
                        and brain.state not in ("ChaseFood", "LookForFood")):
                    proposed_states[e] = "LookForFood"

        return proposed_states
