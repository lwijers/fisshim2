from dataclasses import dataclass

@dataclass
class Velocity:
    dx: float
    dy: float

    # --- Compatibility aliases (tests sometimes use vx/vy) ---
    @property
    def vx(self) -> float:            # why: keep old test API working
        return self.dx

    @vx.setter
    def vx(self, value: float) -> None:
        self.dx = float(value)

    @property
    def vy(self) -> float:
        return self.dy

    @vy.setter
    def vy(self, value: float) -> None:
        self.dy = float(value)

    def __iter__(self):
        yield self.dx
        yield self.dy
