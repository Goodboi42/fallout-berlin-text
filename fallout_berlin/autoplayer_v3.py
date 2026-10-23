import time
import random
import json
from datetime import datetime
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Set
from collections import deque
import sys
import os
import re
import types
import traceback

# Mock colorama if missing to allow running without dependencies
try:
    import colorama
except ImportError:
    mock_colorama = types.ModuleType("colorama")
    mock_colorama.init = lambda *args, **kwargs: None
    mock_colorama.just_fix_windows_console = lambda: None
    class MockAnsi:
        def __init__(self, codes):
            for name, code in codes.items():
                setattr(self, name, code)
        def __getattr__(self, name): return ""
    
    FORE = {
        'BLACK': '\033[30m', 'RED': '\033[31m', 'GREEN': '\033[32m', 'YELLOW': '\033[33m',
        'BLUE': '\033[34m', 'MAGENTA': '\033[35m', 'CYAN': '\033[36m', 'WHITE': '\033[37m',
        'RESET': '\033[39m', 'LIGHTBLACK_EX': '\033[90m', 'LIGHTRED_EX': '\033[91m',
        'LIGHTGREEN_EX': '\033[92m', 'LIGHTYELLOW_EX': '\033[93m', 'LIGHTBLUE_EX': '\033[94m',
        'LIGHTMAGENTA_EX': '\033[95m', 'LIGHTCYAN_EX': '\033[96m', 'LIGHTWHITE_EX': '\033[97m'
    }
    BACK = {'BLACK': '\033[40m', 'RED': '\033[41m', 'GREEN': '\033[42m', 'YELLOW': '\033[43m', 'BLUE': '\033[44m', 'MAGENTA': '\033[45m', 'CYAN': '\033[46m', 'WHITE': '\033[47m', 'RESET': '\033[49m'}
    STYLE = {'DIM': '\033[2m', 'NORMAL': '\033[22m', 'BRIGHT': '\033[1m', 'RESET_ALL': '\033[0m'}

    mock_colorama.Fore = MockAnsi(FORE)
    mock_colorama.Back = MockAnsi(BACK)
    mock_colorama.Style = MockAnsi(STYLE)
    sys.modules["colorama"] = mock_colorama

# Ensure we can import from the package even if running incorrectly
try:
    import fallout_berlin
except ImportError:
    # Add parent directory to path to allow absolute imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Import game components for type hinting (optional, but good for IDEs)
# derived from reading improved_game_engine.py
from fallout_berlin.engine_states import ExplorationState, CombatState, DialogueState

try:
    from fallout_berlin.looting_state import LootingState
except ImportError:
    LootingState = None

try:
    from fallout_berlin.level_up_state import LevelUpState
except ImportError:
    LevelUpState = None

try:
    from fallout_berlin.quest_log_state import QuestLogState
except ImportError:
    QuestLogState = None

try:
    from fallout_berlin.inventory_state import InventoryState
except ImportError:
    InventoryState = None

try:
    from fallout_berlin.vats_state import VatsState
except ImportError:
    VatsState = None

try:
    from fallout_berlin.crafting_state import CraftingState
except ImportError:
    CraftingState = None

class IntentionType(Enum):
    SURVIVE = auto()      # Critical health/hunger/rads
    COMBAT = auto()       # Active threat or calculated aggression
    DIALOGUE = auto()     # Talking to NPCs
    QUEST = auto()        # Active objective pursuit
    EXPLORE = auto()      # Mapping the world
    REST = auto()         # Recovering resources safely
    LOOT = auto()         # Gathering resources
    WAIT = auto()         # Fallback
    LEVEL_UP = auto()     # Character progression
    QUEST_LOG = auto()    # Viewing quest log
    INVENTORY = auto()    # Managing inventory
    VATS = auto()         # Targeting
    CRAFTING = auto()     # Crafting items

@dataclass
class Signal:
    """Represents a semantic input from the game world."""
    type: str
    value: float  # 0.0 to 1.0 usually
    urgency: float # 0.0 to 1.0
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorldView:
    """Snapshot of the current frame's perceived reality."""
    player_status: Dict[str, float] # hp_percent, hunger, thirst, rads
    context: str # 'COMBAT', 'DIALOGUE', 'EXPLORATION', 'MENU'
    local_affordances: Dict[str, Any] # enemies, items, npcs, exits
    narrative_state: Dict[str, Any] # active_quests, current_objective
    current_location_id: str
    location_name: str
    dialogue_partner: Optional[str] = None

@dataclass
class Intention:
    """The high-level strategy the agent has decided to pursue."""
    type: IntentionType
    score: float
    reason: str
    target: Any = None # Target entity, location, or item

@dataclass
class LocationBelief:
    """Probabilistic memory of a location."""
    id: str
    safety_score: float = 0.5 # 0=Deadly, 1=Safe
    last_visited: float = 0.0
    explored_score: float = 0.0 # 0=Unknown, 1=Fully mapped
    npc_trust: Dict[str, float] = field(default_factory=dict)
    known_resources: List[str] = field(default_factory=list)
    known_enemies: List[str] = field(default_factory=list)


def analyze_location_connectivity(locations: Dict[str, Any]) -> Dict[str, Any]:
    """Report dangling exits and whether every location can reach every other."""
    location_ids = set(locations)
    dangling_exits = []
    adjacency = {}

    for location_id, location in locations.items():
        connections = getattr(location, "connections", {})
        adjacency[location_id] = set(connections.values()) & location_ids
        for direction, destination in connections.items():
            if destination not in location_ids:
                dangling_exits.append({
                    "from": location_id,
                    "direction": direction,
                    "to": destination,
                })

    unreachable = {}
    for start in location_ids:
        reached = {start}
        pending = [start]
        while pending:
            current = pending.pop()
            for destination in adjacency[current] - reached:
                reached.add(destination)
                pending.append(destination)
        missing = sorted(location_ids - reached)
        if missing:
            unreachable[start] = missing

    return {
        "location_count": len(location_ids),
        "strongly_connected": bool(location_ids) and not unreachable and not dangling_exits,
        "unreachable_from": unreachable,
        "dangling_exits": dangling_exits,
    }


