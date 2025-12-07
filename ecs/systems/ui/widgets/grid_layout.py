from typing import Tuple

class CardGrid:
    """Compute grid geometry for fixed-size cards."""
    def __init__(self, card_w: int, card_h: int, gutter_x: int, gutter_y: int):
        self.card_w = card_w
        self.card_h = card_h
        self.gx = gutter_x
        self.gy = gutter_y

    def measure(self, view_w: int, count: int) -> Tuple[int, int, int]:
        cols = max(1, (view_w + self.gx) // (self.card_w + self.gx))
        total_w = int(cols) * self.card_w + int(cols - 1) * self.gx
        grid_x = max(0, (view_w - total_w) // 2)
        rows = (count + cols - 1) // cols if count else 0
        return int(cols), int(rows), int(grid_x)

    def pos(self, index: int, cols: int, grid_x: int) -> Tuple[int, int]:
        row = index // cols
        col = index % cols
        x = grid_x + col * (self.card_w + self.gx)
        y = row * (self.card_h + self.gy)
        return x, y
