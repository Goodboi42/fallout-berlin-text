from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Tuple, Optional
import colorama
from colorama import Style, Fore

if TYPE_CHECKING:
    from fallout_berlin.improved_game_engine import ImprovedGameEngine # Changed to ImprovedGameEngine

class EngineState(ABC):
    """Abstract base class for game engine states."""

    def __init__(self, engine: "ImprovedGameEngine", prompt_label: str = "Explore"):
        self.engine = engine
        self.prompt_label = prompt_label

    def enter(self):
        """Called when entering this state."""
        pass

    def exit(self):
        """Called when exiting this state."""
        pass

    @abstractmethod
    def handle_input(self, command: str):
        """Handle user input."""
        pass

    def update(self):
        """Update state logic (called every loop iteration)."""
        pass

    def render(self):
        """Render state-specific UI."""
        pass


class ExplorationState(EngineState):
    """State for normal gameplay (exploration, movement, inventory)."""

    def __init__(self, engine: "ImprovedGameEngine"):
        super().__init__(engine, "Explore")

    def handle_input(self, command: str):
        command_obj = self.engine.input_parser.parse(command)

        if command_obj:
            command_obj.execute(self.engine)
        elif command == "debug":
            self.engine._handle_debug_menu()
        elif command == "loot":
            location = self.engine.location_manager.get_location(self.engine.state.current_location)
            if location and location.items:
                from fallout_berlin.looting_state import LootingState
                self.engine.change_state(LootingState(self.engine, location.name, location.items))
            else:
                print(f"{Fore.YELLOW}There is nothing here to loot.{Style.RESET_ALL}")
        elif command == "craft":
            self.engine._handle_craft([])
        else:
            suggestions = self.engine.input_parser.get_suggestions(command)
            if suggestions:
                print(f"Terminal Error: Command unknown. Did you mean: {', '.join(suggestions)}?")
            else:
                print("Terminal Error: Command unknown. Type 'help' for options.")

    def render(self):
        # Only render UI if not in special modes (which are now states)
        # In original code: if not self.combat_manager.in_combat and not self.in_dialogue: self._render_ui()
        location = self.engine.location_manager.get_location(self.engine.state.current_location)
        self.engine.ui_manager.display_location(location, force_art=True, weather=self.engine.current_weather, time_of_day=self.engine.time_of_day)
        print("\n[I] Inventory   [Q] Quests   [H] Help")


class CombatState(EngineState):
    """State for combat encounters."""

    def __init__(self, engine: "ImprovedGameEngine"):
        super().__init__(engine, "Combat")

    def enter(self):
        # Ensure combat manager knows we are in combat if not already
        # (Though usually CombatManager starts it)
        pass

    def handle_input(self, command: str):
        if not self.engine.combat_manager:
            return
        command = command.strip().lower()
        command = {
            "a": "attack",
            "v": "vats",
            "h": "heal",
            "c": "take cover",
            "f": "flee",
        }.get(command, command)
        
        # Check for pause/menu
        if command in ["pause", "menu", "esc"]:
            self.engine.change_state(PauseMenuState(self.engine))
            return
            
        if command == "vats":
            from fallout_berlin.vats_state import VatsState
            self.engine.change_state(VatsState(self.engine))
            return

        status, data = self.engine.combat_manager.process_combat_turn(command, self.engine)
        
        if status == "VICTORY":
            if data: # Loot items
                # Add drops to location to ensure persistence if not taken immediately
                location = self.engine.location_manager.get_location(self.engine.state.current_location)
                if location:
                    location.items.extend(data)
                    from fallout_berlin.looting_state import LootingState
                    self.engine.change_state(LootingState(self.engine, "Area Loot", location.items))
            else:
                self.engine.change_state(ExplorationState(self.engine))
        elif status == "ESCAPED":
            self.engine.change_state(ExplorationState(self.engine))
        elif status == "DEFEAT":
            self.engine.running = False

    def render(self):
        """Render combat status screen with full details"""
        cm = self.engine.combat_manager
        if not cm or not cm.current_enemy:
            return

        player = self.engine.state.player
        enemy = cm.current_enemy
        
        # Get player AP
        player_ap = getattr(player, 'current_ap', 0)
        player_max_ap = getattr(player, 'max_ap', 0)
        
        # Get player and enemy effects
        player_effects = getattr(player, 'active_effects', [])
        enemy_effects = getattr(enemy, 'active_effects', [])

        # Get enemy cover status
        enemy_has_cover = getattr(enemy, 'has_cover', False)
        
        # Determine available combat actions
        available_actions = [
            ("a", "Attack with equipped weapon"),
            ("v", "Enter V.A.T.S."),
            ("h", "Use Stimpak"),
            ("c", "Take cover"),
            ("f", "Attempt to flee")
        ]
        
        # Before rendering, clear the screen
        self.engine.ui_manager.clear_screen()

        self.engine.ui_manager.show_combat_status(
            player_name=player.name,
            player_hp=player.hit_points,
            player_max_hp=player.max_hit_points,
            player_ap=player_ap,
            player_max_ap=player_max_ap,
            player_effects=player_effects,
            enemy_name=enemy.name,
            enemy_hp=enemy.hp,
            enemy_max_hp=enemy.max_hp,
            enemy_effects=enemy_effects,
            enemy_has_cover=enemy_has_cover,
            action_feedback=getattr(cm, 'last_action_feedback', None),
            available_actions=available_actions
        )