class PerceptionLayer:
    """
    Translator. Converts engine.state (raw data) into WorldView (semantic meaning).
    """
    def scan(self, engine) -> WorldView:
        player = engine.state.player
        
        if player is None:
            return WorldView(
                player_status={"hp_percent": 1.0, "hunger": 0.0, "thirst": 0.0, "rads": 0.0, "is_sneaking": False},
                context="MENU",
                local_affordances={"enemies": [], "items": [], "npcs": [], "exits": []},
                narrative_state={"active_quests": []},
                current_location_id="menu",
                location_name="Menu",
                dialogue_partner=None
            )

        # 1. Player Status
        hp_percent = player.hit_points / player.max_hit_points if player.max_hit_points > 0 else 0
        hunger = getattr(player, 'hunger', 0) / 100.0
        thirst = getattr(player, 'thirst', 0) / 100.0
        rads = getattr(player, 'radiation', 0) / 1000.0 # Assuming 1000 is deadly
        
        status = {
            "hp_percent": hp_percent,
            "hunger": hunger,
            "thirst": thirst,
            "rads": rads,
            "is_sneaking": getattr(player, "is_sneaking", False)
        }

        # 2. Context
        context = "EXPLORATION"
        dialogue_partner = None
        if isinstance(engine.current_state, CombatState):
            context = "COMBAT"
        elif LootingState and isinstance(engine.current_state, LootingState):
            context = "LOOTING"
        elif isinstance(engine.current_state, DialogueState):
            context = "DIALOGUE"
            dialogue_partner = engine.current_state.npc_id
        elif LevelUpState and isinstance(engine.current_state, LevelUpState):
            context = "LEVEL_UP"
        elif QuestLogState and isinstance(engine.current_state, QuestLogState):
            context = "QUEST_LOG"
        elif InventoryState and isinstance(engine.current_state, InventoryState):
            context = "INVENTORY"
        elif VatsState and isinstance(engine.current_state, VatsState):
            context = "VATS"
        elif CraftingState and isinstance(engine.current_state, CraftingState):
            context = "CRAFTING"
        
        # 3. Local Affordances
        current_loc_id = engine.state.current_location
        location = engine.location_manager.get_location(current_loc_id)
        
        affordances = {
            "enemies": [],
            "items": [],
            "npcs": [],
            "exits": []
        }
        
        if location:
            affordances["enemies"] = [e.name for e in location.enemies]
            affordances["items"] = [i.name for i in location.items]
            affordances["npcs"] = location.npcs
            if location.connections:
                affordances["exits"] = list(location.connections.keys())

        # 4. Narrative State
        # We'd extract active quests here. For now, simple list.
        narrative = {
            "active_quests": [
                quest_id
                for quest_id, quest in engine.state.quests.items()
                if getattr(getattr(quest, "state", None), "value", None) == "active"
            ] if engine.state.quests else []
        }

        return WorldView(
            player_status=status,
            context=context,
            local_affordances=affordances,
            narrative_state=narrative,
            current_location_id=current_loc_id,
            location_name=location.name if location else "Unknown",
            dialogue_partner=dialogue_partner
        )

    def assess_threat(self, combat_manager) -> float:
        """
        Returns 0.0 to 1.0 based on combat difficulty.
        If no combat, returns 0.0 unless enemies are visible in exploration.
        """
        if not combat_manager or not combat_manager.current_enemy:
            return 0.0
            
        # Simple heuristic: Player HP vs Enemy Level/HP
        # Real v3 would check DPS, but we don't have direct DPS access easily without simulating.
        # So we use a proxy: Enemy Level vs Player Level.
        
        enemy = combat_manager.current_enemy
        player = combat_manager.player
        
        level_diff = enemy.level - player.level
        base_threat = 0.5 + (level_diff * 0.1) # Even match = 0.5
        
        # Modifier: Player HP
        hp_factor = 1.0 - (player.hit_points / player.max_hit_points)
        
        return min(1.0, max(0.0, base_threat + (hp_factor * 0.5)))

class SimpleGraph:
    def __init__(self):
        self.adj = {} # Adjacency list

    def add_node(self, node):
        if node not in self.adj:
            self.adj[node] = set()

    def add_edge(self, u, v):
        self.add_node(u)
        self.add_node(v)
        self.adj[u].add(v)
        self.adj[v].add(u)

    def has_edge(self, u, v):
        return u in self.adj and v in self.adj[u]

class WorldModel:
    """
    The Brain. Persistent memory and belief system.
    """
    def __init__(self):
        self.location_graph = SimpleGraph()
        self.beliefs: Dict[str, LocationBelief] = {}
        self.action_history = deque(maxlen=10)
        self.last_intention: Optional[IntentionType] = None
        self.start_time = time.time()
        self.npc_cooldowns: Dict[str, float] = {} # npc_id -> timestamp when allowed to talk again
        self.stuck_counter = 0
        self.consecutive_look_count = 0
        self.spoken_npcs: Set[str] = set()
        self.failed_npcs: Set[str] = set()
        self.dialogue_nodes_by_npc: Dict[str, Set[str]] = {}
        self.failed_edges: Dict[Tuple[str, str], Tuple[Any, ...]] = {}
        self.visit_counts: Dict[str, int] = {}
        
    def update(self, view: WorldView, last_action: str = None, last_result: str = None):
        loc_id = view.current_location_id

        # Update Dialogue Cooldowns
        if view.context == 'DIALOGUE' and view.dialogue_partner:
            # If we are talking, prevent starting new dialogue with this NPC for a while
            self.npc_cooldowns[view.dialogue_partner] = time.time() + 30.0
        
        # Detect Failed Dialogue Attempts
        # If we tried to talk but are NOT in dialogue, the NPC likely refused or has no tree.
        if last_action and last_action.startswith("talk "):
            parts = last_action.split(" ", 1)
            if len(parts) > 1:
                target_npc = parts[1]
                if view.context != 'DIALOGUE':
                    # Apply a cooldown to prevent infinite retry loops
                    self.npc_cooldowns[target_npc] = time.time() + 15.0
        
        # Update or Create Belief
        if loc_id not in self.beliefs:
            self.beliefs[loc_id] = LocationBelief(id=loc_id)
            self.location_graph.add_node(loc_id)
        
        belief = self.beliefs[loc_id]
        belief.last_visited = time.time()
        belief.explored_score = min(1.0, belief.explored_score + 0.1) # Visited means partially explored
        self.visit_counts[loc_id] = self.visit_counts.get(loc_id, 0) + 1

        if view.context == "DIALOGUE" and view.dialogue_partner:
            self.spoken_npcs.add(view.dialogue_partner)
        
        # Update graph connections
        for exit_dir in view.local_affordances['exits']:
            # We don't know where it leads yet unless we've been there, 
            # but we can mark it as an edge.
            # For now, we only add edges if we know the destination.
            # In a full V3, we'd track "unexplored edges".
            pass
            
        # Update Safety based on enemies
        if view.local_affordances['enemies']:
            belief.safety_score = max(0.0, belief.safety_score - 0.2)
            belief.known_enemies = view.local_affordances['enemies']
        else:
            belief.safety_score = min(1.0, belief.safety_score + 0.05) # Safety recovers slowly
            
        # Add to history
        if last_action:
            self.action_history.append({"action": last_action, "result": last_result, "loc": loc_id})

    def mark_connection(self, from_id, to_id):
        if not self.location_graph.has_edge(from_id, to_id):
            self.location_graph.add_edge(from_id, to_id)

    def get_safety(self, loc_id):
        return self.beliefs[loc_id].safety_score if loc_id in self.beliefs else 0.5

