from typing import TYPE_CHECKING
from colorama import Fore, Style
from fallout_berlin.engine_states import EngineState

if TYPE_CHECKING:
    from fallout_berlin.improved_game_engine import ImprovedGameEngine

class VatsState(EngineState):
    """State for VATS targeting system."""

    def __init__(self, engine: "ImprovedGameEngine"):
        super().__init__(engine, "V.A.T.S.")
        self.parts = ["Head", "Torso", "Left Arm", "Right Arm", "Left Leg", "Right Leg"]
        self.chances = engine.combat_manager.get_vats_chances()
        engine.combat_manager.in_vats = True

    def render(self):
        self.engine.ui_manager.clear_screen()
        self.engine.ui_manager.display_header("VAULT-TEC ASSISTED TARGETING SYSTEM", style="double", color=Fore.GREEN)
        
        enemy = self.engine.combat_manager.current_enemy
        if not enemy:
            self._exit_vats()
            return

        print(f"\n{Fore.RED}TARGET: {enemy.name.upper()} (HP: {enemy.hp}/{enemy.max_hp}){Style.RESET_ALL}\n")
        
        # Display body parts with hit chances
        print(f"{Fore.CYAN}{'ID':<4} {'Body Part':<15} {'Hit Chance':<12} {'AP Cost'}{Style.RESET_ALL}")
        print("-" * 50)
        
        for i, part in enumerate(self.parts, 1):
            chance = self.chances.get(part, 0)
            color = Fore.GREEN if chance >= 70 else (Fore.YELLOW if chance >= 40 else Fore.RED)
            print(f"{i:<4} {part:<15} {color}{chance}%{Style.RESET_ALL}        5 AP")
            
        print(f"\n{Fore.GREEN}AP Available: {self.engine.state.player.current_ap}/{self.engine.state.player.max_ap}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}[1-6] Select Target   [C] Cancel (or type a body part){Style.RESET_ALL}")

    def handle_input(self, command: str):
        cmd = command.lower().strip()
        
        if cmd in ['c', 'cancel', 'exit', 'back']:
            self._exit_vats()
            return
            
        if cmd.isdigit():
            try:
                idx = int(cmd) - 1
                if 0 <= idx < len(self.parts):
                    target = self.parts[idx]
                    self._execute_attack(target)
                else:
                    print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
        else:
            # Allow typing part name directly
            for part in self.parts:
                if part.lower() == cmd:
                    self._execute_attack(part)
                    return
            print(f"{Fore.RED}Invalid target. Choose 1-6 or type a body part.{Style.RESET_ALL}")

    def _execute_attack(self, part: str):
        combat_manager = self.engine.combat_manager
        if self.engine.state.player.current_ap < combat_manager.ATTACK_AP_COST:
            print(f"{Fore.RED}Not enough Action Points!{Style.RESET_ALL}")
            self._exit_vats()
            return

        from fallout_berlin.engine_states import CombatState
        combat_manager.in_vats = False
        self.engine.change_state(CombatState(self.engine))
        self.engine.current_state.handle_input(f"vats {part}")

    def _exit_vats(self):
        from fallout_berlin.engine_states import CombatState
        self.engine.combat_manager.in_vats = False
        self.engine.change_state(CombatState(self.engine))