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

    @property
    def caps(self) -> int:
        return sum(
            item.quantity
            for item in self.items
            if item.item_type == "currency" and item.item_id == "caps"
        )

    def add_caps(self, amount: int) -> bool:
        if amount <= 0:
            return False
        from fallout_berlin.item import create_item

        caps = create_item("caps", amount)
        if not caps:
            return False
        caps.quantity = amount
        caps.stackable = True
        return self.add_item(caps)

    def remove_caps(self, amount: int) -> bool:
        if amount <= 0 or self.caps < amount:
            return False

        remaining = amount
        for item in list(self.items):
            if item.item_type != "currency" or item.item_id != "caps":
                continue
            removed = min(item.quantity, remaining)
            item.quantity -= removed
            remaining -= removed
            if item.quantity == 0:
                self.items.remove(item)
            if remaining == 0:
                return True
        return False
    
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
        if item.item_type == "currency" and item.item_id == "caps":
            item.stackable = True
        if not self.can_add_item(item):
            return False

        # Unique/Special Item discovery animation
        unique_items = ["legendary_currywurst", "nefertiti_bust", "iron_ring_data", "pre_war_engagement_ring", "mp_gauss", "currywurst", "nefertiti_bust"]
        item_id = getattr(item, 'item_id', '')
        if item_id in unique_items or item.value >= 500:
             from fallout_berlin.art_master import ArtEffects
             
             # Custom animations for specific items
             if item_id == "currywurst":
                 ArtEffects.currywurst_discovery().play()
             elif item_id == "nefertiti_bust":
                 ArtEffects.nefertiti_discovery().play()
             else:
                 # Placeholder for a generic item discovery animation if needed
                 # ArtEffects.item_discovery_animation(item.name, item.ascii_art).play()
                 pass
        
        # Check if item already exists (for stackable items)
        existing = self.find_item(item.name)
        if existing and item.stackable:
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
    
    def find_item(self, item_id: str) -> Optional[Item]:
        """Find item by ID or name, with partial matching"""
        search_term = item_id.lower()
        
        # 1. Exact match
        for item in self.items:
            current_id = getattr(item, 'item_id', '')
            if current_id.lower() == search_term or item.name.lower() == search_term:
                return item
        
        # 2. Partial match
        for item in self.items:
            current_id = getattr(item, 'item_id', '')
            if search_term in current_id.lower() or search_term in item.name.lower():
                return item
                
        return None
    
    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Check if inventory has item"""
        item = self.find_item(item_name)
        if not item:
            return False
        return item.quantity >= quantity

    def has_healing_items(self) -> bool:
        """Check if inventory contains any healing items (e.g., Stimpaks)"""
        return any(item.name.lower() == "stimpak" for item in self.get_consumables())
    
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
            return [item for item in ammo_items if getattr(item, 'item_id', '') == ammo_type]
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
        for item in self.items:
            if item.item_type == "currency" and item.item_id == "caps":
                item.stackable = True
        self.max_weight = data.get('max_weight', 150)
    
    def display(self) -> str:
        """Get formatted inventory display"""
        if not self.items:
            return "Inventory is empty."

        lines = [f"Inventory ({self.get_total_weight():.1f}/{self.max_weight} lbs)"]
        
        # Group items by type
        grouped_items: Dict[str, List[Item]] = {}
        for item in self.items:
            if item.item_type not in grouped_items:
                grouped_items[item.item_type] = []
            grouped_items[item.item_type].append(item)
            
        # Sort item types for consistent order
        sorted_item_types = sorted(grouped_items.keys())
        
        for item_type in sorted_item_types:
            lines.append(f"\n--- {item_type.upper()} ---")
            
            # Sort items within each group by name
            sorted_items = sorted(grouped_items[item_type], key=lambda x: x.name)
            
            for item in sorted_items:
                # Format: [Qty] Name (Weight)
                quantity_str = f"[{item.quantity}]".ljust(5)
                name_str = item.name.ljust(30)
                weight_str = f"({item.weight * item.quantity:.1f} lbs)"
                lines.append(f"  {quantity_str} {name_str} {weight_str}")
                
        return "\n".join(lines)

    def display_item_details(self, item_name: str) -> str:
        """Get formatted display for a specific item"""
        item = self.find_item(item_name)
        if not item:
            return f"You don't have a {item_name}."

        lines = [f"--- {item.name} ---"]
        if hasattr(item, 'ascii_art') and item.ascii_art:
            lines.append(item.ascii_art)
        
        lines.append(f"Description: {item.description}")
        lines.append(f"Type: {item.item_type}")
        lines.append(f"Weight: {item.weight} lbs")
        lines.append(f"Value: {item.value} caps")
        lines.append(f"Quantity: {item.quantity}")

        if hasattr(item, 'damage'):
            lines.append(f"Damage: {item.damage}")
        if hasattr(item, 'damage_resistance'):
            lines.append(f"DR: {item.damage_resistance}")
        if hasattr(item, 'effect_type'):
            lines.append(f"Effect: {item.effect_type} ({item.effect_value})")

        return "\n".join(lines)