class IntentionPlanner:
    """
    High-level strategist. Decides WHY we are acting.
    """
    def decide_intention(self, world_model: WorldModel, view: WorldView) -> Intention:
        # 0. Stuck Break (Critical Priority)
        if world_model.stuck_counter > 5:
            return Intention(IntentionType.EXPLORE, 1.0, "Force Unstuck - Stuck Loop Detected")

        # 1. Survival Check (Highest Priority)
        status = view.player_status
        if status['hp_percent'] < 0.3:
            return Intention(IntentionType.SURVIVE, 1.0, "Health Critical", "heal")
        if status['hunger'] > 0.8:
            return Intention(IntentionType.SURVIVE, 0.9, "Starving", "eat")
            
        # 2. Context Overrides
        if view.context == 'COMBAT':
            # Unless we are dying (covered above), we fight or flee
            # Assess threat
            return Intention(IntentionType.COMBAT, 1.0, "In Combat")
            
        if view.context == 'DIALOGUE':
            return Intention(IntentionType.DIALOGUE, 1.0, "In Dialogue")
            
        if view.context == 'LOOTING':
            return Intention(IntentionType.LOOT, 1.0, "Looting enemy")
            
        if view.context == 'LEVEL_UP':
            return Intention(IntentionType.LEVEL_UP, 1.0, "Level Up Available")
            
        if view.context == 'QUEST_LOG':
            return Intention(IntentionType.QUEST_LOG, 1.0, "In Quest Log")
            
        if view.context == 'INVENTORY':
            return Intention(IntentionType.INVENTORY, 1.0, "In Inventory")
            
        if view.context == 'VATS':
            return Intention(IntentionType.VATS, 1.0, "Targeting Enemy")
            
        if view.context == 'CRAFTING':
            return Intention(IntentionType.CRAFTING, 1.0, "In Crafting Menu")
            
        # 3. Narrative / Quest (High Priority)
        # Speak to every NPC at least once; their dialogue can start or advance quests.
        for target_npc in view.local_affordances['npcs']:
            if target_npc not in world_model.spoken_npcs and target_npc not in world_model.failed_npcs:
                return Intention(IntentionType.DIALOGUE, 0.9, "Unvisited NPC", target_npc)

        # If we have an active quest, keep exploring for objectives and quest givers.
        if view.narrative_state['active_quests']:
            if not view.local_affordances['items']:
                 return Intention(IntentionType.EXPLORE, 0.8, "Exploring for Quest Objectives")

        # 4. Looting / Resources
        if view.local_affordances['items']:
             # If we aren't burdened or dying, loot
             return Intention(IntentionType.LOOT, 0.6, "Items spotted", view.local_affordances['items'][0])

        # 5. Exploration (Default)
        return Intention(IntentionType.EXPLORE, 0.5, "Exploring world")

class ActionArbiter:
    """
    Safety net to prevent stupid or repetitive actions.
    """
    def validate(self, command: str, world_model: WorldModel) -> str:
        history = world_model.action_history
        
        # Track consecutive 'look' commands
        if command == "look":
            world_model.consecutive_look_count += 1
        else:
            world_model.consecutive_look_count = 0
            
        # Rule 0: Prevent 'look' spam
        if world_model.consecutive_look_count > 1:
            return "stats"

        if not history:
            return command
            
        last_action = history[-1]['action']
        
        # Rule 1: Don't repeat identical commands if they failed (simplified here as we don't have explicit failure signal yet)
        if command == last_action and command.startswith("go "):
             # If we are stuck (determined by WorldModel stuck_counter elsewhere), we should allow a different command.
             # But here, if we blindly return the same command, we loop.
             pass

        # Rule 2: Oscillation detection (Go North -> Go South -> Go North)
        if len(history) >= 2:
            prev_action = history[-2]['action']
            if command == prev_action and command.startswith("go"):
                 # Detected oscillation
                 directions = ["north", "south", "east", "west"]
                 for d in directions:
                     if d in command:
                         # Break loop by forcing a look, which will trigger re-evaluation
                         return "look"
        
        return command

# --- Executors ---

