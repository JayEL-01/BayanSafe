"""Emergency Inventory and Supply System for BayanSafe.

Manages 72-hour Go-Bag contents, survival items, and story-critical keys/logs.
"""

from typing import Dict, List, Optional


class InventorySystem:
    def __init__(self, score_system=None):
        self.score_system = score_system
        self.items: Dict[str, int] = {}
        self.item_meta = {
            "gobag": {"name": "72-Hour Go-Bag", "desc": "Pre-packed emergency survival backpack."},
            "water": {"name": "Bottled Water", "desc": "Clean drinking water for hydration."},
            "food": {"name": "Food Rations", "desc": "Canned goods and high-energy biscuits."},
            "firstaid": {"name": "First-Aid Kit", "desc": "Bandages, antiseptic, and sterile gauze."},
            "flashlight": {"name": "Flashlight", "desc": "Battery-powered emergency torch."},
            "radio": {"name": "Transistor Radio", "desc": "Portable AM/FM radio for disaster bulletins."},
            "keycard": {"name": "Facility Keycard", "desc": "Aegis-Terra security override card."},
            "log": {"name": "Dr. Voss Log", "desc": "Recorded admission of machine activation."},
            "map": {"name": "Hazard Map", "desc": "Faultline and safe elevation map."},
        }

    def add_item(self, item_id: str, quantity: int = 1) -> bool:
        if quantity <= 0:
            return False
        self.items[item_id] = self.items.get(item_id, 0) + quantity
        if self.score_system and item_id in ("gobag", "water", "food", "firstaid", "flashlight", "radio"):
            self.score_system.collect_supply(item_id)
        return True

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        if self.has_item(item_id, quantity):
            self.items[item_id] -= quantity
            if self.items[item_id] <= 0:
                del self.items[item_id]
            return True
        return False

    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        return self.items.get(item_id, 0) >= quantity

    def get_count(self, item_id: str) -> int:
        return self.items.get(item_id, 0)

    def get_all(self) -> List[Dict[str, str]]:
        result = []
        for item_id, count in self.items.items():
            meta = self.item_meta.get(item_id, {"name": item_id.title(), "desc": ""})
            result.append({
                "id": item_id,
                "name": meta["name"],
                "desc": meta["desc"],
                "count": count,
            })
        return result

    def is_gobag_complete(self) -> bool:
        """Check if essential go-bag requirements are satisfied."""
        essential = ["water", "food", "flashlight", "firstaid", "radio"]
        return all(self.has_item(item) for item in essential)

    def to_dict(self) -> Dict[str, int]:
        return dict(self.items)

    def from_dict(self, data: Dict[str, int]):
        if isinstance(data, dict):
            self.items = dict(data)
