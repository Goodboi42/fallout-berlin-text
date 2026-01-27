"""
Location System
Handles locations, navigation, and area descriptions
"""

import json
import os
from typing import Dict, List, Optional, Callable, Any
from item import Item, create_item
from enemy import Enemy, create_enemy

class Location:
    """Represents a location in the game world"""
    
    def __init__(self, name: str, description: str, location_id: str):
        self.name = name
        self.description = description
        self.location_id = location_id
        
        # Connections to other locations
        self.connections: Dict[str, str] = {}  # direction -> location_id
        
        # Items in this location
        self.items: List[Item] = []
        
        # Enemies in this location
        self.enemies: List[Enemy] = []
        
        # NPCs in this location (will be added later)
        self.npcs: List[str] = []  # NPC IDs
        
        # Location flags and properties
        self.properties = {
            'discovered': False,
            'visited': False,
            'hostile': False,
            'radiation_level': 0,  # 0-100
            'safe': True
        }
        
        # Custom actions available in this location
        self.actions: Dict[str, Callable] = {}
        
        # Location-specific events
        self.events: List[Dict] = []
    
    def add_connection(self, direction: str, location_id: str):
        """Add a connection to another location"""
        self.connections[direction] = location_id
    
    def get_connections(self) -> Dict[str, str]:
        """Get all connections from this location"""
        return self.connections.copy()
    
    def add_item(self, item: Item):
        """Add an item to this location"""
        self.items.append(item)
    
    def add_enemy(self, enemy: Any):
        """Add an enemy to this location"""
        self.enemies.append(enemy)
    
    def remove_item(self, item_name: str) -> Optional[Item]:
        """Remove and return an item from this location"""
        for i, item in enumerate(self.items):
            if item.name.lower() == item_name.lower():
                return self.items.pop(i)
        return None
    
    def remove_enemy(self, enemy_name: str) -> Optional[Any]:
        """Remove and return an enemy from this location"""
        for i, enemy in enumerate(self.enemies):
            if enemy.name.lower() == enemy_name.lower():
                return self.enemies.pop(i)
        return None
    
    def find_item(self, item_name: str) -> Optional[Item]:
        """Find an item in this location"""
        for item in self.items:
            if item.name.lower() == item_name.lower():
                return item
        return None

    def find_enemy(self, enemy_name: str) -> Optional[Any]:
        """Find an enemy in this location"""
        for enemy in self.enemies:
            if enemy.name.lower() == enemy_name.lower():
                return enemy
        return None
    
    def set_property(self, key: str, value: Any):
        """Set a location property"""
        self.properties[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a location property"""
        return self.properties.get(key, default)
    
    def add_action(self, action_name: str, action_func: Callable):
        """Add a custom action to this location"""
        self.actions[action_name] = action_func
    
    def get_description(self, detailed: bool = False) -> str:
        """Get location description"""
        desc = f"{self.name}\n{self.description}\n"
        
        if detailed:
            # Add connections
            if self.connections:
                desc += "\nYou can go: " + ", ".join(self.connections.keys())
            
            # Add items
            if self.items:
                desc += "\n\nItems here: " + ", ".join(str(item) for item in self.items)
            
            # Add enemies
            if self.enemies:
                desc += "\n\nEnemies here: " + ", ".join(f"{e.name} (Level {e.level})" for e in self.enemies)
            
            # Add properties
            if self.properties.get('radiation_level', 0) > 0:
                rad_level = self.properties['radiation_level']
                if rad_level < 25:
                    desc += "\n[Low radiation detected]"
                elif rad_level < 50:
                    desc += "\n[Moderate radiation detected]"
                elif rad_level < 75:
                    desc += "\n[High radiation detected]"
                else:
                    desc += "\n[EXTREME RADIATION - Seek shelter immediately!]"
        
        return desc
    
    def to_dict(self) -> Dict:
        """Convert location to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'location_id': self.location_id,
            'connections': self.connections,
            'items': [item.to_dict() for item in self.items],
            'enemies': [enemy.to_dict() for enemy in self.enemies],
            'npcs': self.npcs,
            'properties': self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Location':
        """Create location from dictionary"""
        from item import Item
        from enemy import Enemy
        
        location = cls(
            data['name'],
            data['description'],
            data['location_id']
        )
        location.connections = data.get('connections', {})
        location.items = [Item.from_dict(item_data) for item_data in data.get('items', [])]
        location.enemies = [Enemy.from_dict(enemy_data) for enemy_data in data.get('enemies', [])]
        location.npcs = data.get('npcs', [])
        location.properties = data.get('properties', {})
        return location


class LocationManager:
    """Manages all locations in the game world"""
    
    def __init__(self):
        self.locations: Dict[str, Location] = {}
        self._initialize_locations()
    
    def _initialize_locations(self):
        """Initialize game locations from JSON data"""
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'locations.json')
        if not os.path.exists(data_path):
            # Fallback to minimal hardcoded if file missing
            self.add_location(Location("Checkpoint Charlie Market", "A trading hub.", "checkpoint_charlie"))
            return

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for loc_id, loc_data in data.items():
                    location = Location(
                        loc_data['name'],
                        loc_data['description'],
                        loc_id
                    )
                    location.connections = loc_data.get('connections', {})
                    location.properties = loc_data.get('properties', {
                        'discovered': False,
                        'visited': False,
                        'hostile': False,
                        'radiation_level': 0,
                        'safe': True
                    })
                    location.npcs = loc_data.get('npcs', [])
                    
                    # Add initial items if specified
                    for item_key in loc_data.get('items', []):
                        item = create_item(item_key)
                        if item:
                            location.add_item(item)
                    
                    # Add initial enemies if specified
                    for enemy_key in loc_data.get('enemies', []):
                        enemy = create_enemy(enemy_key)
                        if enemy:
                            location.add_enemy(enemy)
                            
                    self.add_location(location)
        except Exception as e:
            print(f"Error loading location database: {e}")
    
    def add_location(self, location: Location):
        """Add a location to the world"""
        self.locations[location.location_id] = location
    
    def get_location(self, location_id: str) -> Optional[Location]:
        """Get a location by ID"""
        return self.locations.get(location_id)
    
    def get_location_by_name(self, name: str) -> Optional[Location]:
        """Get a location by name"""
        for location in self.locations.values():
            if location.name.lower() == name.lower():
                return location
        return None
    
    def can_travel(self, from_location_id: str, direction: str) -> Optional[str]:
        """Check if travel is possible and return destination"""
        location = self.get_location(from_location_id)
        if not location:
            return None
        return location.connections.get(direction.lower())
    
    def discover_location(self, location_id: str):
        """Mark a location as discovered"""
        location = self.get_location(location_id)
        if location:
            location.set_property('discovered', True)
    
    def visit_location(self, location_id: str):
        """Mark a location as visited"""
        location = self.get_location(location_id)
        if location:
            location.set_property('visited', True)
            if not location.get_property('discovered'):
                self.discover_location(location_id)
