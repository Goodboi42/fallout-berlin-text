"""
Location System
Handles locations, navigation, and area descriptions
"""

import json
import os
from typing import Dict, List, Optional, Callable, Any
import colorama # Added back for debug prints
from colorama import Fore, Style # Added back for debug prints
import fallout_berlin.item
import fallout_berlin.enemy

class Location:
    """Represents a location in the game world"""
    
    def __init__(self, name: str, description: str, location_id: str):
        self.name = name
        self.description = description
        self.location_id = location_id
        self.ascii_map: Optional[str] = None

        # Connections to other locations
        self.connections: Dict[str, str] = {}  # direction -> location_id
        
        # Items in this location
        self.items: List[fallout_berlin.item.Item] = []
        
        # Enemies in this location
        self.enemies: List[fallout_berlin.enemy.Enemy] = [] # Changed type hint
        
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
        self.connections[direction.lower()] = location_id.lower()
    
    def get_connections(self) -> Dict[str, str]:
        """Get all connections from this location"""
        return self.connections.copy()
    
    def add_item(self, item: fallout_berlin.item.Item):
        """Add an item to this location"""
        self.items.append(item)
    
    def add_enemy(self, enemy: fallout_berlin.enemy.Enemy):
        """Add an enemy to this location"""
        self.enemies.append(enemy)
    
    def remove_item(self, item_name: str) -> Optional[fallout_berlin.item.Item]:
        """Remove and return an item from this location"""
        for i, item in enumerate(self.items):
            if item.name.lower() == item_name.lower():
                return self.items.pop(i)
        return None
    
    def remove_enemy(self, enemy_name: str) -> Optional[fallout_berlin.enemy.Enemy]:
        """Remove and return an enemy from this location"""
        for i, enemy in enumerate(self.enemies):
            if enemy.name.lower() == enemy_name.lower():
                return self.enemies.pop(i)
        return None
    
    def find_item(self, item_name: str) -> Optional[fallout_berlin.item.Item]:
        """Find an item in this location"""
        for item in self.items:
            if item.name.lower() == item_name.lower():
                return item
        return None

    def find_enemy(self, enemy_name: str) -> Optional[fallout_berlin.enemy.Enemy]:
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
            'properties': self.properties,
            'ascii_map': self.ascii_map
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Location':
        """Create location from dictionary"""
        # Removed local imports to avoid shadowing and rely on module-level imports
        
        location = cls(
            data['name'],
            data['description'],
            data['location_id']
        )
        location.connections = data.get('connections', {})
        location.items = [fallout_berlin.item.Item.from_dict(item_data) for item_data in data.get('items', [])]
        location.enemies = [fallout_berlin.enemy.Enemy.from_dict(enemy_data) for enemy_data in data.get('enemies', [])]
        location.npcs = data.get('npcs', [])
        location.properties = data.get('properties', {})
        location.ascii_map = data.get('ascii_map')
        return location


