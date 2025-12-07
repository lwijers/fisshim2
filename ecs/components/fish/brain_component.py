from dataclasses import dataclass

@dataclass
class Brain:
    state: str = "Cruise"     # current FSM state
    state_timer: float = 0.0  # time spent in the current state
    next_state_time: float = 0.0  # earliest time we MAY switch
    tx: float = 0.0           # target point
    ty: float = 0.0
    current_desired_speed: float = 0.0
