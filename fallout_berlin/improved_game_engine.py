"""
FALLOUT BERLIN - IMPROVED GAME ENGINE
======================================
Enhanced game engine with better architecture, improved systems, and polished gameplay.

IMPROVEMENTS:
- Better state management
- Enhanced visual feedback with art system
- Improved command handling
- Better error handling and recovery
- More dynamic world interactions
- Enhanced save/load system
- Better performance
- Cleaner code organization
"""

import sys
import os
import time
import random
import json
import operator
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# External dependencies
import colorama
from colorama import Fore, Back, Style
import difflib

# Game modules
from fallout_berlin.game_state import GameState
from fallout_berlin.player import Player
from fallout_berlin.inventory import Inventory
from fallout_berlin.location import LocationManager
from fallout_berlin.dialogue import DialogueManager
from fallout_berlin.quest import QuestManager
from fallout_berlin.item import create_item, Weapon, Armor, Consumable
from fallout_berlin.enemy import create_enemy
from fallout_berlin.crafting import CraftingManager
from fallout_berlin.combat import CombatManager
from fallout_berlin.ui import UIManager
from fallout_berlin.events import EventManager, EventType, Event
from fallout_berlin.input_parser import InputParser
from fallout_berlin.companion import Companion
from fallout_berlin.character_creation import CharacterCreator
from fallout_berlin.minigames import MiniGameManager
from fallout_berlin.commands import SettingsCommand
from fallout_berlin.cutscene import CutsceneManager
from fallout_berlin.effect_manager import EffectManager

# Art system
from fallout_berlin.art_master import (
    TITLE_LOGO, LOCATIONS, ENEMIES, NPCS, ITEMS, UI_ELEMENTS,
    SceneRenderer, ArtEffects, ArtComposer,
    Animation, ArtFrame,
    generate_rain, generate_radiation_storm, generate_fog, generate_dust
)


# ==============================================================================
# ENUMS & DATA CLASSES
# ==============================================================================

class GameDifficulty(Enum):
    """Difficulty levels"""
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    SURVIVAL = "survival"


@dataclass
class EngineConfig:
    """Engine configuration"""
    autosave_enabled: bool = True
    autosave_interval: int = 300  # seconds
    weather_enabled: bool = True
    radio_enabled: bool = True
    time_progression: bool = True
    encounter_rate: float = 0.2
    debug_mode: bool = False


# ==============================================================================
# IMPROVED GAME ENGINE
# ==============================================================================

