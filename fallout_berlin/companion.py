from typing import Dict, Any
from fallout_berlin.inventory import Inventory
from fallout_berlin.npc import NPC


class Companion(NPC):
    def __init__(self, name: str, description: str, hp: int, damage: int):
        super().__init__(name, description)
        self.max_hp = hp
        self.hp = hp
        self.damage = damage
        self.inventory = Inventory(max_weight=50)

    def attack(self) -> int:
        return self.damage

    def take_damage(self, amount: int):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "max_hp": self.max_hp,
                "hp": self.hp,
                "damage": self.damage,
                "inventory": self.inventory.to_dict(),
                "is_alive": self.is_alive,
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Companion":
        c = cls(data["name"], data["description"], data["max_hp"], data["damage"])
        c.hp = data["hp"]
        c.is_alive = data.get("is_alive", True)
        c.dialogue_id = data.get("dialogue_id")
        if "inventory" in data:
            c.inventory.from_dict(data["inventory"])
        return c