class NavigationExecutor:
    def execute(self, view: WorldView, world_model: WorldModel, intention: Intention, engine=None) -> str:
        access_snapshot = None
        if engine:
            inventory = engine.state.inventory
            player = engine.state.player
            if player and inventory and player.is_overencumbered(inventory.get_total_weight()):
                heaviest_item = max(inventory.items, key=lambda item: item.weight, default=None)
                if heaviest_item:
                    return f"drop {heaviest_item.name}"

        # Occasional quest log check to verify UI state handling
        if random.random() < 0.05:
            return "quest"
        # Occasional inventory check
        if random.random() < 0.05:
            return "inventory"
        # Occasional crafting check
        if random.random() < 0.05:
            return "craft"

        exits = view.local_affordances['exits']
        if not exits:
            return "look" # Stuck?

        if engine:
            locations = engine.location_manager.locations
            start_id = view.current_location_id
            inventory_snapshot = tuple(sorted(self._inventory_names(engine)))
            player = engine.state.player
            access_snapshot = (
                inventory_snapshot,
                getattr(player, "level", None),
                bool(player and player.hit_points > player.max_hit_points * 0.5),
            )
            pending = [(start_id, 0, 0)]
            best_cost = {start_id: (0, 0)}
            first_directions = {}
            while pending:
                pending.sort(key=lambda entry: (entry[1], entry[2]))
                current_id, risk, distance = pending.pop(0)
                if best_cost.get(current_id) != (risk, distance):
                    continue
                location = locations.get(current_id)
                if not location:
                    continue
                for direction, destination in location.connections.items():
                    edge = (current_id, direction)
                    if edge in world_model.failed_edges:
                        if world_model.failed_edges[edge] == access_snapshot:
                            continue
                        del world_model.failed_edges[edge]
                    next_location = locations.get(destination)
                    if not next_location:
                        continue
                    properties = next_location.properties
                    hazard = int(bool(properties.get("hostile")) or bool(next_location.enemies))
                    hazard += int(properties.get("radiation_level", 0) >= 30)
                    next_cost = (risk + hazard, distance + 1)
                    if destination not in best_cost or next_cost < best_cost[destination]:
                        best_cost[destination] = next_cost
                        first_directions[destination] = (
                            first_directions.get(current_id) or direction
                        )
                        pending.append((destination, *next_cost))

            candidates = [
                (cost, location_id)
                for location_id, cost in best_cost.items()
                if location_id != start_id and location_id not in world_model.beliefs
            ]
            if candidates:
                _, target_id = min(candidates)
                direction = first_directions.get(target_id)
                if direction:
                    return f"go {direction}"

        available_exits = []
        for direction in exits:
            edge = (view.current_location_id, direction)
            failed_snapshot = world_model.failed_edges.get(edge)
            if failed_snapshot == access_snapshot:
                continue
            if failed_snapshot is not None:
                del world_model.failed_edges[edge]
            available_exits.append(direction)
        if not available_exits:
            return "look"
        if world_model.action_history:
            last_move = world_model.action_history[-1]["action"]
            opposites = {"north": "south", "south": "north", "east": "west", "west": "east"}
            if last_move.startswith("go "):
                backtrack_dir = opposites.get(last_move.split(" ")[-1])
                if backtrack_dir in available_exits and len(available_exits) > 1:
                    available_exits.remove(backtrack_dir)
        return f"go {random.choice(available_exits)}"

    @staticmethod
    def _inventory_names(engine) -> Set[str]:
        inventory = engine.state.inventory
        return {item.name for item in inventory.items} if inventory else set()

class CombatExecutor:
    def execute(self, view: WorldView, world_model: WorldModel, intention: Intention, engine) -> str:
        # Access combat manager for valid moves
        cm = engine.combat_manager
        
        # Fix: If combat manager says enemy is dead or None, but we are in CombatState,
        # we must advance the state. "attack" will fail or loop.
        if not cm or not cm.current_enemy or cm.current_enemy.hp <= 0:
             return "end turn" # Force turn end to trigger state transition
        
        # V3 Logic:
        # If HP low -> Heal (handled by SURVIVE intent usually, but tactical heal is good)
        # If AP low -> defend/reload
        # Else -> Attack (VATS or normal)
        
        player = engine.state.player
        health_ratio = player.hit_points / player.max_hit_points
        if health_ratio < 0.3:
            if engine.state.inventory.find_item("stimpak"):
                return "heal"
            return "flee"
        if health_ratio < 0.55 and engine.state.inventory.find_item("stimpak"):
            return "heal"
        if player.current_ap < cm.ATTACK_AP_COST:
            return "end turn"
        
        # Use VATS occasionally (simulated logic)
        if random.random() < 0.2 and not cm.in_vats and getattr(player, 'current_ap', 0) >= 5:
            return "vats"
            
        # Take cover if low health but no stimpaks?
        if player.hit_points / player.max_hit_points < 0.5 and random.random() < 0.3:
            return "take cover"

        # STRESS TEST: Command Hierarchy Fix
        # Attempt to equip items or use consumables during combat to verify they consume a turn.
        # Previously, these were free actions. Now, the enemy should attack back.
        if random.random() < 0.15:
            inv = engine.state.inventory
            # Try to swap weapon
            weapons = [i for i in inv.items if hasattr(i, 'damage')]
            if len(weapons) > 1:
                return f"equip {random.choice(weapons).name}"

        return "attack"

class DialogueExecutor:
    def execute(self, view: WorldView, world_model: WorldModel, intention: Intention, engine) -> str:
        if view.context == 'DIALOGUE':
            node = engine.current_dialogue_node
            if not node:
                return "bye"
            
            options = node.get_available_options(engine.state)
            if not options:
                return "bye"

            npc_id = view.dialogue_partner or ""
            visited = world_model.dialogue_nodes_by_npc.setdefault(npc_id, set())
            for index, option in enumerate(options, 1):
                if option.action:
                    return str(index)
            for index, option in enumerate(options, 1):
                if option.next_node and option.next_node not in visited:
                    return str(index)
            for index, option in enumerate(options, 1):
                if option.end_dialogue:
                    return str(index)
            return "bye"
            
        # If not in dialogue but want to be (Intent was DIALOGUE)
        if intention.target:
             return f"talk {intention.target}"
        
        # Fallback: If we see an NPC, talk to them
        if view.local_affordances['npcs']:
            target = view.local_affordances['npcs'][0]
            return f"talk {target}"
            
        return "look"

class SurvivalExecutor:
    def execute(self, view: WorldView, world_model: WorldModel, intention: Intention, engine=None) -> str:
        status = view.player_status
        if status['hp_percent'] < 0.5:
            if view.context == 'COMBAT':
                if engine and engine.state.inventory.find_item("stimpak"):
                    return "heal"
                return "flee"
            if engine and engine.state.inventory.find_item("stimpak"):
                return "use stimpak"
            return "camp"
        if status['hunger'] > 0.5:
            return "camp"
        return "camp" # Fallback rest