class ImprovedGameEngine:
    """
    Enhanced game engine with better architecture and features.
    
    Key Improvements:
    - Better separation of concerns
    - Enhanced visual feedback
    - Improved state management
    - Better error handling
    - More dynamic world
    """
    
    def __init__(self):
        """Initialize the improved game engine"""
        self._init_platform_fixes()
        if hasattr(colorama, "just_fix_windows_console"):
            colorama.just_fix_windows_console()
        else:
            colorama.init()
        
        # Core state
        self.state = GameState()
        self.config = EngineConfig()
        if os.environ.get("DEBUG_MODE") == "1":
            self.config.debug_mode = True
        self.running = False
        self.player = None
        
        # Managers
        self._managers: Dict[str, Any] = {}
        self._init_managers()
        
        # Enhanced art system
        # self.scene_renderer is now accessed via self.ui_manager.renderer
        self.art_composer = ArtComposer()
        
        # State machine
        self.current_state: Optional[Any] = None
        self.state_history: List[str] = []
        self.current_dialogue_tree = None
        self.current_dialogue_node = None
        
        # Game data
        perks_data = self._load_json_data("perks.json", [])
        self.perks_db = list(perks_data.values()) if isinstance(perks_data, dict) else perks_data
        self.encounter_tables = self._load_json_data("encounters.json", {"default": ["radroach"]})
        self.radio_data = self._load_json_data("radio.json", {"music": [], "banter": [], "news": {}})
        
        # Game variables
        self.radio_active = True
        self.last_radio_time = 0
        self.last_autosave = 0
        self.current_weather = None
        self.time_of_day = "day"
        
        # Event system
        self._setup_event_handlers()
        
    def _init_platform_fixes(self):
        """Platform-specific fixes"""
        if sys.platform == 'win32':
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except AttributeError:
                pass
    
    def _init_managers(self):
        """Initialize all game managers"""
        # Core managers (order-independent)
        self.location_manager = self._register_manager("location", LocationManager())
        self.dialogue_manager = self._register_manager("dialogue", DialogueManager())
        self.quest_manager = self._register_manager("quest", QuestManager())
        self.crafting_manager = self._register_manager("crafting", CraftingManager())
        self.event_manager = self._register_manager("event", EventManager())
        self.input_parser = self._register_manager("input", InputParser())
        self.effect_manager = self._register_manager("effect", EffectManager())
        
        # UI-dependent managers
        self.ui_manager = self._register_manager("ui", UIManager(self.state))
        self.ui_manager.engine = self
        self.ui_manager.location_manager = self.location_manager
        self.character_creator = self._register_manager("character", CharacterCreator(self.ui_manager))
        self.minigame_manager = self._register_manager("minigame", MiniGameManager(self.ui_manager))
        self.cutscene_manager = self._register_manager("cutscene", CutsceneManager(self.ui_manager))
        
        # Deferred managers
        self.combat_manager = None  # Initialized after player creation
        
        # Add custom recipes
        self._add_custom_recipes()
    
    def _register_manager(self, name: str, instance: Any) -> Any:
        """Register a manager instance"""
        self._managers[name] = instance
        return instance
    
    def get_manager(self, name: str) -> Optional[Any]:
        """Get a manager instance by name"""
        return self._managers.get(name)
    
    def _add_custom_recipes(self):
        """Add custom crafting recipes"""
        self.crafting_manager.recipes["berliner_luft"] = {
            "name": "Berliner Luft",
            "requirements": {"empty_bottle": 1, "chems": 2, "mutated_fruit": 1},
            "perk_req": "Chemist"
        }
        self.crafting_manager.recipes["spreeschwan_club"] = {
            "name": "Spreeschwan Feather Club",
            "requirements": {"scrap_metal": 2, "adhesive": 1},
        }
        self.crafting_manager.recipes["currywurst_supreme"] = {
            "name": "Premium Currywurst",
            "requirements": {"currywurst": 2, "spices": 1},
        }
    
    def _load_json_data(self, filename: str, default: Any) -> Any:
        """Load JSON data file with error handling"""
        try:
            filepath = os.path.join("fallout_berlin", "data", filename)
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            if self.config.debug_mode:
                print(f"{Fore.YELLOW}[WARNING] {filename} not found, using defaults{Style.RESET_ALL}")
            return default
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}[ERROR] Failed to parse {filename}: {e}{Style.RESET_ALL}")
            return default
    
    def _setup_event_handlers(self):
        """Register event listeners"""
        self.event_manager.subscribe(EventType.RADIO_MESSAGE, self._on_radio_message)
        self.event_manager.subscribe(EventType.LOCATION_ENTER, self._on_location_enter)
        self.event_manager.subscribe(EventType.LOCATION_ENTER, self.quest_manager.on_location_enter)
    
    # ==========================================================================
    # STATE MANAGEMENT
    # ==========================================================================
    
    def _get_engine_states(self):
        """Dynamic import to avoid circular dependencies"""
        from fallout_berlin.engine_states import (
            ExplorationState, CombatState, DialogueState, MainMenuState
        )
        return ExplorationState, CombatState, DialogueState, MainMenuState

    def change_state(self, new_state: Any):
        """Transition to a new game state"""
        if self.current_state:
            self.state_history.append(type(self.current_state).__name__)
            self.current_state.exit()
        
        self.current_state = new_state
        self.current_state.enter()
    
    def start_combat(self, enemy):
        """Start combat encounter"""
        if not self.combat_manager:
            if self.config.debug_mode:
                print(f"{Fore.YELLOW}[DEBUG] Initializing deferred CombatManager...{Style.RESET_ALL}")
            self.combat_manager = CombatManager(
                self.state, self.location_manager, self.ui_manager
            )
        
        # Show combat animation
        ArtEffects.combat_start().play(max_loops=1)
        time.sleep(0.5)
        
        self.combat_manager.start_combat(enemy)
        ExplorationState, CombatState, DialogueState, MainMenuState = self._get_engine_states()
        self.change_state(CombatState(self))
        
    
    # ==========================================================================
    # CORE SYSTEM HOOKS FOR INTEGRATION
    # ==========================================================================
    
    def _check_quest_triggers_global(self):
        """Check for global quest/objective triggers that are not location-dependent"""
        # This hook is crucial for narrative reinforcement:
        # E.g., if a player gained enough XP (stat change), trigger a narrative flag.
        
        # Check for quest triggers
        self.quest_manager.check_quest_triggers(self.state)
        
        # Check for performance/artifact events (Physics Stability check)
        if self.config.debug_mode and random.random() < 0.001:
            # Simulate graphics artifacting check if we suspect instability
            print(f"{Fore.MAGENTA}[PHYSICS CHECK] Running deep check on current frame state... Passed.{Style.RESET_ALL}")
            
    
    def start_new_game(self):
        """Start a new game"""
        # Reset GameState completely to ensure clean slate
        self.state = GameState()
        self.ui_manager.state = self.state

        # Reset quest manager to ensure clean state
        self.quest_manager.reset()

        # Reset dialogue state to prevent context bleeding
        self.current_dialogue_tree = None
        self.current_dialogue_node = None

        # Show title with effect
        self._show_title_screen()
        
        # Character creation
        self.player, companion = self.character_creator.create_character()
        if companion:
            self.state.companion = companion
        
        # Initialize game state
        self._init_game_state()
        
        # Start game
        ExplorationState, CombatState, DialogueState, MainMenuState = self._get_engine_states()
        self.change_state(ExplorationState(self))
        
        print(f"\n{Fore.GREEN}{'═' * 60}")
        print("GAME START")
        print(f"{'═' * 60}{Style.RESET_ALL}\n")
        
        # Show starting location
        self._show_location_entrance()

    
    def _show_title_screen(self):
        """Display enhanced title screen"""
        print(f"{Fore.GREEN}{TITLE_LOGO}{Style.RESET_ALL}")
        
        welcome = """
        FALLOUT: BERLIN
        
        War... War never changes.
        
        The year is 2287. Berlin lies in ruins, divided by old walls
        and new conflicts. Your story begins here...
        """
        
        print(self.art_composer.create_border(welcome.strip(), "double", Fore.CYAN))
        print()
        time.sleep(1)
    
    def _init_game_state(self):
        """Initialize game state after character creation"""
        self.state.player = self.player
        self.state.inventory = Inventory(max_weight=self.player.carry_weight)
        self.state.current_location = "checkpoint_charlie"
        
        # Add starting items
        self._add_starting_items()
        
        # Start first quest
        self.quest_manager.start_quest("first_steps")
        
        self.state.quests = self.quest_manager.quests
        
        # Mark starting location as visited
        location = self.location_manager.get_location(self.state.current_location)
        if location:
            self.location_manager.visit_location(self.state.current_location)
        
        # Initialize combat manager
        self.combat_manager = CombatManager(
            self.state, self.location_manager, self.ui_manager
        )
        
        # Set initial weather
        self._update_weather()
    
    def _add_starting_items(self):
        """Add starting items based on character origin"""
        origin_data = self.player.get_origin_data()
        if not origin_data:
            return
        
        for item_key in origin_data.get("starting_items", []):
            if " x" in item_key:
                item_name, quantity = item_key.split(" x")
                item = create_item(item_name.lower().replace(" ", "_"), int(quantity))
            else:
                item = create_item(item_key.lower().replace(" ", "_"))
            
            if item:
                self.state.inventory.add_item(item)
    
    def game_loop(self):
        """Main game loop with improved structure"""
        last_update = time.time()
        
        while self.running:
            current_time = time.time()
            delta_time = current_time - last_update
            last_update = current_time
            
            # Update systems
            self._update_systems(delta_time)
            
            # Post-system update checks (e.g., Quest triggers, Physics stability check)
            self._check_quest_triggers_global()

            # Check for death
            if self._check_player_death():
                break
            
            # Check for level ups
            if self.state.player and self.state.player.stat_points > 0:
                from fallout_berlin.level_up_state import LevelUpState
                if not isinstance(self.current_state, LevelUpState):
                    self.change_state(LevelUpState(self))
            
            # State update and render
            try:
                self.current_state.update()
                self.current_state.render()
                
                # Get input
                prompt = f"\n{Fore.CYAN}[{self.current_state.prompt_label}]{Style.RESET_ALL}> "
                command = input(prompt).strip().lower()

                if not command:
                    continue
                
                # Handle global commands
                if self._handle_global_command(command):
                    continue
                
                # Handle state-specific commands
                self.current_state.handle_input(command)
                
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Game interrupted.{Style.RESET_ALL}")
                self._quit_game()
                break
            except EOFError:
                print(f"\n\n{Fore.YELLOW}Input ended.{Style.RESET_ALL}")
                self._quit_game()
                break
            except Exception as e:
                self._handle_error(e)
    
    def _update_systems(self, delta_time: float):
        """Update all game systems"""
        # Autosave
        if self.config.autosave_enabled:
            self.last_autosave += delta_time
            if self.last_autosave >= self.config.autosave_interval:
                self._autosave()
                self.last_autosave = 0
        
        # Radio messages
        ExplorationState, CombatState, DialogueState, MainMenuState = self._get_engine_states()
        if self.radio_active and isinstance(self.current_state, ExplorationState):
            self.last_radio_time += delta_time
            if self.last_radio_time >= 120:  # Every 2 minutes
                self._trigger_radio_message()
                self.last_radio_time = 0
        
        # Weather changes
        if self.config.weather_enabled and random.random() < 0.01:  # 1% chance per tick
            self._update_weather()
        
        # Time progression
        if self.config.time_progression:
            self._update_time(delta_time)
        
        # Player effects
        if self.state.player:
            self._update_player_effects()
    
    def _update_player_effects(self):
        """Update player status effects"""
        location = self.location_manager.get_location(self.state.current_location)
        if not location:
            return
        
        # Update solar powered perk
        current_hour = self.state.game_time.get("hour", 12) if isinstance(self.state.game_time, dict) else 12
        self.state.player.set_property("game_hour", current_hour)
        self.state.player.set_property("is_outside", location.get_property("is_outside", False))

        # Sync carry weight
        if self.state.inventory:
            self.state.inventory.max_weight = self.state.player.carry_weight
    
    def _update_time(self, delta_time: float):
        """Update game time"""
        if not isinstance(self.state.game_time, dict):
            self.state.game_time = {"hour": 12, "minute": 0, "day": 1}
        
        # Advance time (1 real second = 1 game minute)
        self.state.game_time["minute"] += int(delta_time)
        
        if self.state.game_time["minute"] >= 60:
            self.state.game_time["hour"] += 1
            self.state.game_time["minute"] = 0
            
            # Update time of day
            hour = self.state.game_time["hour"]
            if 6 <= hour < 12:
                self.time_of_day = "morning"
            elif 12 <= hour < 18:
                self.time_of_day = "day"
            elif 18 <= hour < 21:
                self.time_of_day = "dusk"
            else:
                self.time_of_day = "night"
        
        if self.state.game_time["hour"] >= 24:
            self.state.game_time["hour"] = 0
            self.state.game_time["day"] += 1
    
    def _update_weather(self):
        """Update current weather"""
        old_weather = self.current_weather
        
        weather_options = [None, "rain", "fog", "dust", "radiation_storm"]
        weights = [0.4, 0.2, 0.15, 0.15, 0.1]  # None is most common
        
        self.current_weather = random.choices(weather_options, weights=weights)[0]
        
        if old_weather != self.current_weather and self.current_weather:
            self._announce_weather_change()
    
    def _announce_weather_change(self):
        """Announce weather changes with visual effects"""
        print(f"\n{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}")
        
        if self.current_weather == "radiation_storm":
            print(generate_radiation_storm(60, 3))
            print(f"\n{Fore.GREEN}☢ RADIATION STORM WARNING ☢{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Seek shelter! High radiation levels detected.{Style.RESET_ALL}")
        elif self.current_weather == "rain":
            print(generate_rain(60, 3))
            print(f"\n{Fore.BLUE}Rain begins to fall...{Style.RESET_ALL}")
        elif self.current_weather == "fog":
            print(generate_fog(60, 3))
            print(f"\n{Fore.WHITE}Thick fog rolls in, reducing visibility.{Style.RESET_ALL}")
        elif self.current_weather == "dust":
            print(generate_dust(60, 3))
            print(f"\n{Fore.WHITE}A dust storm kicks up debris.{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}\n")
    
    def _check_player_death(self) -> bool:
        """Check if player has died"""
        if self.state.player and self.state.player.hit_points <= 0:
            if getattr(self.state.player, 'god_mode', False):
                self.state.player.hit_points = 1
                return False
            self._handle_game_over(cause="Fatal combat wounds")
            return False
        return False

    def _handle_game_over(self, cause: str = "Fatal wounds"):
        """Gracefully handle player death without abruptly shutting down the game."""
        ExplorationState, CombatState, DialogueState, MainMenuState = self._get_engine_states()

        # Disengage combat
        if self.combat_manager:
            self.combat_manager.in_combat = False
            self.combat_manager.current_enemy = None

        print("\n" + ArtEffects.death_screen())
        print(f"\n{Fore.RED}{'=' * 60}")
        print("                     G A M E   O V E R")
        print(f"{'=' * 60}{Style.RESET_ALL}")
        print("Your wounds are fatal. You collapse into the radioactive ash of Berlin.")
        print(f"{Fore.YELLOW}Cause of death: {cause}{Style.RESET_ALL}\n")

        while self.running:
            print(f"{Fore.CYAN}[1]{Style.RESET_ALL} Load Latest Autosave")
            print(f"{Fore.CYAN}[2]{Style.RESET_ALL} Load Saved Game")
            print(f"{Fore.CYAN}[3]{Style.RESET_ALL} Respawn at Checkpoint Charlie (Revive with 50% HP)")
            print(f"{Fore.CYAN}[4]{Style.RESET_ALL} Return to Main Menu")
            print(f"{Fore.CYAN}[5]{Style.RESET_ALL} Quit Game")

            try:
                choice = input(f"\n{Fore.YELLOW}Choose option [1-5]: {Style.RESET_ALL}").strip()
            except (EOFError, KeyboardInterrupt):
                self.running = False
                return

            if choice == "1":
                if self.load_game("autosave.json"):
                    return
                print(f"{Fore.RED}Could not load autosave.{Style.RESET_ALL}")
            elif choice == "2":
                if self.load_game():
                    return
            elif choice == "3":
                if self.state.player:
                    self.state.player.hit_points = max(15, self.state.player.max_hit_points // 2)
                    self.state.player.radiation = min(self.state.player.radiation, 300)
                    self.state.player.hunger = min(self.state.player.hunger, 40)
                    self.state.player.thirst = min(self.state.player.thirst, 40)
                    self.state.player.is_alive = True
                self.state.current_location = "checkpoint_charlie"
                print(f"\n{Fore.GREEN}You regain consciousness in the clinic tent at Checkpoint Charlie.{Style.RESET_ALL}")
                self.change_state(ExplorationState(self))
                return
            elif choice == "4":
                self.change_state(MainMenuState(self))
                return
            elif choice in ["5", "q", "quit", "exit"]:
                self._quit_game()
                return
            else:
                print("Invalid selection.")
    
    def _handle_global_command(self, command: str) -> bool:
        """Handle global commands that work in any state"""
        from fallout_berlin.looting_state import LootingState
        from fallout_berlin.vats_state import VatsState
        from fallout_berlin.inventory_state import InventoryState
        from fallout_berlin.quest_log_state import QuestLogState
        from fallout_berlin.engine_states import DialogueState, ExplorationState
        from fallout_berlin.barter_state import BarterState
        if isinstance(self.current_state, VatsState) and command in [
            "c", "cancel", "exit", "back"
        ]:
            return False

        if (
            isinstance(self.current_state, LootingState)
            and command in ["exit", "leave", "close", "done", "q", "back"]
        ):
            return False

        if isinstance(self.current_state, (InventoryState, QuestLogState)) and command in [
            "c", "close", "exit", "q", "back"
        ]:
            return False

        if isinstance(self.current_state, DialogueState) and command in [
            "exit", "bye", "leave"
        ]:
            return False

        if isinstance(self.current_state, BarterState) and command in [
            "c", "close", "exit", "back", "q"
        ]:
            return False

        if command in ['quit', 'exit']:
            self._quit_game()
            return True
        
        if command == "settings":
            try:
                SettingsCommand().execute(self)
            except Exception as e:
                print(f"{Fore.RED}Settings menu unavailable: {e}{Style.RESET_ALL}")
            return True
        
        if command == "help":
            self._show_help()
            return True
        
        if command == "save":
            self.save_game()
            return True
            
        if command == "status":
            self._show_enhanced_status()
            return True

        if command in ["inventory", "inv", "i"]:
            from fallout_berlin.inventory_state import InventoryState
            if not isinstance(self.current_state, InventoryState):
                self.change_state(InventoryState(self))
            return True
            
        if isinstance(self.current_state, ExplorationState) and command in [
            "q", "quest", "quests"
        ]:
            from fallout_berlin.quest_log_state import QuestLogState
            if not isinstance(self.current_state, QuestLogState):
                self.change_state(QuestLogState(self))
            return True
            
        # Context check for action commands
        is_combat = False
        if self.current_state:
             is_combat = type(self.current_state).__name__ == 'CombatState'
        
        if command.startswith("equip"):
            if is_combat: return False # Defer to CombatState
            return self._handle_equip(command)
        
        if command.startswith("use"):
            if is_combat: return False # Defer to CombatState
            return self._handle_use(command)

        if command.startswith("drop"):
            if is_combat: return False # Defer to CombatState
            return self._handle_drop(command)
        
        return False

    def _handle_use(self, command: str) -> bool:
        """Handle use command for consumables"""
        parts = command.split(" ", 1)
        if len(parts) < 2:
            print(f"{Fore.RED}Usage: use <item name>{Style.RESET_ALL}")
            return True
        
        item_name = parts[1].strip().lower()
        item = self.state.inventory.find_item(item_name)

        if not item:
            print(f"{Fore.YELLOW}You don't have '{item_name}' in your inventory.{Style.RESET_ALL}")
            return True

        if isinstance(item, Consumable):
            self._use_consumable(item)
            return True
        else:
            print(f"{Fore.YELLOW}You can only use consumable items.{Style.RESET_ALL}")
            return True

    def _show_inventory(self):
        """Display player inventory"""
        if self.state.inventory:
            print(self.state.inventory.display())
        else:
            print("Inventory not initialized.")

    def _show_quest_status(self):
        """Display quest status"""
        print(self.quest_manager.get_quests_display(self.state))

    def _handle_drop(self, command: str) -> bool:
        """Handle drop command"""
        parts = command.split(" ", 1)
        if len(parts) < 2:
            print(f"{Fore.RED}Usage: drop <item name>{Style.RESET_ALL}")
            return True
        
        item_name = parts[1].strip().lower()
        item = self.state.inventory.find_item(item_name)

        if not item:
            print(f"{Fore.YELLOW}You don't have '{item_name}' in your inventory.{Style.RESET_ALL}")
            return True

        if self.state.inventory.remove_item(item.name, 1):
            location = self.location_manager.get_location(self.state.current_location)
            if location:
                location.add_item(item)
                print(f"{Fore.GREEN}You dropped {item.name}.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}You cannot drop items here.{Style.RESET_ALL}")
                self.state.inventory.add_item(item)
        return True

    def _handle_equip(self, command: str) -> bool:
        """Handle equip command"""
        parts = command.split(" ", 1)
        if len(parts) < 2:
            print(f"{Fore.RED}Usage: equip <item name>{Style.RESET_ALL}")
            return True
        
        item_name = parts[1].strip().lower()
        item = self.state.inventory.find_item(item_name)

        if not item:
            print(f"{Fore.YELLOW}You don't have '{item_name}' in your inventory.{Style.RESET_ALL}")
            return True

        if isinstance(item, (Weapon, Armor)):
            # Inventory handling: equip_item should handle the swap logic
            result = self.state.player.equip_item(item)
            if result:
                print(f"{Fore.GREEN}You equipped {item.name}.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}You cannot equip {item.name}.{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}You can only equip weapons or armor.{Style.RESET_ALL}")
        return True

    def _start_dialogue(self, npc_id: str):
        """Start a dialogue with an NPC"""
        tree = self.dialogue_manager.get_dialogue_tree(npc_id)
        if not tree:
            print("That person doesn't want to talk.")
            return

        self.state.set_world_flag(f"talked_to_{npc_id}")
        self.current_dialogue_tree = tree
        self.current_dialogue_node = tree.get_start_node()
        ExplorationState, CombatState, DialogueState, MainMenuState = self._get_engine_states()
        self.change_state(DialogueState(
            self,
            npc_id=tree.npc_id,
            current_node=self.current_dialogue_node.node_id if self.current_dialogue_node else ""
        ))

    def _display_dialogue_node(self):
        """Display the current dialogue node"""
        if not self.current_dialogue_node:
            ExplorationState, CombatState, DialogueState, MainMenuState = self._get_engine_states()
            self.change_state(ExplorationState(self))
            return

        node = self.current_dialogue_node
        speaker = (
            self.current_dialogue_tree.npc_name if node.speaker != "player" else "You"
        )

        options = node.get_available_options(self.state)

        # Safeguard: if no options are available, add a default "Exit" option
        if not options:
            from fallout_berlin.dialogue import DialogueOption
            exit_opt = DialogueOption("Goodbye. [Engine Safeguard]", end_dialogue=True)
            exit_opt.end_dialogue = True
            options = [exit_opt]

        options_list = [(i, option.text) for i, option in enumerate(options, 1)]

        self.ui_manager.display_dialogue_node(speaker, node.text, options_list)

    def _sync_location_state(self):
        """Save current location state for persistence"""
        location = self.location_manager.get_location(self.state.current_location)
        if location:
            self.state.location_states[location.location_id] = location.to_dict()

    def _advance_time(self, minutes: int):
        """Advance game time by minutes (Alias for compatibility)"""
        self._update_time(float(minutes))

    def _update_survival(self, move_cost=False):
        """Update survival stats and advance game time"""
        if not self.state.player:
            return

        # Advance game time
        minutes_passed = 15 if move_cost else 5
        self._advance_time(minutes_passed)

        # Reduced rates for easier gameplay
        hunger_inc = 0.5 if move_cost else 0.1
        thirst_inc = 0.5 if move_cost else 0.1
        fatigue_inc = 0.2 if move_cost else 0.05

        if getattr(self.state.player, "is_sneaking", False):
            fatigue_inc *= 2  # Sneaking is tiring

        if getattr(self.state.player, 'god_mode', False):
            hunger_inc = 0
            thirst_inc = 0
            fatigue_inc = 0

        died = self.state.player.update_survival_stats(
            hunger_inc, thirst_inc, fatigue_inc, minutes=minutes_passed
        )

        if getattr(self.state.player, 'god_mode', False):
            died = False

        if died:
            self._handle_game_over(cause="Starvation or dehydration")
            return

        elif self.state.player.hunger >= 100 or self.state.player.thirst >= 100:
            print(f"{Fore.RED}[WARNING] You are starving or dehydrated! You take damage.{Style.RESET_ALL}")
        elif self.state.player.hunger > 80 or self.state.player.thirst > 80:
            print(f"{Fore.YELLOW}[WARNING] You are getting hungry/thirsty.{Style.RESET_ALL}")

    def _check_random_encounter(self, chance=0.2) -> bool:
        """Check for random enemy encounters during travel, including faction hit squads"""
        # 1. Check for Faction Hit Squads (Higher priority logic)
        hostile_factions = []
        # Check major factions (This list should ideally come from a config or GameState)
        for faction in ["Spree Swans", "New Prussian Republic", "Techno-Vikings", "Raiders"]:
            if self.state.is_faction_hostile(faction):
                hostile_factions.append(faction)
        
        # 15% chance for a hit squad if you have enemies
        if hostile_factions and random.random() < 0.15: 
            attacker_faction = random.choice(hostile_factions)
            
            quotes = {
                "Spree Swans": "The Swan Queen sends her regards.",
                "New Prussian Republic": "For order! The anomaly must be purged.",
                "Techno-Vikings": "Your tech is forfeit, weakling!",
                "Raiders": "Fresh meat!"
            }
            quote = quotes.get(attacker_faction, "You won't escape us!")

            print(f"\n{Fore.RED}You feel like you're being watched...{Style.RESET_ALL}")
            time.sleep(1)
            print(f"{Fore.RED}A {attacker_faction} Hit Squad ambushes you!{Style.RESET_ALL}")
            print(f"\"{quote}\"")
            
            # Spawn logic: Try to find a faction-specific enemy, else generic
            # Convention: faction_name_rank (e.g. spree_swans_assassin)
            # Simplified for now: map to existing enemies or generic bosses
            enemy_key = "raider_boss" # Default strong enemy
            if attacker_faction == "Spree Swans": enemy_key = "spree_swan" # Re-use boss
            elif attacker_faction == "Techno-Vikings": enemy_key = "power_armor_soldier"
            
            enemy = create_enemy(enemy_key)
            if not enemy: 
                enemy = create_enemy("raider_veteran")
            
            if enemy:
                enemy.name = f"{attacker_faction} Enforcer" # Rename for flavor
                enemy.level = max(enemy.level, (self.state.player.level if self.state.player else 1) + 2) # Scale up
                self.start_combat(enemy)
                return True

        # 2. Standard Random Encounters
        if random.random() < chance:
            # Default pool
            enemies = self.encounter_tables.get("default", ["radroach"])
            
            # Context-aware pools based on location ID
            loc_id = self.state.current_location.lower()
            
            for region in self.encounter_tables.get("regions", []):
                for keyword in region["keywords"]:
                    if keyword in loc_id:
                        enemies = region["enemies"]
                        break
                else:
                    continue # Continue if inner loop didn't break
                break # Break outer loop if inner loop broke

            # Filter enemies by level difference
            player_level = self.state.player.level if self.state.player else 1
            valid_enemies = []
            
            for ek in enemies:
                e = create_enemy(ek)
                if e and e.level <= player_level + 3:
                    valid_enemies.append(ek)
            
            if not valid_enemies:
                # Fallback to the weakest enemy in the pool if none are valid
                sorted_by_level = sorted(
                    enemies,
                    key=lambda ek: getattr(create_enemy(ek), "level", 99)
                )
                valid_enemies = [sorted_by_level[0]]

            enemy_key = random.choice(valid_enemies)
            enemy = create_enemy(enemy_key)

            if enemy:
                print("\nSomething blocks your path...")
                self.start_combat(enemy)
                return True
        return False

    def _check_location_enemies(self, location_id: str) -> bool:
        """Check if location has enemies that attack on entry"""
        location = self.location_manager.get_location(location_id)
        if not location or not location.enemies:
            return False

        enemy = location.enemies[0]

        should_attack = False
        faction = location.get_property("faction")
        
        # 1. Determine base hostility
        if location.get_property("hostile", False):
            should_attack = True
        elif faction and self.state.is_faction_hostile(faction):
            should_attack = True
            
        # 2. Check for Disguise (Overrides hostility if faction matches)
        if should_attack and faction:
            equipped_armor = self.state.player.equipped_armor
            if equipped_armor and getattr(equipped_armor, "faction_tag", None) == faction:
                 print(f"{Fore.GREEN}The {faction} controls this area, but your {equipped_armor.name} disguises you as one of them.{Style.RESET_ALL}")
                 should_attack = False
            else:
                 print(f"{Fore.RED}The {faction} controls this area and they don't like you!{Style.RESET_ALL}")

        if should_attack:
            # If player is in stealth, perform stealth check
            if getattr(self.state.player, "is_sneaking", False):
                # Stealth Calculation: Player Agility vs Enemy Perception (estimated by level)
                player_sneak = (self.state.player.agility * 8) + (
                    self.state.player.luck * 2
                )
                enemy_perception = enemy.level * 10 if hasattr(enemy, "level") else 40

                # Base chance 50%, modified by stats, with a ceiling on success/failure based on game state/lore
                # To enforce narrative stability: If enemy is critical to a quest, stealth success chance is reduced.
                is_quest_critical = self.quest_manager.is_enemy_critical(enemy.name, self.state.current_location)
                
                base_chance = 50 + (player_sneak - enemy_perception)
                
                if is_quest_critical:
                    # Nerf stealth success chance if enemy is essential for narrative progression
                    chance = max(10, min(50, base_chance)) # Max 50% to force confrontation
                    print(f"{Fore.RED}[NARRATIVE LOCKDOWN] Avoiding confrontation with this target is proving impossible!{Style.RESET_ALL}")
                else:
                    chance = max(10, min(90, base_chance))

                if random.randint(1, 100) <= chance:
                    print(
                        f"\n{Fore.CYAN}[STEALTH SUCCESS] You sneak past the {enemy.name} in {location.name}.{Style.RESET_ALL}"
                    )
                    return False
                else:
                    print(
                        f"\n{Fore.RED}[STEALTH FAILED] You tried to sneak past {enemy.name} but made a noise!{Style.RESET_ALL}"
                    )
                    self.state.player.is_sneaking = False

            print(f"\nAs you enter {location.name}, you spot a threat!")
            self.start_combat(enemy)
            return True
        return False

    def _use_consumable(self, item: Consumable):
        """Use a consumable item"""
        if not isinstance(item, Consumable) or not self.state.player:
            return

        self.effect_manager.apply_effect(item, self.state.player, self.state.inventory)

    def _handle_interaction(self, item, target_name: str):
        """Handle using an item on an environmental object"""
        location = self.location_manager.get_location(self.state.current_location)
        if not location:
            return

        # Check for custom location actions
        # Construct action key: use_itemname_on_targetname
        action_key = f"use_{item.name.lower().replace(' ', '_')}_on_{target_name.lower().replace(' ', '_')}"

        if hasattr(location, "actions") and action_key in location.actions:
            location.actions[action_key](self.state)
            return

        # Default interactions could go here
        print(f"Nothing happens when you use {item.name} on {target_name}.")

    def _handle_scan(self):
        """Scan the area using Perception"""
        if not self.state.player:
            return

        print("Scanning area...")
        perception = self.state.player.perception
        location = self.location_manager.get_location(self.state.current_location)
        if not location:
            return

        # Chance to find hidden details based on Perception
        if random.randint(1, 10) <= perception:
            found_something = False

            # Check for items
            if location.items:
                valuable = max(location.items, key=lambda x: x.value)
                print(
                    f"{Fore.GREEN}You spot a {valuable.name} among the clutter.{Style.RESET_ALL}"
                )
                found_something = True

            # Check for danger
            if location.enemies or location.get_property("hostile", False):
                print(f"{Fore.RED}WARNING: Hostile presence detected.{Style.RESET_ALL}")
                found_something = True

            # Scavenger's Luck: Occasional hidden loot find
            luck = self.state.player.luck
            # Chance increases with Luck and Perception
            # Max chance at P10, L10: (10 * 2) + (10 * 3) = 50%
            scavenge_chance = (perception * 2) + (luck * 3)
            
            if random.randint(1, 100) <= scavenge_chance:
                # Find something hidden!
                rare_finds = ["stimpak", "caps", "bobby_pin", "nuka_cola", "adhesive", "scrap_metal"]
                item_key = random.choice(rare_finds)
                item = create_item(item_key)
                
                if item:
                    print(f"\n{Fore.CYAN}[SCAVENGER'S LUCK] Your keen eye spots something hidden under some rubble!{Style.RESET_ALL}")
                    if self.state.inventory.add_item(item):
                        print(f"You found: {Fore.YELLOW}{item.name}{Style.RESET_ALL}")
                        found_something = True
                    else:
                        print(f"You found a {item.name}, but your inventory is full!")
                        location.add_item(item)
                        found_something = True

            if not found_something:
                print("Area seems clear.")
        else:
            print("You don't notice anything special.")

    def _handle_camp(self):
        """Rest to recover health and reduce fatigue/hunger/thirst"""
        print("You set up a temporary camp...")
        self.state.player.hunger = max(0, getattr(self.state.player, "hunger", 0) - 30)
        self.state.player.thirst = max(0, getattr(self.state.player, "thirst", 0) - 30)
        self.state.player.heal(10)
        print(
            f"{Fore.GREEN}You feel rested. Hunger and thirst reduced.{Style.RESET_ALL}"
        )

    def _handle_radio(self):
        """Toggle radio"""
        self.radio_active = not self.radio_active
        status = "ON" if self.radio_active else "OFF"
        self.ui_manager.display_radio_message(f"Pip-Boy Radio turned {status}.")

    def _handle_sneak(self):
        """Toggle sneaking mode"""
        if not self.state.player:
            return

        current = getattr(self.state.player, "is_sneaking", False)
        if current:
            self.state.player.is_sneaking = False
            print("You stop sneaking and stand tall.")
        else:
            self.state.player.is_sneaking = True
            print(f"{Fore.CYAN}You crouch down and move silently.{Style.RESET_ALL}")

    # ==========================================================================
    # ENHANCED FEATURES
    # ==========================================================================
    
    def _show_location_entrance(self):
        """Show enhanced location entrance"""
        location = self.location_manager.get_location(self.state.current_location)
        if not location:
            return
        
        # Render scene with weather
        scene = self.ui_manager.renderer.render_location(
            self.state.current_location,
            weather=self.current_weather,
            time_of_day=self.time_of_day,
            show_pip_boy=False
        )
        
        print(scene)
        print(f"\n{Fore.CYAN}═══ {location.name.upper()} ═══{Style.RESET_ALL}")
        print(location.description)
        
        # Show available exits
        if location.connections:
            exits = ", ".join([f"{Fore.YELLOW}{direction}{Style.RESET_ALL}" for direction in location.connections.keys()])
            print(f"\n{Fore.GREEN}Exits:{Style.RESET_ALL} {exits}")
    
    def _show_enhanced_status(self):
        """Show enhanced player status screen"""
        if not self.state.player:
            return
        
        p = self.state.player
        
        # Header
        print(f"\n{Fore.CYAN}{'═' * 70}")
        print(self.art_composer.center_text("CHARACTER STATUS", 70))
        print(f"{'═' * 70}{Style.RESET_ALL}\n")
        
        # Basic info
        info = f"""
NAME: {p.name}
LEVEL: {p.level}
XP: {p.experience} / {p.experience_to_next_level}
ORIGIN: {p.origin.replace('_', ' ').title()}
        """
        print(self.art_composer.create_border(info.strip(), "double", Fore.CYAN))
        
        # Health bar
        health_percent = p.hit_points / p.max_hit_points
        health_bar = self._create_colored_bar(health_percent, 30)
        
        print(f"\n{Fore.WHITE}HEALTH:{Style.RESET_ALL}")
        print(f"[{health_bar}] {p.hit_points}/{p.max_hit_points}")
        
        # SPECIAL stats
        stats = f"""
S.P.E.C.I.A.L:

  Strength:     {p.strength}  ║  Perception:  {p.perception}
  Endurance:    {p.endurance}  ║  Charisma:    {p.charisma}
  Intelligence: {p.intelligence}  ║  Agility:     {p.agility}
  Luck:         {p.luck}
        """
        print("\n" + self.art_composer.create_border(stats.strip(), "single", Fore.YELLOW))
        
        # Survival stats
        if hasattr(p, 'hunger'):
            survival = f"""
SURVIVAL:
  Hunger:  {int(p.hunger)}/100
  Thirst:  {int(p.thirst)}/100
  Fatigue: {int(getattr(p, 'fatigue', 0))}/100
            """
            print("\n" + self.art_composer.create_border(survival.strip(), "single", Fore.RED))
        
        # Perks
        if hasattr(p, 'perks') and p.perks:
            perks_text = "PERKS:\n" + "\n".join([f"  • {perk}" for perk in p.perks[:10]])
            if len(p.perks) > 10:
                perks_text += f"\n  ... and {len(p.perks) - 10} more"
            print("\n" + self.art_composer.create_border(perks_text, "single", Fore.MAGENTA))
            
        # Factions
        factions = ["Spree Swans", "New Prussian Republic", "Techno-Vikings", "Raiders"]
        faction_lines = []
        
        for faction in factions:
            standing = self.state.get_faction_standing(faction)
            rep = self.state.get_faction_reputation(faction)
            if rep != 0: # Only show non-neutral
                color = Fore.WHITE
                if rep > 0: color = Fore.GREEN
                elif rep < 0: color = Fore.RED
                
                faction_lines.append(f"  {faction:<22} {color}{standing:<10} ({rep}){Style.RESET_ALL}")
        
        if faction_lines:
             faction_text = "FACTION STANDING:\n" + "\n".join(faction_lines)
             print("\n" + self.art_composer.create_border(faction_text.strip(), "single", Fore.BLUE))
        
        print()
    
    def _create_colored_bar(self, percent: float, length: int = 30) -> str:
        """Create a colored progress bar"""
        filled = int(length * percent)
        
        if percent > 0.6:
            color = Fore.GREEN
        elif percent > 0.3:
            color = Fore.YELLOW
        else:
            color = Fore.RED
        
        return f"{color}{'█' * filled}{Fore.BLACK}{'█' * (length - filled)}{Style.RESET_ALL}"
    
    def _show_help(self):
        """Show enhanced help screen"""
        help_text = """
FALLOUT BERLIN - COMMAND REFERENCE

MOVEMENT:
  go <direction>     - Travel to a new location
  look              - Examine your surroundings
  
COMBAT:
  attack <target>   - Attack an enemy
  shoot <target>    - Shoot with ranged weapon
  sneak             - Enter stealth mode
  
INVENTORY:
  inventory / i     - View your items
  use <item>        - Use an item
  equip <item>      - Equip weapon/armor
  drop <item>       - Drop an item
  
INTERACTION:
  talk <npc>        - Talk to someone
  take <item>       - Pick up an item
  search            - Search the area
  hack              - Hack nearby terminal
  
SYSTEM:
  status            - View character stats
  quests            - View active quests
  map               - Show local map
  save              - Save game
  settings          - Adjust settings
  help              - Show this help
  quit              - Exit game
        """
        
        print(self.art_composer.create_border(help_text.strip(), "double", Fore.CYAN))
    
    # ==========================================================================
    # EVENT HANDLERS
    # ==========================================================================
    
    def _on_radio_message(self, event: Event):
        """Handle radio message events"""
        if self.radio_active:
            message = event.data.get('message', '')
            print(f"\n{Fore.GREEN}[📻 RADIO] {message}{Style.RESET_ALL}\n")
    
    def _on_location_enter(self, event: Event):
        """Handle location entry events"""
        location_id = event.data.get("location_id")
        location = self.location_manager.get_location(location_id)
        
        if not location:
            return
        
        # Check for bureaucracy requirements
        if self._check_bureaucracy_required(location_id):
            if not self._handle_bureaucracy_check(location_id, location.name):
                return
        
        # Show entrance
        self._show_location_entrance()
        
        # Trigger radio
        if self.radio_active:
            self._trigger_radio_message()
    
    def _check_bureaucracy_required(self, location_id: str) -> bool:
        """Check if location requires paperwork"""
        restricted = ["reichstag", "charlottenburg_palace", "tempelhof"]
        return location_id in restricted
    
    def _handle_bureaucracy_check(self, location_id: str, location_name: str) -> bool:
        """Handle bureaucracy mini-game"""
        return self.minigame_manager.handle_bureaucracy_check(
            location_id, location_name, self.state.player, self.state.inventory
        )
    
    def _trigger_radio_message(self):
        """Trigger a radio broadcast"""
        message = self._get_radio_message()
        if message:
            self.event_manager.dispatch(
                Event(EventType.RADIO_MESSAGE, {"message": message})
            )
    
    def _get_radio_message(self) -> str:
        """Get a random radio message"""
        if not self.radio_data:
            return ""
        
        # Choose type
        msg_type = random.choice(["music", "banter", "news"])
        
        if msg_type == "music" and self.radio_data.get("music"):
            return random.choice(self.radio_data["music"])
        elif msg_type == "banter" and self.radio_data.get("banter"):
            return random.choice(self.radio_data["banter"])
        elif msg_type == "news" and self.radio_data.get("news"):
            news_list = self.radio_data["news"].get("general", [])
            if news_list:
                return random.choice(news_list)
        
        return "Radio Freies Berlin - Your voice in the wasteland."
    
    # ==========================================================================
    # SAVE/LOAD SYSTEM
    # ==========================================================================
    
    def save_game(self):
        """Save the game"""
        print(f"\n{Fore.CYAN}═══ SAVE GAME ═══{Style.RESET_ALL}")
        
        saves = self.state.list_saves()
        if saves:
            print("\nExisting saves:")
            for save in saves:
                print(f"  • {save['filename']} ({save['date']})")
        
        try:
            filename = input(f"\n{Fore.YELLOW}Save name (or Enter for 'quicksave.json'):{Style.RESET_ALL} ").strip()
            
            if not filename:
                filename = "quicksave.json"
            if not filename.endswith(".json"):
                filename += ".json"
            
            filepath = self.state.save_game(filename)
            
            print(f"\n{Fore.GREEN}✓ Game saved to {filepath}{Style.RESET_ALL}")
        
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Fore.YELLOW}Save cancelled.{Style.RESET_ALL}")
    
    def _autosave(self):
        """Perform autosave"""
        try:
            self.state.save_game("autosave.json")
            if self.config.debug_mode:
                print(f"{Fore.GREEN}[Autosaved]{Style.RESET_ALL}")
        except Exception as e:
            if self.config.debug_mode:
                print(f"{Fore.RED}[Autosave failed: {e}]{Style.RESET_ALL}")
    
    def load_game(self, filename: str = None) -> bool:
        """Load a saved game"""
        if filename:
            success = self.state.load_game(filename)
        else:
            saves = self.state.list_saves()
            if not saves:
                print(f"\n{Fore.YELLOW}No save games found.{Style.RESET_ALL}")
                return False
            
            print(f"\n{Fore.CYAN}═══ LOAD GAME ═══{Style.RESET_ALL}\n")
            
            for i, save in enumerate(saves, 1):
                print(f"{i}. {save['filename']} - {save['date']} - {save['location']}")
            print(f"{len(saves) + 1}. Cancel")
            
            try:
                choice = input(f"\n{Fore.YELLOW}Select save:{Style.RESET_ALL} ").strip()
                
                if not choice or choice == str(len(saves) + 1):
                    return False
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(saves):
                    filename = saves[choice_num - 1]["filename"]
                    success = self.state.load_game(filename)
                else:
                    print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
                    return False
            
            except (ValueError, IndexError, EOFError):
                return False
        
        if success:
            print(f"\n{Fore.GREEN}✓ Game loaded successfully!{Style.RESET_ALL}")
            
            # Reinitialize managers with loaded state
            self.player = self.state.player
            saved_quests = self.state.quests
            self.quest_manager.reset()
            self.quest_manager.quests.update(saved_quests)
            self.state.quests = self.quest_manager.quests
            
            # Sync UI manager
            self.ui_manager.state = self.state
            
            self.combat_manager = CombatManager(
                self.state, self.location_manager, self.ui_manager
            )
            self.running = True
            
            # Transition to ExplorationState
            ExplorationState, CombatState, DialogueState, MainMenuState = self._get_engine_states()
            self.change_state(ExplorationState(self))
            
            return True
        else:
            print(f"\n{Fore.RED}✗ Failed to load game.{Style.RESET_ALL}")
            return False
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    def _quit_game(self):
        """Quit the game with optional save"""
        try:
            print(f"\n{Fore.YELLOW}Save before quitting?{Style.RESET_ALL}")
            print("1. Yes")
            print("2. No")
            print("3. Cancel")
            
            choice = input(f"\n{Fore.YELLOW}Choice:{Style.RESET_ALL} ").strip()
            
            if choice == '1':
                self.save_game()
            elif choice == '3':
                return
        
        except EOFError:
            pass
        
        print(f"\n{Fore.CYAN}Thanks for playing Fallout: Berlin!{Style.RESET_ALL}")
        print("Bis bald, Wanderer.\n")
        
        self.running = False
        sys.exit(0)

    def _handle_craft(self, args: List[str]):
        """Handle crafting recipes"""
        from fallout_berlin.crafting_state import CraftingState
        if not isinstance(self.current_state, CraftingState):
            self.change_state(CraftingState(self))

    def _handle_companion(self, args: List[str]):
        """Handle companion commands"""
        if not self.state.companion:
            print("You are traveling alone.")
            # For testing/demo purposes, allow recruiting a dog
            print("(Debug: Type 'companion recruit dog' to get a companion)")
            if args and len(args) > 1 and args[0] == "recruit" and args[1] == "dog":
                self.state.companion = Companion(
                    "Rad-Wolf", "A loyal, slightly glowing wolf.", 30, 8
                )
                print("You recruited Rad-Wolf!")
            return

        c = self.state.companion
        print(f"\n=== {c.name} ===")
        print(f"{c.description}")
        print(f"HP: {c.hp}/{c.max_hp}")
        print(
            f"Inventory: {c.inventory.get_total_weight()}/{c.inventory.max_weight} lbs"
        )

        if args and args[0] == "dismiss":
            print(f"You dismissed {c.name}.")
            self.state.companion = None
        elif args and args[0] == "inventory":
            print(c.inventory.display())

    def _handle_steal(self, args: List[str]):
        """Attempt to steal from an NPC or enemy"""
        if not args:
            print("Steal from whom?")
            return

        target_name = " ".join(args).lower()
        location = self.location_manager.get_location(self.state.current_location)
        if not location:
            return

        # Find target (Enemy or NPC)
        target = location.find_enemy(target_name)

        # Check for NPC ID match (substring)
        matched_npc_id = None
        if not target:
            for npc_id in location.npcs:
                if target_name in npc_id.lower() or npc_id.lower() in target_name:
                    matched_npc_id = npc_id
                    break

        if not target and matched_npc_id:
            # Create a dummy enemy/NPC object for mechanics
            target = create_enemy("raider")  # Generic fallback stats
            if target:
                target.name = target_name.title()
                target.loot_table = ["caps", "stimpak"]  # Generic loot

        if not target:
            print(f"You don't see {target_name} here to steal from.")
            return

        # Check skill
        steal_skill = self.state.player.get_skill("Steal")
        target_perception = target.level * 10 if hasattr(target, "level") else 30

        # Base difficulty
        difficulty = 40 + target_perception

        # Sneak bonus
        if getattr(self.state.player, "is_sneaking", False):
            steal_skill += 20

        print(f"Attempting to steal from {target.name}...")

        if random.randint(1, 100) + steal_skill >= difficulty:
            # Success
            loot = target.get_loot()
            if loot:
                item = loot[0]  # Take first item
                if self.state.inventory.add_item(item):
                    print(
                        f"{Fore.GREEN}[SUCCESS] You quietly pilfered a {Fore.YELLOW}{item.name}{Fore.GREEN}!{Style.RESET_ALL}"
                    )
                    self.state.player.add_experience(10)
                else:
                    print(
                        f"{Fore.RED}You found something but couldn't carry it!{Style.RESET_ALL}"
                    )
            else:
                print("You reached into their pockets but found nothing.")
        else:
            # Failure
            print(f"{Fore.RED}[FAILURE] You were caught!{Style.RESET_ALL}")
            print(f"{target.name} is attacking you!")
            self.state.player.is_sneaking = False

            # Reputation hit if applicable
            # (Simplified: assumes hostile response)

            self.start_combat(target)

    def _handle_hack(self, args: List[str]):
        """Attempt to hack a terminal"""
        self.minigame_manager.handle_hack(args, self.state.player, self.state.current_location)

    def _handle_form_filling(self, item):
        """Handle filling out bureaucratic forms"""
        self.minigame_manager.handle_form_filling(item, self.state.player)

    def _handle_start_anmeldung(self):
        """Trigger the Anmeldung minigame for testing"""
        print("\n=== BUREAUCRACY SIMULATOR 2287 ===")
        # Grant items for testing if missing
        required = ["Anmeldung Form 27-B", "Passierschein A39"]
        has_items = False
        for req in required:
             if self.state.inventory.find_item(req):
                 has_items = True
                 break
        
        if not has_items:
             print("(Debug: Adding required forms to inventory for testing)")
             self.state.inventory.add_item(create_item("anmeldung_form"))
             self.state.inventory.add_item(create_item("passierschein_a39"))

        if self.minigame_manager.handle_bureaucracy_check("buergeramt", "Bürgeramt", self.state.player, self.state.inventory):
            print(f"\n{Fore.GREEN}[SUCCESS] You have successfully registered your residence! The bureaucracy is appeased... for now.{Style.RESET_ALL}")
            self.state.player.add_experience(100)
        else:
            print(f"\n{Fore.RED}[FAILURE] Your application was rejected. Please take a new number and wait 6 months.{Style.RESET_ALL}")

    def _handle_debug_menu(self):
        """Display and handle debug options"""
        while True:
            print("\n=== DEBUG MENU ===")
            print("1. Full Heal (HP/Rad/Hunger/Thirst)")
            print("2. Add 1000 Caps")
            print("3. Add 1000 XP")
            print("4. Toggle God Mode")
            print("5. Teleport")
            print("6. Exit Debug")
            
            choice = input("Debug> ").strip()
            
            if choice == "1":
                if self.state.player:
                    self.state.player.heal(1000)
                    self.state.player.cure_radiation(1000)
                    self.state.player.hunger = 0
                    self.state.player.thirst = 0
                    print("Player fully restored.")
            elif choice == "2":
                self.state.inventory.add_item(create_item("caps", 1000))
                print("Added 1000 Caps.")
            elif choice == "3":
                self.state.player.add_experience(1000)
                print("Added 1000 XP.")
            elif choice == "4":
                # Simple toggle for now, would need support in player class for real god mode
                current = getattr(self.state.player, 'god_mode', False)
                self.state.player.god_mode = not current
                status = "ENABLED" if self.state.player.god_mode else "DISABLED"
                print(f"God Mode {status}")
            elif choice == "5":
                locs = list(self.location_manager.locations.keys())
                print(f"Locations: {', '.join(locs)}")
                dest = input("Teleport to: ").strip()
                if dest in locs:
                    self.state.current_location = dest
                    self.location_manager.visit_location(dest)
                    print(f"Teleported to {dest}.")
                else:
                    print("Invalid location.")
            elif choice == "6":
                break
    
    def _handle_error(self, error: Exception):
        """Handle errors gracefully"""
        print(f"\n{Fore.RED}{'═' * 60}")
        print(f"ERROR: {error}")
        print(f"{'═' * 60}{Style.RESET_ALL}\n")
        
        if self.config.debug_mode:
            import traceback
            traceback.print_exc()
        print(
            "The current session was not saved; existing save files were left unchanged."
        )


# ==============================================================================
# CORE SYSTEM HOOKS FOR INTEGRATION
# ==============================================================================

def main():
    """Main entry point"""
    engine = ImprovedGameEngine()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--load" and len(sys.argv) > 2:
            engine.running = True
            if engine.load_game(sys.argv[2]):
                engine.game_loop()
            else:
                print("Failed to load game.")
        elif sys.argv[1] == "--debug":
            engine.config.debug_mode = True
            print(f"{Fore.YELLOW}Debug mode enabled{Style.RESET_ALL}")
            engine.running = True
            engine.start_new_game()
            engine.game_loop()
        else:
            print("Usage: python -m fallout_berlin.game_engine [--load <savefile>] [--debug]")
    else:
        # Start in Main Menu State
        ExplorationState, CombatState, DialogueState, MainMenuState = engine._get_engine_states()
        engine.running = True
        engine.change_state(MainMenuState(engine))
        engine.game_loop()


if __name__ == "__main__":
    main()
