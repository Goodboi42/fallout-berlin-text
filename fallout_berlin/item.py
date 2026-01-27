"""
Item System
Handles items, weapons, armor, consumables, etc.
"""

from typing import Dict, Any, Optional, List


import json
import os

class Item:
    """Base item class"""
    
    def __init__(self, name: str, description: str, weight: float = 0.0, value: int = 0):
        self.name = name
        self.description = description
        self.weight = weight
        self.value = value
        self.quantity = 1
        self.item_type = 'misc'
        self.equipped = False

    
    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'weight': self.weight,
            'value': self.value,
            'quantity': self.quantity,
            'item_type': self.item_type,
            'equipped': self.equipped,
            'class': self.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        """Create item from dictionary"""
        item_type = data.get('class', 'Item')
        
        # Create appropriate subclass
        if item_type == 'Weapon':
            item = Weapon.from_dict(data)
        elif item_type == 'Armor':
            item = Armor.from_dict(data)
        elif item_type == 'Consumable':
            item = Consumable.from_dict(data)
        elif item_type == 'Ammo':
            item = Ammo.from_dict(data)
        else:
            item = cls(
                data['name'],
                data['description'],
                data.get('weight', 0),
                data.get('value', 0)
            )
            item.quantity = data.get('quantity', 1)
            item.item_type = data.get('item_type', 'misc')
        
        item.equipped = data.get('equipped', False)
        return item

    
    def __str__(self):
        if self.quantity > 1:
            return f"{self.name} x{self.quantity}"
        return self.name


class Weapon(Item):
    """Weapon item"""
    
    def __init__(self, name: str, description: str, damage: int, 
                 weapon_type: str, skill: str, ammo_type: str = None,
                 weight: float = 0.0, value: int = 0, range: int = 1):
        super().__init__(name, description, weight, value)
        self.item_type = 'weapon'
        self.damage = damage
        self.weapon_type = weapon_type  # 'melee', 'ranged', 'energy'
        self.skill = skill  # Skill used with this weapon
        self.ammo_type = ammo_type  # None for melee
        self.range = range  # Range in "tiles" or abstract units
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'damage': self.damage,
            'weapon_type': self.weapon_type,
            'skill': self.skill,
            'ammo_type': self.ammo_type,
            'range': self.range
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Weapon':
        weapon = cls(
            data['name'],
            data['description'],
            data['damage'],
            data['weapon_type'],
            data['skill'],
            data.get('ammo_type'),
            data.get('weight', 0),
            data.get('value', 0),
            data.get('range', 1)
        )
        weapon.quantity = data.get('quantity', 1)
        return weapon


class Armor(Item):
    """Armor item"""
    
    def __init__(self, name: str, description: str, damage_resistance: int,
                 weight: float = 0.0, value: int = 0, armor_type: str = 'body'):
        super().__init__(name, description, weight, value)
        self.item_type = 'armor'
        self.damage_resistance = damage_resistance
        self.armor_type = armor_type  # 'body', 'head', 'legs', etc.
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'damage_resistance': self.damage_resistance,
            'armor_type': self.armor_type
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Armor':
        armor = cls(
            data['name'],
            data['description'],
            data['damage_resistance'],
            data.get('weight', 0),
            data.get('value', 0),
            data.get('armor_type', 'body')
        )
        armor.quantity = data.get('quantity', 1)
        return armor


class Consumable(Item):
    """Consumable item (food, medicine, etc.)"""
    
    def __init__(self, name: str, description: str, effect_type: str, 
                 effect_value: int, weight: float = 0.0, value: int = 0):
        super().__init__(name, description, weight, value)
        self.item_type = 'consumable'
        self.effect_type = effect_type  # 'heal', 'rad_heal', 'buff', etc.
        self.effect_value = effect_value
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'effect_type': self.effect_type,
            'effect_value': self.effect_value
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Consumable':
        consumable = cls(
            data['name'],
            data['description'],
            data['effect_type'],
            data['effect_value'],
            data.get('weight', 0),
            data.get('value', 0)
        )
        consumable.quantity = data.get('quantity', 1)
        return consumable


class Ammo(Item):
    """Ammunition item"""
    
    def __init__(self, name: str, ammo_type: str, quantity: int = 1, 
                 weight: float = 0.0, value: int = 0):
        super().__init__(name, f"{ammo_type} ammunition", weight, value)
        self.item_type = 'ammo'
        self.ammo_type = ammo_type
        self.quantity = quantity
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'ammo_type': self.ammo_type
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ammo':
        ammo = cls(
            data['name'],
            data['ammo_type'],
            data.get('quantity', 1),
            data.get('weight', 0),
            data.get('value', 0)
        )
        return ammo


# Global items database, loaded on demand
ITEM_DATABASE = {}

def load_item_database():
    """Load items from JSON data file"""
    global ITEM_DATABASE
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'items.json')
    if not os.path.exists(data_path):
        return
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for key, item_data in data.items():
                ITEM_DATABASE[key] = Item.from_dict(item_data)
    except Exception as e:
        print(f"Error loading item database: {e}")

# Initial load
load_item_database()

def create_item(item_key: str, quantity: int = 1) -> Optional[Item]:
    """Create an item from the database"""
    if item_key not in ITEM_DATABASE:
        # Try reloading if not found
        load_item_database()
        if item_key not in ITEM_DATABASE:
            return None
    
    item = ITEM_DATABASE[item_key]
    # Create a copy using to_dict/from_dict
    new_item = Item.from_dict(item.to_dict())
    new_item.quantity = quantity
    return new_item