class LootExecutor:
    def execute(self, view: WorldView, world_model: WorldModel, intention: Intention, engine=None) -> str:
        # Avoid repeating take-all when the remaining loot cannot fit.
        if view.context == 'LOOTING':
            if engine:
                inventory = engine.state.inventory
                for item in engine.current_state.items:
                    if inventory.can_add_item(item):
                        return f"take {item.name}"
                return "done"
            if view.local_affordances['items']:
                return "take all"
            return "done"
            
        items = view.local_affordances['items']
        if items:
            if engine:
                location = engine.location_manager.get_location(
                    engine.state.current_location
                )
                inventory = engine.state.inventory
                if location and not any(
                    inventory.can_add_item(item) for item in location.items
                ):
                    return NavigationExecutor().execute(
                        view, world_model, intention, engine
                    )
            return "loot"
        return "look"

class LevelUpExecutor:
    def execute(self, view: WorldView, world_model: WorldModel, intention: Intention, engine) -> str:
        state = engine.current_state
        # Check if we are actually in LevelUpState (sanity check)
        if not hasattr(state, "sub_state"):
             return "1"
             
        if state.sub_state == "main":
             # Prioritize stats (1)
             return "1"
        elif state.sub_state == "special":
             # Pick random stat 1-7 to avoid getting stuck on maxed stats
             return str(random.randint(1, 7))
        elif state.sub_state == "perks":
             # Pick first perk
             return "1"
        
        return "1"

class QuestLogExecutor:
    def execute(self, view: WorldView, world_model: WorldModel, intention: Intention, engine=None) -> str:
        return "close"

class InventoryExecutor:
    def execute(self, view: WorldView, world_model: WorldModel, intention: Intention, engine=None) -> str:
        return "close"

class VatsExecutor:
    def execute(self, view: WorldView, world_model: WorldModel, intention: Intention, engine=None) -> str:
        # Check AP to avoid stuck loop
        if getattr(engine.state.player, 'current_ap', 0) < 5:
            return "exit"

        # Simple logic: Aim for the head if chance is decent, else Torso
        chances = engine.combat_manager.get_vats_chances()
        if chances.get("Head", 0) > 60:
            return "1" # Head is usually index 1
        return "2" # Torso

class CraftingExecutor:
    def execute(self, view: WorldView, world_model: WorldModel, intention: Intention, engine=None) -> str:
        return "close"

