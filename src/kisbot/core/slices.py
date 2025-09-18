import math

class SliceBook:
    def __init__(self, equity: float, slices_total=60):
        self.equity = equity
        self.slices_total = slices_total
        self.slices_in_use = 0
    @property
    def slice_value(self) -> float:
        return math.floor(self.equity / self.slices_total)
    def can_add(self, per_entry: int) -> bool:
        return self.slices_in_use + per_entry <= self.slices_total
    def reserve(self, per_entry: int) -> float:
        if not self.can_add(per_entry):
            return 0.0
        self.slices_in_use += per_entry
        return self.slice_value * per_entry
    def free_all(self):
        self.slices_in_use = 0