class DialogueState(EngineState):
    """State for dialogue interactions."""

    def __init__(self, engine: "ImprovedGameEngine", npc_id: str = "", current_node: str = ""):
        super().__init__(engine, "Dialogue")
        self.npc_id = npc_id
        self.current_node = current_node

    def handle_input(self, command: str):
        self._handle_dialogue_command(command)

    def _handle_dialogue_command(self, command: str):
        """
        Moved from GameEngine._handle_dialogue_command
        """
        if command in ["help", "?"]:
            self.engine.ui_manager.show_help("dialogue")
            return
            
        if command in ["exit", "quit", "bye", "leave"]:
            self.engine.change_state(ExplorationState(self.engine))
            return
        
        # Pause logic
        if command in ["pause", "menu", "esc"]:
            self.engine.change_state(PauseMenuState(self.engine))
            return

        node = self.engine.current_dialogue_node
        if not node:
            self.engine.change_state(ExplorationState(self.engine))
            return

        options = node.get_available_options(self.engine.state)

        # Safeguard: if no options are available, add a default "Exit" option
        if not options:
            from fallout_berlin.dialogue import DialogueOption
            exit_opt = DialogueOption("Goodbye. [Engine Safeguard]", end_dialogue=True)
            exit_opt.end_dialogue = True
            options = [exit_opt]

        try:
            choice = int(command)
            if 1 <= choice <= len(options):
                option = options[choice - 1]

                self.engine.dialogue_manager.process_option(option, self.engine)
        except (ValueError, IndexError):
            print("Invalid selection.")

    def render(self):
        """Render dialogue interface"""
        self.engine._display_dialogue_node()

class MainMenuState(EngineState):
    """State for the main menu."""

    def __init__(self, engine: "ImprovedGameEngine"):
        super().__init__(engine, "Menu")
        self.options = ["New Game", "Load Game", "Quit"]

    def handle_input(self, command: str):
        cmd = command.strip().lower()
        if cmd in ["1", "new game", "new"]:
            # Reset engine state for a clean new game
            self.engine.state = self.engine.state.__class__()
            self.engine.start_new_game()
        elif cmd in ["2", "load game", "load"]:
            if self.engine.load_game():
                self.engine.change_state(ExplorationState(self.engine))
        elif cmd in ["3", "quit", "exit", "q"]:
            self.engine._quit_game()
        else:
            print(f"{Fore.YELLOW}Please choose an option from the menu.{Style.RESET_ALL}")

    def update(self):
        pass

    def render(self):
        self.engine.ui_manager.draw_main_menu("MAIN MENU", self.options, True)


class PauseMenuState(EngineState):
    """State for the pause menu."""

    def __init__(self, engine: "ImprovedGameEngine"):
        super().__init__(engine, "Paused")
        self.options = ["Resume", "Settings", "Save Game", "Main Menu", "Quit Desktop"]

    def handle_input(self, command: str):
        cmd = command.strip().lower()
        
        if cmd in ["1", "resume", "r", "esc"]:
            self._resume()
        elif cmd in ["2", "settings", "options"]:
            self.engine.ui_manager.show_settings_menu()
        elif cmd in ["3", "save", "save game"]:
            self.engine._save_game()
        elif cmd in ["4", "main menu", "menu"]:
            self.engine.change_state(MainMenuState(self.engine))
        elif cmd in ["5", "quit", "exit", "q"]:
            self.engine._quit_game()
        else:
            print(f"{Fore.YELLOW}Paused. Choose an option.{Style.RESET_ALL}")
            
    def _resume(self):
        # Logic to return to previous state
        # In this simple state machine, we can check history or default to Exploration
        # History format: ['MainMenuState', 'ExplorationState', 'CombatState', 'PauseMenuState']
        # We want the one before PauseMenuState.
        
        prev_state_name = "ExplorationState"
        if len(self.engine.state_history) >= 1:
            # The last item in history is the one we just left (PauseMenuState replaced it, but change_state appends the OLD one)
            # Wait, change_state logic:
            # if self.current_state: history.append(type(self.current_state).__name__)
            # So history[-1] is indeed the state we just paused from.
            prev_state_name = self.engine.state_history[-1]
            
        if prev_state_name == "CombatState":
            self.engine.change_state(CombatState(self.engine))
        elif prev_state_name == "DialogueState":
            # Recreating DialogueState needs context (npc_id, node). 
            # Ideally DialogueState should persist. 
            # For now, we fall back to Exploration if we can't restore perfectly, 
            # OR we check if engine has stored dialogue context.
            if self.engine.current_dialogue_tree and self.engine.current_dialogue_node:
                 self.engine.change_state(DialogueState(
                     self.engine, 
                     self.engine.current_dialogue_tree.npc_id, 
                     self.engine.current_dialogue_node.node_id
                 ))
            else:
                self.engine.change_state(ExplorationState(self.engine))
        else:
            self.engine.change_state(ExplorationState(self.engine))

    def render(self):
        self.engine.ui_manager.display_menu("PAUSED", self.options, prompt=" > ", numbered=True, allow_cancel=False)