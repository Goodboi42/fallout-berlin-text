from typing import TYPE_CHECKING, List, Dict, Any
import time
from colorama import Fore, Style
from fallout_berlin.engine_states import EngineState

if TYPE_CHECKING:
    from fallout_berlin.improved_game_engine import ImprovedGameEngine

class CraftingState(EngineState):
    """State for crafting items."""

    def __init__(self, engine: "ImprovedGameEngine"):
        super().__init__(engine, "Crafting")
        self.recipes = engine.crafting_manager.recipes
        self.available_recipes = []
        self._refresh_recipes()

    def _refresh_recipes(self):
        self.available_recipes = []
        player_perks = getattr(self.engine.state.player, "perks", [])
        inventory = self.engine.state.inventory
        
        for rid, recipe in self.recipes.items():
            perk_req = recipe.get("perk_req")
            has_perk = True
            if perk_req and perk_req not in player_perks:
                has_perk = False
            
            can_craft = True
            requirements = recipe.get("requirements", {})
            for item_name, quantity in requirements.items():
                if not inventory.has_item(item_name, quantity):
                    can_craft = False
                    break
            
            self.available_recipes.append({
                "id": rid,
                "name": recipe["name"],
                "reqs": requirements,
                "perk_req": perk_req,
                "can_craft": can_craft and has_perk,
                "missing_perk": not has_perk
            })

    def render(self):
        self.engine.ui_manager.clear_screen()
        self.engine.ui_manager.display_header("WORKBENCH - CRAFTING", style="double", color=Fore.YELLOW)
        
        if not self.available_recipes:
            print(f"\n{Fore.WHITE}No recipes known.{Style.RESET_ALL}")
            print(f"\n{Fore.YELLOW}[C] Close{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}{'ID':<4} {'Item Name':<25} {'Status':<12} {'Requirements'}{Style.RESET_ALL}")
        print("-" * 70)
        
        for i, r in enumerate(self.available_recipes, 1):
            status = f"{Fore.GREEN}Craftable{Style.RESET_ALL}" if r["can_craft"] else f"{Fore.RED}Missing Mats{Style.RESET_ALL}"
            if r["missing_perk"]:
                status = f"{Fore.RED}Need Perk{Style.RESET_ALL}"
            
            req_str = ", ".join([f"{k} x{v}" for k, v in r["reqs"].items()])
            if r["perk_req"]:
                req_str += f" ({r['perk_req']})"
                
            print(f"{i:<4} {r['name']:<25} {status:<12} {req_str}")
            
        print(f"\n{Fore.YELLOW}[1-{len(self.available_recipes)}] Craft Item   [C] Close{Style.RESET_ALL}")

    def handle_input(self, command: str):
        cmd = command.lower().strip()
        if cmd in ['c', 'close', 'exit', 'q', 'back']:
            self._exit_crafting()
            return
        
        if command.isdigit():
            try:
                idx = int(command) - 1
                if 0 <= idx < len(self.available_recipes):
                    recipe_data = self.available_recipes[idx]
                    self._attempt_craft(recipe_data)
                else:
                    print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
                    time.sleep(0.5)
            except ValueError:
                pass

    def _attempt_craft(self, recipe_data):
        if recipe_data["missing_perk"]:
            print(f"{Fore.RED}You lack the required perk: {recipe_data['perk_req']}{Style.RESET_ALL}")
            time.sleep(1)
            return

        if not recipe_data["can_craft"]:
            print(f"{Fore.RED}You don't have enough materials.{Style.RESET_ALL}")
            time.sleep(1)
            return
            
        result = self.engine.crafting_manager.craft(
            recipe_data["id"], self.engine.state.inventory, self.engine.state.player
        )
        
        if result:
            print(f"\n{Fore.GREEN}Successfully crafted: {result}{Style.RESET_ALL}")
            self.engine._update_survival(move_cost=True)
            self._refresh_recipes()
            time.sleep(1)
        else:
            print(f"\n{Fore.RED}Crafting failed.{Style.RESET_ALL}")
            time.sleep(1)

    def _exit_crafting(self):
        from fallout_berlin.engine_states import ExplorationState
        self.engine.change_state(ExplorationState(self.engine))