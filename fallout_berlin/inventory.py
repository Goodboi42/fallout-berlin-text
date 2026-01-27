"""
Inventory Management System
Handles player inventory, item management, and weight calculations
"""

from typing import List, Optional, Dict

# Import Item here to avoid circular dependencies
from fallout_berlin.item import Item


class Inventory:
    """Manages player inventory"""
    
    def __init__(self, max_weight: int = 150):
        self.items: List[Item] = []
        self.max_weight = max_weight
    
    def get_total_weight(self) -> float:
        """Calculate total weight of all items"""
        return sum(item.weight * item.quantity for item in self.items)
    
    def get_remaining_capacity(self) -> float:
        """Get remaining carry capacity"""
        return max(0, self.max_weight - self.get_total_weight())
    
    def can_add_item(self, item: Item) -> bool:
        """Check if item can be added (weight check)"""
        weight_needed = item.weight * item.quantity
        return self.get_remaining_capacity() >= weight_needed
    
    def add_item(self, item: Item) -> bool:
        """Add item to inventory"""
        if not self.can_add_item(item):
            return False
        
        # Check if item already exists (for stackable items)
        existing = self.find_item(item.name)
        if existing and item.item_type in ['consumable', 'ammo', 'misc']:
            existing.quantity += item.quantity
            return True
        
        # Add new item
        self.items.append(item)
        return True
    
    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """Remove item from inventory"""
        item = self.find_item(item_name)
        if not item:
            return False
        
        if item.quantity <= quantity:
            self.items.remove(item)
            return True
        else:
            item.quantity -= quantity
            return True
    
    def find_item(self, item_name: str) -> Optional[Item]:
        """Find item by name"""
        for item in self.items:
            if item.name.lower() == item_name.lower():
                return item
        return None
    
    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Check if inventory has item"""
        item = self.find_item(item_name)
        if not item:
            return False
        return item.quantity >= quantity
    
    def get_items_by_type(self, item_type: str) -> List[Item]:
        """Get all items of a specific type"""
        return [item for item in self.items if item.item_type == item_type]
    
    def get_weapons(self) -> List[Item]:
        """Get all weapons"""
        return self.get_items_by_type('weapon')
    
    def get_armor(self) -> List[Item]:
        """Get all armor"""
        return self.get_items_by_type('armor')
    
    def get_consumables(self) -> List[Item]:
        """Get all consumables"""
        return self.get_items_by_type('consumable')
    
    def get_ammo(self, ammo_type: str = None) -> List[Item]:
        """Get all ammo, optionally filtered by type"""
        ammo_items = self.get_items_by_type('ammo')
        if ammo_type:
            return [item for item in ammo_items if hasattr(item, 'ammo_type') and item.ammo_type == ammo_type]
        return ammo_items
    
    def get_ammo_count(self, ammo_type: str) -> int:
        """Get total count of specific ammo type"""
        ammo_items = self.get_ammo(ammo_type)
        return sum(item.quantity for item in ammo_items)
    
    def use_ammo(self, ammo_type: str, amount: int = 1) -> bool:
        """Use ammunition"""
        ammo_items = self.get_ammo(ammo_type)
        if not ammo_items:
            return False
        
        total_ammo = sum(item.quantity for item in ammo_items)
        if total_ammo < amount:
            return False
        
        # Remove ammo starting from first item
        remaining = amount
        for item in ammo_items:
            if item.quantity <= remaining:
                remaining -= item.quantity
                self.remove_item(item.name, item.quantity)
            else:
                item.quantity -= remaining
                remaining = 0
            
            if remaining <= 0:
                break
        
        return True
    
    def to_dict(self) -> Dict:
        """Convert inventory to dictionary"""
        return {
            'items': [item.to_dict() for item in self.items],
            'max_weight': self.max_weight
        }
    
    def from_dict(self, data: Dict):
        """Load inventory from dictionary"""
        from fallout_berlin.item import Item
        self.items = [Item.from_dict(item_data) for item_data in data.get('items', [])]
        self.max_weight = data.get('max_weight', 150)
    
    def display(self) -> str:
        """Get formatted inventory display"""
        if not self.items:
            return "Inventory is empty."
        
        lines = [f"Inventory ({self.get_total_weight():.1f}/{self.max_weight} lbs):"]
        lines.append("-" * 50)
        
        # Group by type
        weapons = self.get_weapons()
        armor = self.get_armor()
        consumables = self.get_consumables()
        ammo = self.get_ammo()
        misc = [item for item in self.items if item.item_type == 'misc']
        
        if weapons:
            lines.append("\nWeapons:")
            for item in weapons:
                lines.append(f"  - {item}")
        
        if armor:
            lines.append("\nArmor:")
            for item in armor:
                lines.append(f"  - {item}")
        
        if consumables:
            lines.append("\nConsumables:")
            for item in consumables:
                lines.append(f"  - {item}")
        
        if ammo:
            lines.append("\nAmmunition:")
            for item in ammo:
                lines.append(f"  - {item}")
        
        if misc:
            lines.append("\nMiscellaneous:")
            for item in misc:
                lines.append(f"  - {item}")
        
        return "\n".join(lines)
