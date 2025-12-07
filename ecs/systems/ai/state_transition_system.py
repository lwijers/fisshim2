from ecs.fsm import FSM_STATES
from ecs.components.fish.brain_component import Brain

class StateTransitionSystem:
    def __init__(self, context, behavior_system):
        self.context = context
        self.behavior = behavior_system
        self._entered = {}

    def update(self, world, final_states, dt):
        for e, next_state in final_states.items():
            if next_state is None:
                continue
            brain = world.get_component(e, Brain)
            if brain is None:
                continue
            current = brain.state
            if next_state == current:
                continue

            fish_view = self.behavior._views.get(e)
            if fish_view is None:
                continue

            # EXIT old state
            if (e, current) in self._entered:
                FSM_STATES[current].exit(fish_view, self.context)
                self._entered.pop((e, current), None)

            # 🔊 if we're transitioning to Dead, play SFX once here
            if next_state == "Dead":
                audio = getattr(self.context, "audio", None)
                if audio:
                    audio.play("death")

            # SWITCH
            brain.state = next_state
            brain.state_timer = 0.0

            # ENTER new state
            FSM_STATES[next_state].enter(fish_view, self.context)
            self._entered[(e, next_state)] = True
