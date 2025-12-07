from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class BehaviorTuning:
    params: Dict[str, Any]

    def get(self, key, default=None):
        return self.params.get(key, default)
