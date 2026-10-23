from typing import List, Any, TYPE_CHECKING
from colorama import Fore, Style
from fallout_berlin.engine_states import EngineState

if TYPE_CHECKING:
    from fallout_berlin.improved_game_engine import ImprovedGameEngine

class LootingState(EngineState):
    """State for looting containers or enemies."""

    def __init__(self, engine: "ImprovedGameEngine", container_name: str, items: List[Any]):
        super().__init__(engine, "Loot")
        self.container_name = container_name
        self.items = items

    def handle_input(self, command: str):
        if command in ["exit", "leave", "close", "done", "q", "back"]:
            self._return_to_exploration()
            return

        if command == "take all":
            self._take_all()
            return

        if command.startswith("take "):
            item_name = command[5:].strip()
            self._take_item(item_name)
            return
            
        if command in ["look", "ls", "list"]:
            return

        print(f"{Fore.YELLOW}Unknown command. Options: take <item>, take all, close{Style.RESET_ALL}")

    def render(self):
        self.engine.ui_manager.clear_screen()
        print(f"\n{Fore.CYAN}═══ {self.container_name.upper()} ═══{Style.RESET_ALL}")
        
        if not self.items:
            print(f"{Fore.WHITE}(Empty){Style.RESET_ALL}")
        else:
            print(f"{Fore.WHITE}Contents:{Style.RESET_ALL}")
            for i, item in enumerate(self.items, 1):
                weight_str = f"{item.weight} lbs" if hasattr(item, 'weight') else "0 lbs"
                print(f"  {i}. {item.name} ({weight_str})")
        
        current_weight = self.engine.state.inventory.get_total_weight()
        max_weight = self.engine.state.inventory.max_weight
        print(f"\n{Fore.GREEN}Inventory: {current_weight}/{max_weight} lbs{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Commands: [take all] [take <name/number>] [close]{Style.RESET_ALL}")

    def _take_all(self):
        if not self.items:
            print("Nothing to take.")
            return

        items_to_take = list(self.items)
        taken_count = 0
        
        for item in items_to_take:
            if self.engine.state.inventory.add_item(item):
                print(f"{Fore.GREEN}Taken: {item.name}{Style.RESET_ALL}")
                self.items.remove(item)
                taken_count += 1
            else:
                print(f"{Fore.RED}Inventory full! Cannot take {item.name}{Style.RESET_ALL}")
        
        if taken_count > 0 and not self.items:
            print(f"{Fore.GREEN}Container empty.{Style.RESET_ALL}")

    def _take_item(self, item_name: str):
        if item_name.isdigit():
            idx = int(item_name) - 1
            if 0 <= idx < len(self.items):
                item = self.items[idx]
                if self.engine.state.inventory.add_item(item):
                    print(f"{Fore.GREEN}Taken: {item.name}{Style.RESET_ALL}")
                    self.items.pop(idx)
                else:
                    print(f"{Fore.RED}Inventory full!{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Invalid item number.{Style.RESET_ALL}")
            return

        found = False
        for i, item in enumerate(self.items):
            if item.name.lower() == item_name.lower():
                if self.engine.state.inventory.add_item(item):
                    print(f"{Fore.GREEN}Taken: {item.name}{Style.RESET_ALL}")
                    self.items.pop(i)
                else:
                    print(f"{Fore.RED}Inventory full!{Style.RESET_ALL}")
                found = True
                break
        
        if not found:
            print(f"{Fore.RED}Item not found.{Style.RESET_ALL}")

    def _return_to_exploration(self):
        ExplorationState, _, _, _ = self.engine._get_engine_states()
        self.engine.change_state(ExplorationState(self.engine))