import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

@dataclass
class Stuff:
    id: int
    name: str
    bought_price: float
    purchase_date: str = field(default_factory=lambda: datetime.now().isoformat())
    extra_info: Dict[str, Any] = field(default_factory=dict)
    
    # Legacy fields for compatibility
    ready_to_sell: bool = False
    in_hand: int = 0
    daily_score: List[int] = field(default_factory=list)
    daily_price: List[float] = field(default_factory=list)

    def is_tradeable(self, current_date: datetime) -> bool:
        """Check if item is tradeable based on T+7 rule."""
        try:
            p_date = datetime.fromisoformat(self.purchase_date)
            return current_date >= p_date + timedelta(days=7)
        except ValueError:
            return False

    def days_held(self, current_date: datetime) -> int:
        """Calculate how many days the item has been held."""
        try:
            p_date = datetime.fromisoformat(self.purchase_date)
            delta = current_date - p_date
            return delta.days
        except ValueError:
            return 0

    def __repr__(self):
        return f'Stuff(id={self.id}, name="{self.name}", price={self.bought_price}, date={self.purchase_date})'


@dataclass
class Inventory:
    items: List[Stuff] = field(default_factory=list)

    def add_item(self, id: int, name: str, price: float, date: datetime = None, info: dict = None):
        """Add a new item to the inventory."""
        if date is None:
            date = datetime.now()
            
        item = Stuff(
            id=id, 
            name=name, 
            bought_price=price, 
            purchase_date=date.isoformat(),
            extra_info=info or {}
        )
        self.items.append(item)

    def get_tradeable_items(self, current_date: datetime) -> List[Stuff]:
        """Get list of items that can be sold."""
        return [i for i in self.items if i.is_tradeable(current_date)]

    def get_item_by_id(self, item_id: int) -> Optional[Stuff]:
        """Find first item with given ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def remove_item(self, item: Stuff):
        """Remove an item from inventory (e.g. sold)."""
        if item in self.items:
            self.items.remove(item)

    def save(self, filepath: str):
        """Save inventory to a JSON file."""
        data = [asdict(item) for item in self.items]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: str) -> 'Inventory':
        """Load inventory from a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            items = [Stuff(**d) for d in data]
            return cls(items=items)
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()

    def __repr__(self):
        return f'Inventory({len(self.items)} items)'