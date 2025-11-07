from dataclasses import dataclass, field


@dataclass
class Stuff:
    id: int
    name: str
    bought_price: float
    ready_to_sell: bool = False
    in_hand: int = 0
    daily_score: list[int] = field(default_factory=list)
    daily_price: list[float] = field(default_factory=list)

    def __repr__(self):
        return f'Stuff(id={self.id}, name="{self.name}", bought_price={self.bought_price}, ready_to_sell={self.ready_to_sell}, in_hand={self.in_hand}, daily_score={self.daily_score}, daily_price={self.daily_price})'


@dataclass
class Inventory:
    items: list[Stuff]

    def __repr__(self):
        return f'Inventory: \n ' + '\n '.join([repr(item) for item in self.items])