class AutoplayerV3:
    def __init__(self, engine, max_steps: int = 1000):
        self.engine = engine
        self.perception = PerceptionLayer()
        self.world_model = WorldModel()
        self.planner = IntentionPlanner()
        self.arbiter = ActionArbiter()
        
        self.executors = {
            IntentionType.EXPLORE: NavigationExecutor(),
            IntentionType.COMBAT: CombatExecutor(),
            IntentionType.DIALOGUE: DialogueExecutor(),
            IntentionType.SURVIVE: SurvivalExecutor(),
            IntentionType.LOOT: LootExecutor(),
            IntentionType.REST: SurvivalExecutor(), # Reuse
            IntentionType.WAIT: NavigationExecutor(), # Fallback
            IntentionType.QUEST: NavigationExecutor(), # Fallback for now
            IntentionType.LEVEL_UP: LevelUpExecutor(),
            IntentionType.QUEST_LOG: QuestLogExecutor(),
            IntentionType.INVENTORY: InventoryExecutor(),
            IntentionType.VATS: VatsExecutor(),
            IntentionType.CRAFTING: CraftingExecutor()
        }
        
        self.last_command = None
        self.step_count = 0
        self.max_steps = max_steps
        self.start_time = time.time()
        self.items_looted = 0
        self.combat_encounters_total = 0
        self.combat_encounters_won = 0
        self.damage_dealt_total = 0.0
        self.damage_taken_total = 0.0
        self.move_attempts = 0
        self.move_successes = 0
        self.movement_failures = 0
        self.stuck_events = 0
        self.loop_events = 0
        self.dialogue_nodes_visited: Set[str] = set()
        self.npc_attempts: Set[str] = set()
        self.npcs_spoken_to: Set[str] = set()
        self.items_collected: Set[str] = set()
        self.edge_cases_run: List[str] = []
        self.action_counts: Dict[str, int] = {}
        self.failure_examples: List[Dict[str, str]] = []
        self.engine_errors: List[str] = []
        self.engine_error_count = 0
        self.death_count = 0
        self.quest_ids_started: Set[str] = set()
        self.quest_ids_completed: Set[str] = set()
        self.quest_log_visits = 0
        self.inventory_visits = 0
        self.vats_visits = 0
        self.vats_low_ap_exits = 0
        self.crafting_visits = 0

        self.in_combat = False
        self.last_player_hp = 0
        self.last_enemy_hp = 0
        self.last_enemy_id = None
        self.last_location_id = None
        self.last_inv_count = 0
        self.pending_action = None
        self.last_unprogressed_action = None
        self.connectivity_before = analyze_location_connectivity(engine.location_manager.locations)
        self.connectivity_after = self.connectivity_before
        self.all_location_ids = set(engine.location_manager.locations)
        self.all_npc_ids = {
            npc_id
            for location in engine.location_manager.locations.values()
            for npc_id in location.npcs
        }
        self.all_item_names = {
            item.name
            for location in engine.location_manager.locations.values()
            for item in location.items
        }

    def _inventory_names(self) -> Set[str]:
        inventory = self.engine.state.inventory
        return {item.name for item in inventory.items} if inventory else set()

    def _state_signature(self):
        player = self.engine.state.player
        enemy = self.engine.combat_manager.current_enemy if self.engine.combat_manager else None
        inventory = self.engine.state.inventory
        return (
            self.engine.state.current_location,
            type(self.engine.current_state).__name__,
            getattr(player, "hit_points", None),
            getattr(player, "hunger", None),
            getattr(player, "thirst", None),
            getattr(player, "radiation", None),
            tuple(sorted(
                (item.name, getattr(item, "quantity", 1))
                for item in inventory.items
            )) if inventory else (),
            getattr(enemy, "hp", None),
            tuple(sorted(
                (quest_id, getattr(getattr(quest, "state", None), "value", None))
                for quest_id, quest in self.engine.quest_manager.quests.items()
            )),
            json.dumps(self.engine.state.world_flags, sort_keys=True, default=str),
            getattr(self.engine.current_dialogue_node, "node_id", None),
        )

    def _update_quest_metrics(self):
        for quest_id, quest in self.engine.quest_manager.quests.items():
            state = getattr(getattr(quest, "state", None), "value", None)
            if state == "active":
                self.quest_ids_started.add(quest_id)
            elif state == "completed":
                self.quest_ids_started.add(quest_id)
                self.quest_ids_completed.add(quest_id)

    def _record_previous_action(self):
        pending = self.pending_action
        if not pending:
            return

        current_signature = self._state_signature()
        if current_signature == pending["signature"]:
            if self.last_unprogressed_action == pending["command"]:
                self.loop_events += 1
                if len(self.failure_examples) < 20:
                    self.failure_examples.append({
                        "action": pending["command"],
                        "location": pending["location"],
                        "result": "Repeated action produced no observable game-state change",
                    })
            self.last_unprogressed_action = pending["command"]
        else:
            self.last_unprogressed_action = None

        current_location = self.engine.state.current_location
        if (
            pending["command"].startswith("go ")
            and pending["command"] != "go autoplayer_probe"
        ):
            if current_location != pending["location"]:
                self.move_successes += 1
                self.world_model.stuck_counter = 0
            else:
                self.movement_failures += 1
                self.stuck_events += 1
                direction = pending["command"][3:]
                player = self.engine.state.player
                self.world_model.failed_edges[(pending["location"], direction)] = (
                    tuple(sorted(self._inventory_names())),
                    getattr(player, "level", None),
                    bool(player and player.hit_points > player.max_hit_points * 0.5),
                )
                self.world_model.stuck_counter += 1
                if len(self.failure_examples) < 20:
                    self.failure_examples.append({
                        "action": pending["command"],
                        "location": pending["location"],
                        "result": "No location change",
                    })
        elif pending["command"].startswith("talk "):
            if isinstance(self.engine.current_state, DialogueState):
                self.npcs_spoken_to.add(self.engine.current_state.npc_id)
            else:
                npc_id = pending["command"][5:]
                self.world_model.failed_npcs.add(npc_id)
                if len(self.failure_examples) < 20:
                    self.failure_examples.append({
                        "action": pending["command"],
                        "location": pending["location"],
                        "result": "No dialogue opened",
                    })

        current_items = self._inventory_names()
        self.items_collected.update(current_items - pending["inventory"])
        self.items_looted += len(current_items - pending["inventory"])
        self._update_quest_metrics()
        self.pending_action = None

    def tick(self, prompt: str = "") -> str:
        """
        Main cognitive cycle. Returns a string command to execute.
        """
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        prompt_clean = ansi_escape.sub('', prompt).strip().lower()
        
        if "what is your name" in prompt_clean:
             return "AutoBotV3"
        if "select stat" in prompt_clean or "which stat" in prompt_clean:
             return str(random.randint(1, 7))
        if "choose a perk" in prompt_clean:
             return "1"
        if "are you sure" in prompt_clean:
             player = self.engine.state.player
             return "y" if player and player.hit_points > player.max_hit_points * 0.5 else "n"
        if "choose option [1-5]" in prompt_clean:
             self.death_count += 1
             return "3"
        if "choice" in prompt_clean or "select an option" in prompt_clean:
             return "1"
        if any(x in prompt_clean for x in ["press enter", "continue", "to proceed"]):
             return ""

        if not prompt_clean.startswith("[") or not self.engine.state.player:
             return "1" if "select" in prompt_clean else ""

        self._record_previous_action()
        if self.step_count >= self.max_steps:
             raise SystemExit(0)
        self.step_count += 1

        # --- METRICS TRACKING ---
        
        # 1. Combat Metrics
        is_combat = isinstance(self.engine.current_state, CombatState)
        
        if is_combat:
            player = self.engine.state.player
            cm = self.engine.combat_manager
            enemy = cm.current_enemy if cm else None
            
            if not self.in_combat: # Just entered combat
                self.combat_encounters_total += 1
                self.in_combat = True
                self.last_player_hp = player.hit_points
                if enemy:
                    self.last_enemy_hp = enemy.hp
                    self.last_enemy_id = id(enemy)
            else:
                # Still in combat
                # Track Player Damage
                if player.hit_points < self.last_player_hp:
                    diff = self.last_player_hp - player.hit_points
                    if diff > 0: self.damage_taken_total += diff
                self.last_player_hp = player.hit_points
                
                # Track Enemy Damage
                if enemy and id(enemy) == self.last_enemy_id:
                    if enemy.hp < self.last_enemy_hp:
                        diff = self.last_enemy_hp - enemy.hp
                        if diff > 0: self.damage_dealt_total += diff
                    self.last_enemy_hp = enemy.hp
                elif enemy:
                    # Switched target
                    self.last_enemy_id = id(enemy)
                    self.last_enemy_hp = enemy.hp
                    
        else:
            if self.in_combat: # Just left combat
                enemy = self.engine.combat_manager.current_enemy
                if (
                    self.engine.state.player.hit_points > 0
                    and enemy
                    and enemy.hp <= 0
                ):
                     self.combat_encounters_won += 1
                self.in_combat = False
        
        # 2. Dialogue Metrics
        if isinstance(self.engine.current_state, DialogueState):
            node = self.engine.current_dialogue_node
            if node:
                self.dialogue_nodes_visited.add(node.node_id)
        
        # 3. Quest Log Metrics
        if QuestLogState and isinstance(self.engine.current_state, QuestLogState):
            self.quest_log_visits += 1
            
        # 4. Inventory Metrics
        if InventoryState and isinstance(self.engine.current_state, InventoryState):
            self.inventory_visits += 1
            
        # 5. VATS Metrics
        if VatsState and isinstance(self.engine.current_state, VatsState):
            self.vats_visits += 1
            
        # 6. Crafting Metrics
        if CraftingState and isinstance(self.engine.current_state, CraftingState):
            self.crafting_visits += 1

        # 1. Perceive
        view = self.perception.scan(self.engine)
        
        # 2. Update Model
        self.world_model.update(view, self.last_command)
        if view.context == "DIALOGUE" and self.engine.current_dialogue_node:
            self.world_model.dialogue_nodes_by_npc.setdefault(
                view.dialogue_partner or "", set()
            ).add(self.engine.current_dialogue_node.node_id)
        self.all_npc_ids.update(view.local_affordances["npcs"])
        self.all_item_names.update(view.local_affordances["items"])
        self._update_quest_metrics()
        
        # 3. Plan
        intention = self.planner.decide_intention(self.world_model, view)
        
        # 4. Execute
        executor = self.executors.get(intention.type)
        if intention.type in [IntentionType.COMBAT, IntentionType.DIALOGUE, IntentionType.LOOT, IntentionType.LEVEL_UP, IntentionType.QUEST_LOG, IntentionType.INVENTORY, IntentionType.VATS, IntentionType.CRAFTING, IntentionType.EXPLORE, IntentionType.WAIT, IntentionType.QUEST, IntentionType.SURVIVE, IntentionType.REST]:
             # These need engine access for context
             raw_command = executor.execute(view, self.world_model, intention, self.engine)
        else:
             raw_command = executor.execute(view, self.world_model, intention)

        edge_case_commands = (
            "zz_autoplayer_probe",
            "go autoplayer_probe",
            "take autoplayer_missing_item",
            "talk autoplayer_missing_npc",
        )
        if (
            view.context == "EXPLORATION"
            and len(self.edge_cases_run) < len(edge_case_commands)
            and self.step_count >= (len(self.edge_cases_run) + 1) * 200
        ):
            raw_command = edge_case_commands[len(self.edge_cases_run)]
            self.edge_cases_run.append(raw_command)
        
        # Track VATS low AP exits
        if intention.type == IntentionType.VATS and raw_command == "exit":
            self.vats_low_ap_exits += 1

        # 5. Arbitrate
        final_command = self.arbiter.validate(raw_command, self.world_model)
        location_id = self.engine.state.current_location
        self.action_counts[final_command] = self.action_counts.get(final_command, 0) + 1

        if final_command.startswith("go ") and final_command != "go autoplayer_probe":
            self.move_attempts += 1
        if final_command.startswith("talk "):
            self.npc_attempts.add(final_command[5:])

        self.pending_action = {
            "command": final_command,
            "location": location_id,
            "inventory": self._inventory_names(),
            "signature": self._state_signature(),
        }
        self.last_command = final_command
        return final_command

    def generate_report(self, output_dir: str = "autoplayer_reports", runtime_error: str = None):
        self._record_previous_action()
        self.connectivity_after = analyze_location_connectivity(
            self.engine.location_manager.locations
        )
        self._update_quest_metrics()

        duration = time.time() - self.start_time
        visited_locations = set(self.world_model.beliefs)
        location_count = len(self.all_location_ids)
        location_coverage = len(visited_locations) / location_count if location_count else 0.0
        npc_count = len(self.all_npc_ids)
        npc_coverage = len(self.npcs_spoken_to) / npc_count if npc_count else 0.0
        movement_success_rate = (
            self.move_successes / self.move_attempts if self.move_attempts else 0.0
        )
        blocked_edges = [
            {"from": location_id, "direction": direction}
            for location_id, direction in sorted(self.world_model.failed_edges)
        ]
        active_quests = sorted(
            quest_id
            for quest_id, quest in self.engine.quest_manager.quests.items()
            if getattr(getattr(quest, "state", None), "value", None) == "active"
        )
        current_location_ids = set(self.engine.location_manager.locations)
        self.all_location_ids.update(current_location_ids)
        player = self.engine.state.player

        critique = []
        if self.engine_error_count:
            critique.append(
                f"The engine reported {self.engine_error_count} error(s); "
                f"first: {self.engine_errors[0]}."
            )
        if runtime_error:
            critique.append(f"The game run raised {runtime_error}.")
        if not self.connectivity_before["strongly_connected"]:
            critique.append(
                "The world map is not mutually reachable in the directed travel graph; "
                "see unreachable_from and dangling_exits."
            )
        if self.step_count < self.max_steps:
            critique.append(
                f"The run stopped after {self.step_count} actions, short of the "
                f"{self.max_steps}-action target."
            )
        if location_coverage < 1.0:
            missing = sorted(self.all_location_ids - visited_locations)
            critique.append(
                f"Exploration reached {len(visited_locations)}/{len(self.all_location_ids)} "
                f"locations; unvisited: {', '.join(missing[:12])}."
            )
        if self.move_attempts and movement_success_rate < 0.9:
            critique.append(
                f"Only {self.move_successes}/{self.move_attempts} travel attempts succeeded."
            )
        if blocked_edges:
            critique.append(
                f"{len(blocked_edges)} travel edge(s) remained blocked under the current "
                "inventory and player state."
            )
        if self.loop_events:
            critique.append(
                f"Detected {self.loop_events} repeated actions without location progress."
            )
        if self.death_count:
            critique.append(
                f"The player died and respawned {self.death_count} time(s); review "
                "combat difficulty and healing access."
            )
        if npc_count and npc_coverage < 1.0:
            missing_npcs = sorted(self.all_npc_ids - self.npcs_spoken_to)
            critique.append(
                f"NPC dialogue coverage was {len(self.npcs_spoken_to)}/{npc_count}; "
                f"unspoken: {', '.join(missing_npcs[:12])}."
            )
        if self.quest_ids_started and not self.quest_ids_completed:
            critique.append("Quests were started but none completed during the run.")
        if not self.items_collected:
            critique.append("No items were collected.")
        if not critique:
            critique.append("No playability issues crossed the current reporting thresholds.")

        report = {
            "steps": {"completed": self.step_count, "target": self.max_steps},
            "duration_seconds": round(duration, 2),
            "connectivity_before": self.connectivity_before,
            "connectivity_after": self.connectivity_after,
            "exploration": {
                "visited": sorted(visited_locations),
                "visited_count": len(visited_locations),
                "location_count": len(self.all_location_ids),
                "coverage": round(location_coverage, 4),
                "unvisited": sorted(self.all_location_ids - visited_locations),
                "move_attempts": self.move_attempts,
                "move_successes": self.move_successes,
                "move_failures": self.movement_failures,
                "move_success_rate": round(movement_success_rate, 4),
                "stuck_events": self.stuck_events,
                "loop_events": self.loop_events,
                "blocked_edges": blocked_edges,
            },
            "npcs": {
                "spoken_to": sorted(self.npcs_spoken_to),
                "attempted": sorted(self.npc_attempts),
                "count": npc_count,
                "coverage": round(npc_coverage, 4),
                "unspoken": sorted(self.all_npc_ids - self.npcs_spoken_to),
            },
            "items": {
                "collected": sorted(self.items_collected),
                "count": len(self.items_collected),
                "visible_world_items": sorted(self.all_item_names),
            },
            "quests": {
                "started": sorted(self.quest_ids_started),
                "completed": sorted(self.quest_ids_completed),
                "active_at_end": active_quests,
            },
            "combat": {
                "encounters": self.combat_encounters_total,
                "won": self.combat_encounters_won,
                "damage_dealt": round(self.damage_dealt_total, 1),
                "damage_taken": round(self.damage_taken_total, 1),
            },
            "player": {
                "location": self.engine.state.current_location,
                "level": player.level if player else None,
                "experience": player.experience if player else None,
                "experience_to_next_level": (
                    player.experience_to_next if player else None
                ),
                "hit_points": player.hit_points if player else None,
                "max_hit_points": player.max_hit_points if player else None,
                "deaths_and_respawns": self.death_count,
            },
            "actions": dict(sorted(self.action_counts.items())),
            "edge_cases": self.edge_cases_run,
            "failure_examples": self.failure_examples,
            "engine_error_count": self.engine_error_count,
            "engine_errors": self.engine_errors,
            "critique": critique,
        }
        if runtime_error:
            report["runtime_error"] = runtime_error

        os.makedirs(output_dir, exist_ok=True)
        report_stem = f"autoplayer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        json_path = os.path.join(output_dir, report_stem + ".json")
        text_path = os.path.join(output_dir, report_stem + ".txt")
        with open(json_path, "w", encoding="utf-8") as report_file:
            json.dump(report, report_file, indent=2, ensure_ascii=False)

        summary = [
            "Fallout Berlin Autoplayer Playability Report",
            f"Actions: {self.step_count}/{self.max_steps}",
            f"Connectivity: {'PASS' if self.connectivity_after['strongly_connected'] else 'FAIL'} "
            f"({self.connectivity_after['location_count']} locations)",
            f"Exploration: {len(visited_locations)}/{len(self.all_location_ids)} locations",
            f"Movement: {self.move_successes}/{self.move_attempts} successful; "
            f"{self.movement_failures} failed",
            f"NPCs: {len(self.npcs_spoken_to)}/{npc_count} spoken to",
            f"Items collected: {len(self.items_collected)}",
            f"Quests started/completed: {len(self.quest_ids_started)}/{len(self.quest_ids_completed)}",
            f"Combat: {self.combat_encounters_won}/{self.combat_encounters_total} won",
            f"Player: {player.hit_points}/{player.max_hit_points} HP, "
            f"level {player.level}, deaths/respawns {self.death_count}" if player else "Player: unavailable",
            f"Engine errors: {self.engine_error_count}",
            "Critique:",
            *[f"- {finding}" for finding in critique],
            f"JSON: {json_path}",
        ]
        if player:
            summary.insert(
                9,
                f"XP: {player.experience}/{player.experience_to_next} to next level",
            )
        with open(text_path, "w", encoding="utf-8") as report_file:
            report_file.write("\n".join(summary) + "\n")
        print("\n" + "\n".join(summary))
        return report


