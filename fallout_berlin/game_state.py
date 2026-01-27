"""
Game State Management
Handles saving, loading, and tracking all game state
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class GameState:
    """Manages all game state including player, world, and quest data"""
    
    def __init__(self):
        self.player = None
        self.current_location = None
        self.faction_reputation = {}
        self.quests = {}
        self.world_flags = {}
        self.inventory = None  # Will be initialized as Inventory object
        self.game_time = 0  # Days since game start
        self.visited_locations = set()
        self.killed_creatures = {}
        self.discovered_locations = set()
        self.location_states = {}  # location_id -> location_dict
        self.combat_state = None  # None or Dict with enemy info
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to dictionary for saving"""
        return {
            'player': self.player.to_dict() if self.player else None,
            'current_location': self.current_location,
            'faction_reputation': self.faction_reputation,
            'quests': {k: v.to_dict() for k, v in self.quests.items()},
            'world_flags': self.world_flags,
            'inventory': self.inventory.to_dict() if hasattr(self.inventory, 'to_dict') else [item.to_dict() for item in (self.inventory if isinstance(self.inventory, list) else [])],
            'game_time': self.game_time,
            'visited_locations': list(self.visited_locations),
            'killed_creatures': self.killed_creatures,
            'discovered_locations': list(self.discovered_locations),
            'location_states': self.location_states,
            'combat_state': self.combat_state,
            'save_date': datetime.now().isoformat()
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Load game state from dictionary"""
        # Import here to avoid circular dependencies
        from fallout_berlin.player import Player
        from fallout_berlin.quest import Quest
        from fallout_berlin.item import Item
        from fallout_berlin.inventory import Inventory
        
        if data.get('player'):
            self.player = Player.from_dict(data['player'])
        self.current_location = data.get('current_location')
        self.faction_reputation = data.get('faction_reputation', {})
        
        # Reconstruct quests
        self.quests = {}
        for k, v in data.get('quests', {}).items():
            self.quests[k] = Quest.from_dict(v)
        
        self.world_flags = data.get('world_flags', {})
        
        # Reconstruct inventory
        if isinstance(data.get('inventory'), list):
            # Old format: list of items
            self.inventory = Inventory()
            for item_data in data.get('inventory', []):
                item = Item.from_dict(item_data)
                self.inventory.add_item(item)
        else:
            # New format: Inventory object
            self.inventory = Inventory()
            if data.get('inventory'):
                self.inventory.from_dict(data['inventory'])
        
        self.game_time = data.get('game_time', 0)
        self.visited_locations = set(data.get('visited_locations', []))
        self.killed_creatures = data.get('killed_creatures', {})
        self.discovered_locations = set(data.get('discovered_locations', []))
        self.location_states = data.get('location_states', {})
        self.combat_state = data.get('combat_state')
    
    def save_game(self, filename: str = "savegame.json"):
        """Save game state to file"""
        save_dir = "saves"
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_game(self, filename: str = "savegame.json") -> bool:
        """Load game state from file"""
        save_dir = "saves"
        filepath = os.path.join(save_dir, filename)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.from_dict(data)
            return True
        except Exception as e:
            print(f"Error loading game: {e}")
            return False
    
    def list_saves(self) -> list:
        """List all available save files"""
        save_dir = "saves"
        if not os.path.exists(save_dir):
            return []
        
        saves = []
        for filename in os.listdir(save_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(save_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        save_date = data.get('save_date', 'Unknown')
                        saves.append({
                            'filename': filename,
                            'date': save_date,
                            'location': data.get('current_location', 'Unknown')
                        })
                except:
                    pass
        
        return sorted(saves, key=lambda x: x['date'], reverse=True)
    
    def set_world_flag(self, flag: str, value: Any = True):
        """Set a world flag (for tracking story events)"""
        self.world_flags[flag] = value
    
    def get_world_flag(self, flag: str, default: Any = False) -> Any:
        """Get a world flag value"""
        return self.world_flags.get(flag, default)
    
    def check_world_flag(self, flag: str) -> bool:
        """Check if a world flag is set"""
        return self.world_flags.get(flag, False)
    
    def modify_faction_reputation(self, faction: str, amount: int):
        """Modify faction reputation"""
        if faction not in self.faction_reputation:
            self.faction_reputation[faction] = 0
        self.faction_reputation[faction] += amount
        # Clamp between -100 and 100
        self.faction_reputation[faction] = max(-100, min(100, self.faction_reputation[faction]))
    
    def get_faction_reputation(self, faction: str) -> int:
        """Get faction reputation"""
        return self.faction_reputation.get(faction, 0)
    
    def get_faction_standing(self, faction: str) -> str:
        """Get faction standing as text"""
        rep = self.get_faction_reputation(faction)
        if rep >= 75:
            return "Idolized"
        elif rep >= 50:
            return "Liked"
        elif rep >= 25:
            return "Accepted"
        elif rep >= 0:
            return "Neutral"
        elif rep >= -25:
            return "Disliked"
        elif rep >= -50:
            return "Hated"
        else:
            return "Vilified"