class LocationManager:
    """Manages all locations in the game world"""
    
    def __init__(self):
        self.locations: Dict[str, Location] = {}
        self._initialize_locations()
    
    def _initialize_locations(self):
        """Initialize game locations from JSON data"""
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'locations.json')
        if os.environ.get("DEBUG_MODE") == "1":
            print(f"{Fore.CYAN}[DEBUG] Looking for locations.json at: {data_path}{Style.RESET_ALL}")
        if not os.path.exists(data_path):
            print(f"{Fore.RED}[ERROR] locations.json NOT FOUND! Falling back to hardcoded location.{Style.RESET_ALL}")
            # Fallback to minimal hardcoded if file missing
            self.add_location(Location("Checkpoint Charlie Market", "A trading hub.", "checkpoint_charlie"))
            return

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if os.environ.get("DEBUG_MODE") == "1":
                    print(f"{Fore.GREEN}[DEBUG] Successfully loaded locations.json. Found locations: {list(data.keys())}{Style.RESET_ALL}")
                for loc_id, loc_data in data.items():
                    location = Location(
                        loc_data['name'],
                        loc_data['description'],
                        loc_id
                    )
                    # Ensure all connection directions are lower-cased for robust lookup
                    connections = loc_data.get('connections', {})
                    location.connections = {k.lower(): v for k, v in connections.items()}
                    location.properties = loc_data.get('properties', {
                        'discovered': False,
                        'visited': False,
                        'hostile': False,
                        'radiation_level': 0,
                        'safe': True
                    })
                    
                    # Store art in properties if present
                    if 'art' in loc_data:
                        location.set_property('art', loc_data['art'])
                    location.npcs = loc_data.get('npcs', [])
                    
                    # Add initial items if specified
                    for item_key in loc_data.get('items', []):
                        # Fix inconsistent item IDs (Audit 2.1.4)
                        if item_key in ["Döner (Special Meat)", "doner_kebab"]:
                            item_key = "doner_human"

                        item = fallout_berlin.item.create_item(item_key) # Changed create_item reference
                        if item:
                            location.add_item(item)
                    
                    # Add initial enemies if specified
                    for enemy_key in loc_data.get('enemies', []):
                        enemy = fallout_berlin.enemy.create_enemy(enemy_key) # Changed create_enemy reference
                        if enemy:
                            location.add_enemy(enemy)
                    
                    location.ascii_map = loc_data.get('ascii_map')
                    self.add_location(location)
            
            # Restore missing content identified in audit
            self._restore_missing_content()
            
            # Verify connectivity after restoration
            self._verify_connectivity()

        except Exception as e:
            print(f"Error loading location database: {e}")
    
    def _restore_missing_content(self):
        """Programmatically restore missing world content identified in audit."""
        if os.environ.get("DEBUG_MODE") == "1":
            print(f"{Fore.CYAN}[DEBUG] Restoring missing content and applying World Expansion...{Style.RESET_ALL}")
        # 1. Populate Empty Hubs
        bg = self.get_location("brandenburg_gate")
        if bg and not bg.npcs:
            bg.npcs.extend(["Guard Captain Hans", "Tourist Ghoul"])
            bg.description += "\n(Restored: Guards patrol the perimeter.)"
            
        alex = self.get_location("alexanderplatz")
        if alex and not alex.npcs:
            alex.npcs.extend(["Merchant Jakob", "Street Urchin"])
            alex.description += "\n(Restored: The plaza is bustling.)"

        # 2. Add Missing Locations & World Expansion
        
        # --- WEDDING ZONE EXPANSION ---
        wedding = self.get_location("wedding")
        if not wedding:
            wedding = Location("Wedding Center", "A claustrophobic maze of crumbled apartment blocks and concrete dust.", "wedding")
            wedding.set_property("hostile", True)
            self.add_location(wedding)
        else:
            wedding.name = "Wedding Center"
            wedding.description = "A claustrophobic maze of crumbled apartment blocks and concrete dust."

        # Connect Wedding to South (Museum Island or Alexanderplatz)
        museum = self.get_location("museum_island")
        if museum:
            wedding.add_connection("south", "museum_island")
            museum.add_connection("north", "wedding")
        elif alex:
            wedding.add_connection("south", "alexanderplatz")
            alex.add_connection("north", "wedding")

        # Raider Fortress (North of Wedding)
        if not self.get_location("raider_fortress"):
            fortress = Location("The Flak Tower Fortress", "An imposing, windowless concrete monolith converted into a raider stronghold.", "raider_fortress")
            fortress.set_property("hostile", True)
            # Fallback enemy creation if factory fails
            raider = fallout_berlin.enemy.create_enemy("raider") or fallout_berlin.enemy.Enemy("Raider", "A generic raider", 50, 5, 1)
            fortress.add_enemy(raider)
            fortress.add_connection("south", "wedding")
            wedding.add_connection("north", "raider_fortress")
            self.add_location(fortress)

        # Concrete Canyons (West of Wedding)
        if not self.get_location("concrete_canyons"):
            canyons = Location("The Concrete Canyons", "A sunken street level where collapsed buildings have formed an artificial valley.", "concrete_canyons")
            canyons.set_property("hostile", True)
            canyons.add_connection("east", "wedding")
            wedding.add_connection("west", "concrete_canyons")
            self.add_location(canyons)

        # U-Bahn Wedding (Down from Wedding)
        if not self.get_location("u_bahn_wedding"):
            u_wedding = Location("U-Bahn Station Wedding (U6)", "The yellow tiles are covered in grime and dried blood.", "u_bahn_wedding")
            u_wedding.set_property("radiation_level", 10)
            u_wedding.add_connection("up", "wedding")
            wedding.add_connection("down", "u_bahn_wedding")
            self.add_location(u_wedding)

        # --- GRUNEWALD ZONE EXPANSION ---
        grune = self.get_location("grunewald")
        if not grune:
            grune = Location("Grunewald - The Whispering Woods", "The trees here are twisted and wrong, their bark glowing with a faint, sick luminescence.", "grunewald")
            grune.set_property("radiation_level", 40)
            self.add_location(grune)
        else:
            grune.name = "Grunewald - The Whispering Woods"
            grune.description = "The trees here are twisted and wrong, their bark glowing with a faint, sick luminescence."

        # Connect Grunewald to East (Charlottenburg or Tiergarten)
        charlottenburg = self.get_location("charlottenburg_palace")
        tier = self.get_location("tiergarten")
        if charlottenburg:
            grune.add_connection("east", "charlottenburg_palace")
            charlottenburg.add_connection("west", "grunewald")
        elif tier:
            grune.add_connection("east", "tiergarten")
            tier.add_connection("west", "grunewald")

        # Teufelsberg Station (West of Grunewald)
        if not self.get_location("teufelsberg_station"):
            teufelsberg = Location("Teufelsberg Listening Post", "Perched atop the artificial hill, the tattered white domes look like giant, cracked eggs.", "teufelsberg_station")
            teufelsberg.set_property("radiation_level", 60)
            teufelsberg.add_connection("east", "grunewald")
            grune.add_connection("west", "teufelsberg_station")
            self.add_location(teufelsberg)

        # U-Bahn Grunewald (Down from Grunewald)
        if not self.get_location("u_bahn_grunewald"):
            u_grune = Location("U-Bahn Station Onkel Toms Hütte (U3)", "Nature has broken through the ceiling here. Partially flooded.", "u_bahn_grunewald")
            u_grune.set_property("radiation_level", 30)
            u_grune.add_connection("up", "grunewald")
            grune.add_connection("down", "u_bahn_grunewald")
            self.add_location(u_grune)

        # --- U-BAHN NETWORK HUB ---
        u_hub = self.get_location("u_bahn_tunnel")
        if not u_hub:
            u_hub = Location("U-Bahn Central Tunnel", "A dark, central junction of the metro network.", "u_bahn_tunnel")
            self.add_location(u_hub)
            # Connect to a central surface location if possible
            if alex:
                u_hub.add_connection("up", "alexanderplatz")
                alex.add_connection("down", "u_bahn_tunnel")

        # Connect U-Bahn Wedding (South) <-> Hub (North)
        u_wedding = self.get_location("u_bahn_wedding")
        if u_wedding:
            u_wedding.add_connection("south", "u_bahn_tunnel")
            u_hub.add_connection("north", "u_bahn_wedding")

        # Connect U-Bahn Grunewald (East) <-> Hub (West)
        u_grune = self.get_location("u_bahn_grunewald")
        if u_grune:
            u_grune.add_connection("east", "u_bahn_tunnel")
            u_hub.add_connection("west", "u_bahn_grunewald")

        # 3. Restore Spandau Citadel (Audit 2.2.1)
        if not self.get_location("spandau_citadel"):
            spandau = Location("Spandau Citadel", "A star fortress turned into a neo-feudal castle by the Bundesritter.", "spandau_citadel")
            spandau.set_property("safe", True)
            spandau.npcs.append("Grand Knight Albrecht")
            # Attempt to add faction guards
            knight = fallout_berlin.enemy.create_enemy("bundesritter_knight")
            if knight: spandau.add_enemy(knight)
            
            # Link to Concrete Canyons (West of Wedding)
            canyons = self.get_location("concrete_canyons")
            if canyons:
                canyons.add_connection("west", "spandau_citadel")
                spandau.add_connection("east", "concrete_canyons")
            self.add_location(spandau)

        # 4. Restore Tempelhof & Kreuzberg (Audit 2.2.1)
        if not self.get_location("tempelhof"):
            tempelhof = Location("Tempelhofer Feld", "A massive airport turned into a hydroponic farm by the Feld Commune.", "tempelhof")
            tempelhof.set_property("safe", True)
            tempelhof.npcs.append("Mother Renate")
            self.add_location(tempelhof)

        if not self.get_location("kreuzberg"):
            xberg = Location("Kreuzberg", "A district of shadows, neon, and danger.", "kreuzberg")
            xberg.set_property("hostile", True)
            # Add enemies
            for enemy_id in ["punk_raider", "dealer_ghoul"]:
                e = fallout_berlin.enemy.create_enemy(enemy_id)
                if e: xberg.add_enemy(e)
            
            # Link Tempelhof <-> Kreuzberg <-> Checkpoint Charlie
            tempelhof = self.get_location("tempelhof")
            if tempelhof:
                tempelhof.add_connection("north", "kreuzberg")
                xberg.add_connection("south", "tempelhof")
            
            cp = self.get_location("checkpoint_charlie")
            if cp:
                cp.add_connection("south", "kreuzberg")
                xberg.add_connection("north", "checkpoint_charlie")
            self.add_location(xberg)

        # 5. Ensure Quest Items exist (Audit 2.1.4)
        cp = self.get_location("checkpoint_charlie")
        if cp and not cp.find_item("anmeldung_form"):
            # Critical item for "Bureaucrat's Nightmare"
            form = fallout_berlin.item.create_item("anmeldung_form")
            if form: cp.add_item(form)

    def _verify_connectivity(self):
        """Analyze map connectivity and report orphans."""
        if not self.locations:
            return

        # Start BFS from a known central location
        start_node = 'checkpoint_charlie'
        if start_node not in self.locations:
            start_node = next(iter(self.locations))
        
        visited = set()
        queue = [start_node]
        
        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)
            
            loc = self.locations.get(current_id)
            if loc:
                for target_id in loc.connections.values():
                    if target_id not in visited:
                        queue.append(target_id)
        
        all_locs = set(self.locations.keys())
        orphans = all_locs - visited
        
        if orphans:
            if os.environ.get("DEBUG_MODE") == "1":
                print(f"{Fore.YELLOW}[WARNING] Disconnected locations found: {orphans}{Style.RESET_ALL}")
        else:
            if os.environ.get("DEBUG_MODE") == "1":
                print(f"{Fore.GREEN}[DEBUG] Map connectivity verified. All locations reachable.{Style.RESET_ALL}")

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
        dir_clean = direction.lower().strip()
        dir_aliases = {
            "n": "north", "s": "south", "e": "east", "w": "west",
            "u": "up", "d": "down"
        }
        dir_clean = dir_aliases.get(dir_clean, dir_clean)
        if os.environ.get("DEBUG_MODE") == "1":
            print(f"{Fore.MAGENTA}[DEBUG] can_travel: from_location_id={from_location_id}, direction={dir_clean}, connections={location.connections}{Style.RESET_ALL}")
        return location.connections.get(dir_clean)
    
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