def run_v3_simulation():
    try:
        from fallout_berlin.improved_game_engine import ImprovedGameEngine
    except ImportError:
        from fallout_berlin.game_engine import ImprovedGameEngine
    from unittest.mock import patch
    from contextlib import redirect_stdout
    from io import StringIO

    random.seed(42)
    
    engine = ImprovedGameEngine()
    engine.config.autosave_enabled = False
    engine.ui_manager.clear_screen = lambda: None
    bot = AutoplayerV3(engine)

    def record_engine_error(error):
        bot.engine_error_count += 1
        if len(bot.engine_errors) < 100:
            frames = traceback.extract_tb(error.__traceback__)
            location = f" ({os.path.basename(frames[-1].filename)}:{frames[-1].lineno})" if frames else ""
            bot.engine_errors.append(f"{type(error).__name__}: {error}{location}")

    # Collect engine errors for the report without touching game save files.
    engine._handle_error = record_engine_error

    def mock_input(prompt=""):
        if bot.step_count >= bot.max_steps:
            raise SystemExit(0)
        return bot.tick(prompt)

    output = StringIO()
    run_error = None
    try:
        with patch("builtins.input", side_effect=mock_input), redirect_stdout(output):
            engine.running = True
            engine.start_new_game()
            while bot.step_count < bot.max_steps:
                engine.game_loop()
                player = engine.state.player
                if bot.step_count >= bot.max_steps or not player or player.hit_points > 0:
                    break

                bot.death_count += 1
                player.hit_points = max(15, player.max_hit_points // 2)
                player.radiation = min(player.radiation, 300)
                player.hunger = min(player.hunger, 40)
                player.thirst = min(player.thirst, 40)
                player.is_alive = True
                engine.state.current_location = "checkpoint_charlie"
                engine.combat_manager.in_combat = False
                engine.combat_manager.current_enemy = None
                engine.running = True
                engine.change_state(ExplorationState(engine))
    except SystemExit:
        pass
    except Exception as error:
        run_error = f"{type(error).__name__}: {error}"

    report = bot.generate_report(runtime_error=run_error)
    if run_error:
        raise RuntimeError(f"Autoplayer run failed: {run_error}")

if __name__ == "__main__":
    run_v3_simulation()
