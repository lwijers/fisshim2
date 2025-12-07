from dataclasses import dataclass
from typing import Optional

@dataclass
class Breeding:
    wants_breed: bool = False
    partner_id: Optional[int] = None
    time_near: float = 0.0
    cooldown: float = 0.0
    toggle_on: bool = False   # per-fish UI toggle; default OFF
