from typing import TYPE_CHECKING, List, Dict, Any
import operator
import time
from colorama import Fore, Style
from fallout_berlin.engine_states import EngineState
from fallout_berlin.art_master import ArtEffects

if TYPE_CHECKING:
    from fallout_berlin.improved_game_engine import ImprovedGameEngine

class LevelUpState(EngineState):
    """State for handling character progression."""

    def __init__(self, engine: "ImprovedGameEngine"):
        super().__init__(engine, "Level Up")
        self.sub_state = "main"  # main, special, perks
        self.perks_db = engine.perks_db
        self.selectable_perks = []

    def enter(self):
        # Play effect
        ArtEffects.level_up_sequence().play(max_loops=1)
        self._show_milestone_message()

    def render(self):
        self.engine.ui_manager.clear_screen()
        
        # Header
        print(f"\n{Fore.YELLOW}{'★' * 60}")
        print(f"  LEVEL UP! You reached level {self.engine.state.player.level}!")
        print(f"{'★' * 60}{Style.RESET_ALL}\n")
        
        print(f"{Fore.GREEN}Points Remaining: {self.engine.state.player.stat_points}{Style.RESET_ALL}\n")

        if self.sub_state == "main":
            self._render_main()
        elif self.sub_state == "special":
            self._render_special()
        elif self.sub_state == "perks":
            self._render_perks()

    def _render_main(self):
        print("How will you develop your character?")
        print(f"  {Fore.CYAN}1.{Style.RESET_ALL} Increase S.P.E.C.I.A.L. Stats")
        print(f"  {Fore.CYAN}2.{Style.RESET_ALL} Select a New Perk")
        print(f"  {Fore.CYAN}C.{Style.RESET_ALL} Decide Later (Exit)")
        print(f"\n{Fore.YELLOW}Choice:{Style.RESET_ALL} ", end="")

    def _render_special(self):
        stats = ["strength", "perception", "endurance", "charisma", 
                "intelligence", "agility", "luck"]
        
        print(f"{Fore.CYAN}S.P.E.C.I.A.L. TRAINING{Style.RESET_ALL}\n")
        
        for i, stat in enumerate(stats, 1):
            current = getattr(self.engine.state.player, stat)
            max_val = 10
            bar = "█" * current + "░" * (max_val - current)
            print(f"  {i}. {stat.capitalize():<12} [{Fore.GREEN}{bar}{Style.RESET_ALL}] {current}/10")
        
        print(f"\n  C. Back")
        print(f"\n{Fore.YELLOW}Select stat to increase (1-7):{Style.RESET_ALL} ", end="")

    def _render_perks(self):
        # Filter perks
        available = [p for p in self.perks_db 
                    if self._check_perk_requirements(p, self.engine.state.player)]
        
        current_perks = getattr(self.engine.state.player, "perks", [])
        self.selectable_perks = [p for p in available if p["name"] not in current_perks]

        if not self.selectable_perks:
            print(f"{Fore.YELLOW}You have learned all available perks!{Style.RESET_ALL}")
            print("\n  C. Back")
            return

        print(f"{Fore.CYAN}AVAILABLE PERKS{Style.RESET_ALL}\n")
        
        for i, perk in enumerate(self.selectable_perks, 1):
            req_text = perk.get("req_text", "None")
            print(f"  {i}. {Fore.YELLOW}{perk.get('name', 'Unknown')}{Style.RESET_ALL}")
            print(f"     Requirements: {req_text}")
            print(f"     {perk.get('desc', 'No description')}\n")
        
        print(f"  C. Back")
        print(f"\n{Fore.YELLOW}Choose a perk (1-{len(self.selectable_perks)}):{Style.RESET_ALL} ", end="")

    def handle_input(self, command: str):
        if self.sub_state == "main":
            if command == "1":
                self.sub_state = "special"
            elif command == "2":
                self.sub_state = "perks"
            elif command.lower() == "c":
                self._exit_level_up()
            else:
                print(f"{Fore.RED}Invalid choice.{Style.RESET_ALL}")
        
        elif self.sub_state == "special":
            if command.lower() == "c":
                self.sub_state = "main"
                return

            stats = ["strength", "perception", "endurance", "charisma", 
                    "intelligence", "agility", "luck"]
            
            idx = -1
            if command.isdigit():
                idx = int(command) - 1
            elif command.lower() in stats:
                idx = stats.index(command.lower())
            
            if 0 <= idx < len(stats):
                stat = stats[idx]
                current = getattr(self.engine.state.player, stat)
                if current >= 10:
                    print(f"{Fore.RED}Stat maxed out!{Style.RESET_ALL}")
                    time.sleep(1)
                else:
                    self.engine.state.player.set_special(stat, current + 1)
                    self.engine.state.player.stat_points -= 1
                    print(f"{Fore.GREEN}{stat.capitalize()} increased!{Style.RESET_ALL}")
                    time.sleep(0.5)
                    self._check_points()
            else:
                print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
                time.sleep(0.5)

        elif self.sub_state == "perks":
            if command.lower() == "c":
                self.sub_state = "main"
                return
            
            if not self.selectable_perks:
                 return

            if command.isdigit():
                idx = int(command) - 1
                if 0 <= idx < len(self.selectable_perks):
                    selected = self.selectable_perks[idx]
                    self.engine.state.player.perks.append(selected["name"])
                    self.engine.state.player.stat_points -= 1
                    print(f"{Fore.GREEN}Perk gained: {selected['name']}{Style.RESET_ALL}")
                    self._apply_perk_effects(selected)
                    time.sleep(1)
                    self._check_points()
                else:
                    print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
                    time.sleep(0.5)
            else:
                print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
                time.sleep(0.5)

    def _check_points(self):
        if self.engine.state.player.stat_points <= 0:
            self._exit_level_up()

    def _exit_level_up(self):
        from fallout_berlin.engine_states import ExplorationState
        self.engine.change_state(ExplorationState(self.engine))

    def _show_milestone_message(self):
        level = self.engine.state.player.level
        if level % 5 != 0:
            return
        
        milestones = {
            5: "You're starting to get the hang of this wasteland thing.",
            10: "A true survivor. Berlin is starting to fear you.",
            15: "Legendary status approaching. The Wall itself trembles.",
            20: "The Apex Predator of the Spree.",
            25: "Your name is whispered in every faction hall.",
            30: "You have become a legend of the wastes.",
        }
        
        message = milestones.get(level, "A major milestone reached!")
        
        print(f"\n{Fore.CYAN}{'═' * 60}")
        print(f"  MILESTONE: LEVEL {level}")
        print(f"  {message}")
        print(f"{'═' * 60}{Style.RESET_ALL}\n")
        time.sleep(2)

    def _check_perk_requirements(self, perk: Dict, player) -> bool:
        ops = {
            ">=": operator.ge,
            ">": operator.gt,
            "<=": operator.le,
            "<": operator.lt,
            "==": operator.eq,
            "!=": operator.ne
        }
        
        for req in perk.get("req", []):
            stat = req["stat"]
            value = req["value"]
            op_str = req["op"]
            
            player_val = getattr(player, stat, 0)
            op_func = ops.get(op_str)
            
            if op_func and not op_func(player_val, value):
                return False
        return True

    def _apply_perk_effects(self, perk: Dict):
        name = perk["name"]
        if name == "Lifegiver":
            self.engine.state.player.max_hit_points += 20
            self.engine.state.player.hit_points += 20
            print(f"{Fore.GREEN}+20 Max HP!{Style.RESET_ALL}")
        elif name == "Trümmerfrau":
            self.engine.state.player.carry_weight += 50
            if self.engine.state.inventory:
                self.engine.state.inventory.max_weight = self.engine.state.player.carry_weight
            print(f"{Fore.GREEN}+50 Carry Weight!{Style.RESET_ALL}")
        elif name == "Solar Powered":
            print(f"{Fore.GREEN}Regenerate HP in sunlight!{Style.RESET_ALL}")