# ecs/components/__init__.py
from dataclasses import dataclass

# Registry of component classes, so systems can refer to them easily
COMPONENTS = {}

def register_component(cls):
    """Decorator to auto-register component in ECS."""
    COMPONENTS[cls.__name__] = cls
    return cls
