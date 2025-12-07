# ecs/fsm/__init__.py
from ecs.fsm.idle_state import IdleState
from ecs.fsm.cruise_state import CruiseState
from ecs.fsm.dead_state import DeadState
from ecs.fsm.look_for_food_state import LookForFoodState
from ecs.fsm.chase_food_state import ChaseFoodState
from ecs.fsm.egg_state import EggState  # ← NEW

# Single registry
FSM_STATES = {
    IdleState.NAME: IdleState(),
    CruiseState.NAME: CruiseState(),
    DeadState.NAME: DeadState(),
    LookForFoodState.NAME: LookForFoodState(),
    ChaseFoodState.NAME: ChaseFoodState(),
    EggState.NAME: EggState(),  # ← NEW
}
