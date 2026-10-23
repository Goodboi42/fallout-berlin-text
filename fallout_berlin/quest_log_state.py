from typing import TYPE_CHECKING, List, Dict, Any
import time
from colorama import Fore, Style
from fallout_berlin.engine_states import EngineState

if TYPE_CHECKING:
    from fallout_berlin.improved_game_engine import ImprovedGameEngine

class QuestLogState(EngineState):
    """State for viewing active quests and objectives."""

    def __init__(self, engine: "ImprovedGameEngine"):
        super().__init__(engine, "Quest Log")
        self.quests = []
        self.selected_quest = None

    def render(self):
        self.quests = (
            self.engine.quest_manager.get_active_quests()
            + self.engine.quest_manager.get_completed_quests()
        )
        self.engine.ui_manager.clear_screen()
        self.engine.ui_manager.display_header("PIP-BOY 3000 - QUEST LOG", style="double", color=Fore.YELLOW)

        if self.selected_quest:
            self._render_quest_details(self.selected_quest)
        else:
            self._render_quest_list()

    def _render_quest_list(self):
        active = self.engine.quest_manager.get_active_quests()
        completed = self.engine.quest_manager.get_completed_quests()
        if not self.quests:
            print(f"\n{Fore.WHITE}No active or completed quests.{Style.RESET_ALL}")
            print(f"\n{Fore.YELLOW}[C] Close{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}Active Quests:{Style.RESET_ALL}")
        for i, quest in enumerate(self.quests, 1):
            if quest not in active:
                continue
            name = self._get_attr(quest, 'title', 'Unknown Quest')
            status = self._get_attr(quest, 'state', 'Active')
            status = getattr(status, "value", status)
            print(f"  {Fore.YELLOW}[{i}]{Style.RESET_ALL} {name} ({status})")
        if completed:
            print(f"\n{Fore.CYAN}Completed Quests:{Style.RESET_ALL}")
            for i, quest in enumerate(self.quests, 1):
                if quest in completed:
                    print(f"  {Fore.YELLOW}[{i}]{Style.RESET_ALL} {self._get_attr(quest, 'title', 'Unknown Quest')} (completed)")
        print(f"\n{Fore.YELLOW}[1-{len(self.quests)}] Select Quest   [C] Close{Style.RESET_ALL}")

    def _render_quest_details(self, quest):
        name = self._get_attr(quest, 'title', 'Unknown Quest')
        desc = self._get_attr(quest, 'description', 'No description.')
        objectives = self._get_attr(quest, 'objectives', [])

        print(f"\n{Fore.CYAN}Quest: {name}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{desc}{Style.RESET_ALL}\n")
        
        print(f"{Fore.CYAN}Objectives:{Style.RESET_ALL}")
        if objectives:
            for obj in objectives:
                text = self._get_attr(obj, 'text', self._get_attr(obj, 'description', 'Unknown Objective'))
                completed = self._get_attr(obj, 'completed', False)
                
                status_icon = f"{Fore.GREEN}[X]{Style.RESET_ALL}" if completed else f"{Fore.RED}[ ]{Style.RESET_ALL}"
                print(f"  {status_icon} {text}")
        else:
            print("  No active objectives.")

        print(f"\n{Fore.YELLOW}[B] Back to List   [C] Close{Style.RESET_ALL}")

    def handle_input(self, command: str):
        cmd = command.lower().strip()
        if cmd in ['c', 'close', 'exit', 'q']:
            self._exit_quest_log()
            return
        
        if self.selected_quest:
            if cmd in ['b', 'back']:
                self.selected_quest = None
            return

        if command.isdigit():
            try:
                idx = int(command) - 1
                if 0 <= idx < len(self.quests):
                    self.selected_quest = self.quests[idx]
                else:
                    print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
                    time.sleep(0.5)
            except ValueError:
                pass

    def _exit_quest_log(self):
        from fallout_berlin.engine_states import ExplorationState
        self.engine.change_state(ExplorationState(self.engine))

    def _get_attr(self, obj, attr, default):
        """Helper to safely get attributes from objects or dicts"""
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)