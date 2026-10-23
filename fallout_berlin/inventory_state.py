from typing import TYPE_CHECKING, List, Any
import time
from colorama import Fore, Style
from fallout_berlin.engine_states import EngineState
from fallout_berlin.item import Weapon, Armor, Consumable

if TYPE_CHECKING:
    from fallout_berlin.improved_game_engine import ImprovedGameEngine

class InventoryState(EngineState):
    """State for managing inventory interactively."""

    def __init__(self, engine: "ImprovedGameEngine"):
        super().__init__(engine, "Inventory")
        self.selected_item = None
        self.items = []
        self._refresh_items()

    def _refresh_items(self):
        if self.engine.state.inventory:
            self.items = self.engine.state.inventory.items
        else:
            self.items = []

    def render(self):
        self.engine.ui_manager.clear_screen()
        self.engine.ui_manager.display_header("PIP-BOY 3000 - INVENTORY", style="double", color=Fore.GREEN)
        
        if self.engine.state.inventory:
            current_weight = self.engine.state.inventory.get_total_weight()
            max_weight = self.engine.state.inventory.max_weight
            print(f"{Fore.GREEN}Weight: {current_weight}/{max_weight} lbs{Style.RESET_ALL}\n")

        if self.selected_item:
            self._render_item_details()
        else:
            self._render_item_list()

    def _render_item_list(self):
        if not self.items:
            print("  (Empty)")
        else:
            print(f"{Fore.CYAN}{'ID':<4} {'Name':<25} {'Type':<12} {'Wt':<6} {'Val':<6}{Style.RESET_ALL}")
            print("-" * 60)
            for i, item in enumerate(self.items, 1):
                item_type = type(item).__name__
                weight = getattr(item, 'weight', 0)
                value = getattr(item, 'value', 0)
                
                equipped_mark = ""
                if self.engine.state.player:
                    if self.engine.state.player.equipped_weapon == item:
                        equipped_mark = " [E]"
                    elif self.engine.state.player.equipped_armor == item:
                        equipped_mark = " [E]"

                print(f"{i:<4} {item.name}{equipped_mark:<25} {item_type:<12} {weight:<6} {value:<6}")
        
        print(f"\n{Fore.YELLOW}[1-{len(self.items)}] Select Item   [C] Close{Style.RESET_ALL}")

    def _render_item_details(self):
        item = self.selected_item
        print(f"{Fore.CYAN}Item: {item.name}{Style.RESET_ALL}")
        print(f"Type: {type(item).__name__}")
        print(f"Description: {getattr(item, 'description', 'No description')}")
        
        if hasattr(item, 'damage'):
            print(f"Damage: {item.damage}")
        if hasattr(item, 'defense'):
            print(f"Defense: {item.defense}")
        if hasattr(item, 'effect_type'):
            print(f"Effect: {item.effect_type} ({getattr(item, 'effect_value', 0)})")
            
        print(f"\n{Fore.YELLOW}Actions:{Style.RESET_ALL}")
        print("  [U] Use/Equip")
        print("  [D] Drop")
        print("  [B] Back")

    def handle_input(self, command: str):
        cmd = command.lower().strip()
        
        if cmd in ['c', 'close', 'exit', 'q']:
            self._exit_state()
            return

        if self.selected_item:
            if cmd in ['b', 'back']:
                self.selected_item = None
            elif cmd in ['u', 'use', 'equip']:
                self._use_item(self.selected_item)
            elif cmd in ['d', 'drop']:
                self._drop_item(self.selected_item)
            return

        if command.isdigit():
            try:
                idx = int(command) - 1
                if 0 <= idx < len(self.items):
                    self.selected_item = self.items[idx]
                else:
                    print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
                    time.sleep(0.5)
            except ValueError:
                pass

    def _use_item(self, item):
        if isinstance(item, (Weapon, Armor)):
            if self.engine.state.player.equip_item(item):
                print(f"{Fore.GREEN}Equipped {item.name}.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Cannot equip {item.name}.{Style.RESET_ALL}")
        elif isinstance(item, Consumable):
            self.engine._use_consumable(item)
            self._refresh_items()
            if item not in self.items:
                self.selected_item = None
        else:
             print(f"{Fore.YELLOW}Cannot use this item.{Style.RESET_ALL}")
        
        time.sleep(1)

    def _drop_item(self, item):
        if self.engine.state.inventory.remove_item(item.name, 1):
            location = self.engine.location_manager.get_location(self.engine.state.current_location)
            if location:
                location.add_item(item)
                print(f"{Fore.GREEN}Dropped {item.name}.{Style.RESET_ALL}")
            else:
                self.engine.state.inventory.add_item(item)
                print(f"{Fore.RED}Cannot drop here.{Style.RESET_ALL}")
        
        self._refresh_items()
        self.selected_item = None
        time.sleep(1)

    def _exit_state(self):
        from fallout_berlin.engine_states import ExplorationState
        self.engine.change_state(ExplorationState(self.engine))