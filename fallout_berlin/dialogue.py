"""
Dialogue System
Handles NPC dialogue trees and conversation management
"""

from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import json
import os
from colorama import Fore, Style

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fallout_berlin.quest import QuestState
from fallout_berlin.item import create_item


class DialogueCondition:
    """Represents a condition that must be met for dialogue option"""

    def __init__(self, condition_type: str, **kwargs):
        self.condition_type = condition_type
        self.params = kwargs

    def check(self, game_state) -> bool:
        """Check if condition is met"""
        if self.condition_type == "skill":
            skill = self.params.get("skill")
            min_value = self.params.get("min", 0)
            if game_state.player:
                return game_state.player.get_skill(skill) >= min_value
        elif self.condition_type == "faction_rep":
            faction = self.params.get("faction")
            min_rep = self.params.get("min", 0)
            return game_state.get_faction_reputation(faction) >= min_rep
        elif self.condition_type == "has_item":
            item_name = self.params.get("item")
            quantity = self.params.get("quantity", 1)
            if game_state.inventory:
                return game_state.inventory.has_item(item_name, quantity)
        elif self.condition_type == "world_flag":
            flag = self.params.get("flag")
            value = self.params.get("value", True)
            return game_state.get_world_flag(flag) == value
        elif self.condition_type == "quest_state":
            quest_id = self.params.get("quest")
            state = self.params.get("state")
            if quest_id in game_state.quests:
                current_state = game_state.quests[quest_id].state
                # Handle string comparison if state is passed as string from JSON
                if isinstance(state, str):
                    # Convert string to enum value if possible, or compare values
                    return current_state.value == state
                else:
                    return current_state == state
        elif self.condition_type == "and":
            items = self.params.get("items", [])
            for item in items:
                cond = DialogueCondition(item["type"], **item.get("params", {}))
                if not cond.check(game_state):
                    return False
            return True
        elif self.condition_type == "or":
            items = self.params.get("items", [])
            for item in items:
                cond = DialogueCondition(item["type"], **item.get("params", {}))
                if cond.check(game_state):
                    return True
            return False
        elif self.condition_type == "always":
            return True
        elif self.condition_type == "never":
            return False

        return False


class DialogueOption:
    """A single dialogue option/response"""

    def __init__(
        self,
        text: str,
        next_node: Optional[str] = None,
        condition: Optional[DialogueCondition] = None,
        action: Optional[Callable] = None,
    ):
        self.text = text
        self.next_node = next_node
        self.condition = condition
        self.action = action  # Function to call when selected
        self.end_dialogue = False

    def is_available(self, game_state) -> bool:
        """Check if this option is available"""
        if self.condition:
            return self.condition.check(game_state)
        return True


class DialogueNode:
    """A node in the dialogue tree"""

    def __init__(self, node_id: str, speaker: str, text: str):
        self.node_id = node_id
        self.speaker = speaker  # 'player' or NPC name
        self.text = text
        self.options: List[DialogueOption] = []
        self.end_dialogue = False  # If True, dialogue ends after this node

    def add_option(self, option: DialogueOption):
        """Add a dialogue option"""
        self.options.append(option)

    def get_available_options(self, game_state) -> List[DialogueOption]:
        """Get all available options based on conditions"""
        return [opt for opt in self.options if opt.is_available(game_state)]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "node_id": self.node_id,
            "speaker": self.speaker,
            "text": self.text,
            "options": [
                {
                    "text": opt.text,
                    "next_node": opt.next_node,
                    "condition": {
                        "type": opt.condition.condition_type,
                        "params": opt.condition.params,
                    }
                    if opt.condition
                    else None,
                }
                for opt in self.options
            ],
            "end_dialogue": self.end_dialogue,
        }


class DialogueTree:
    """Complete dialogue tree for an NPC"""

    def __init__(self, npc_id: str, npc_name: str):
        self.npc_id = npc_id
        self.npc_name = npc_name
        self.nodes: Dict[str, DialogueNode] = {}
        self.start_node: Optional[str] = None

    def add_node(self, node: DialogueNode):
        """Add a dialogue node"""
        self.nodes[node.node_id] = node
        if not self.start_node:
            self.start_node = node.node_id

    def get_node(self, node_id: str) -> Optional[DialogueNode]:
        """Get a dialogue node"""
        return self.nodes.get(node_id)

    def get_start_node(self) -> Optional[DialogueNode]:
        """Get the starting dialogue node"""
        if self.start_node:
            return self.nodes.get(self.start_node)
        return None


class DialogueManager:
    """Manages all dialogue trees"""

    def __init__(self):
        self.dialogue_trees: Dict[str, DialogueTree] = {}
        self.action_handlers: Dict[str, Callable] = {}
        self._register_actions()
        self._initialize_dialogue()

    def _turn_in_quest_item(self, state, quest_id: str, item_id: str) -> bool:
        quest = state.quests.get(quest_id)
        if (
            quest is None
            or quest.state != QuestState.ACTIVE
            or not state.inventory.remove_item(item_id)
        ):
            return False

        quest.complete()
        return True

    def _register_actions(self):
        """Register available dialogue actions"""
        self.action_handlers["start_currywurst_quest"] = (
            self._action_start_currywurst_quest
        )
        self.action_handlers["complete_currywurst_quest"] = (
            self._action_complete_currywurst_quest
        )
        self.action_handlers["start_green_thumb"] = self._action_start_green_thumb
        self.action_handlers["trigger_green_thumb_stage_2"] = self._action_trigger_green_thumb_stage_2
        self.action_handlers["complete_green_thumb"] = self._action_complete_green_thumb
        self.action_handlers["start_iron_will"] = self._action_start_iron_will
        self.action_handlers["complete_iron_will"] = self._action_complete_iron_will
        self.action_handlers["start_bureaucrats_nightmare"] = self._action_start_bureaucrats_nightmare
        self.action_handlers["complete_bureaucrats_nightmare"] = self._action_complete_bureaucrats_nightmare
        self.action_handlers["buy_currywurst"] = self._action_buy_currywurst
        self.action_handlers["buy_doner"] = self._action_buy_doner
        self.action_handlers["buy_doner_kebab"] = self._action_buy_doner_kebab
        self.action_handlers["open_shop"] = self._action_open_shop
        for action, quest_id in {
            "start_bureaucracy_blues": "bureaucracy_blues",
            "start_unit_247_repair": "unit_247_repair",
            "start_klaus_record_hunt": "klaus_record_hunt",
            "start_doner_mafia_protection": "doner_mafia_protection",
            "start_story_for_gaertner_quest": "story_for_gaertner",
            "start_vault_b12_key_quest": "vault_b12_key_quest",
        }.items():
            self.action_handlers[action] = (
                lambda state, quest_id=quest_id: self._action_start_quest(
                    state, quest_id
                )
            )
        self.action_handlers["complete_unit_247_repair"] = (
            self._action_complete_unit_247_repair
        )

    def _action_open_shop(self, state):
        return "open_shop"

    @staticmethod
    def _action_start_quest(state, quest_id):
        quest = state.quests.get(quest_id)
        if quest and quest.state == QuestState.NOT_STARTED:
            quest.start()
            print(f"\n{Fore.YELLOW}[Quest Started: {quest.title}]{Style.RESET_ALL}")

    def _action_complete_unit_247_repair(self, state):
        quest = state.quests.get("unit_247_repair")
        if (
            not quest
            or quest.state != QuestState.ACTIVE
            or not state.inventory.has_item("protectron_spare_parts")
        ):
            print(f"\n{Fore.RED}Unit 247 still needs its spare parts.{Style.RESET_ALL}")
            return
        state.inventory.remove_item("protectron_spare_parts")
        for objective in quest.objectives:
            objective.complete()
        quest.complete()
        state.player.add_experience(quest.rewards.get("experience", 0))
        state.inventory.add_caps(quest.rewards.get("caps", 0))
        print(f"\n{Fore.YELLOW}[Quest Completed: {quest.title}]{Style.RESET_ALL}")

    def _action_start_currywurst_quest(self, state):
        if "lost_currywurst" in state.quests:
            state.quests["lost_currywurst"].start()
            print(
                f"\n{Fore.YELLOW}[Quest Started: The Lost Currywurst]{Style.RESET_ALL}"
            )

    def _action_complete_currywurst_quest(self, state):
        if self._turn_in_quest_item(state, "lost_currywurst", "currywurst"):
            state.player.add_experience(300)
            caps = create_item("caps", 100)
            if caps:
                state.inventory.add_item(caps)
            print(
                f"\n{Fore.YELLOW}[Quest Completed: The Lost Currywurst]{Style.RESET_ALL}"
            )
            print(f"{Fore.GREEN}Received: 300 XP, 100 Caps{Style.RESET_ALL}")

    def _action_start_green_thumb(self, state):
        if "green_thumb" in state.quests:
            state.quests["green_thumb"].start()
            print(f"\n{Fore.YELLOW}[Quest Started: Green Thumb]{Style.RESET_ALL}")

    def _action_trigger_green_thumb_stage_2(self, state):
        if "green_thumb" in state.quests:
            print(f"\n{Fore.YELLOW}[Quest Updated: Green Thumb]{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Objective Updated: Purify the seeds and clear the pests in the North Hangar.{Style.RESET_ALL}")

    def _action_complete_green_thumb(self, state):
        if self._turn_in_quest_item(state, "green_thumb", "purified_seeds"):
            state.player.add_experience(500)
            
            fruit = create_item("mutated_fruit", 5)
            kit = create_item("soil_analysis_kit")
            caps = create_item("caps", 100)
            
            if fruit: state.inventory.add_item(fruit)
            if kit: state.inventory.add_item(kit)
            if caps: state.inventory.add_item(caps)
            
            print(f"\n{Fore.YELLOW}[Quest Completed: Green Thumb]{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Received: 500 XP, 100 Caps, 5 Mutated Fruit, Soil Analysis Kit{Style.RESET_ALL}")

    def _action_start_iron_will(self, state):
        if "iron_will" in state.quests:
            state.quests["iron_will"].start()
            print(f"\n{Fore.YELLOW}[Quest Started: Iron Will]{Style.RESET_ALL}")

    def _action_complete_iron_will(self, state):
        if self._turn_in_quest_item(state, "iron_will", "iron_ring_data"):
            state.player.add_experience(200)
            
            pistol = create_item("laser_pistol")
            cells = create_item("fusion_cell", 20)
            
            if pistol:
                state.inventory.add_item(pistol)
            if cells:
                state.inventory.add_item(cells)
                
            state.modify_faction_reputation("Iron Ring", 25)
            
            print(f"\n{Fore.YELLOW}[Quest Completed: Iron Will]{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Received: 200 XP, Laser Pistol, Fusion Cells{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Faction Reputation (Iron Ring) increased!{Style.RESET_ALL}")

    def _action_start_bureaucrats_nightmare(self, state):
        if "bureaucrats_nightmare" in state.quests:
            state.quests["bureaucrats_nightmare"].start()
            print(f"\n{Fore.YELLOW}[Quest Started: The Bureaucrat's Nightmare]{Style.RESET_ALL}")

    def _action_complete_bureaucrats_nightmare(self, state):
        if self._turn_in_quest_item(
            state, "bureaucrats_nightmare", "anmeldung_form"
        ):
            state.player.add_experience(250)
            
            caps = create_item("caps", 75)
            stimpak = create_item("stimpak", 1)
            
            if caps: state.inventory.add_item(caps)
            if stimpak: state.inventory.add_item(stimpak)
            
            print(f"\n{Fore.YELLOW}[Quest Completed: The Bureaucrat's Nightmare]{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Received: 250 XP, 75 Caps, Stimpak{Style.RESET_ALL}")

    def _action_buy_currywurst(self, state):
        cost = 15
        food = create_item("doner_human")
        if not food:
            print(f"\n{Fore.RED}The Currywurst is unavailable.{Style.RESET_ALL}")
        elif not state.inventory.can_add_item(food):
            print(f"\n{Fore.RED}You don't have enough carry capacity.{Style.RESET_ALL}")
        elif state.inventory.remove_caps(cost):
            food.name = "Hot Currywurst"
            state.inventory.add_item(food)
            print(f"\n{Fore.GREEN}You bought a Currywurst for {cost} caps.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}You don't have enough caps!{Style.RESET_ALL}")

    def _action_buy_doner(self, state):
        cost = 5
        food = create_item("doner_human")
        if not food:
            print(f"\n{Fore.RED}The Döner is unavailable.{Style.RESET_ALL}")
        elif not state.inventory.can_add_item(food):
            print(f"\n{Fore.RED}You don't have enough carry capacity.{Style.RESET_ALL}")
        elif state.inventory.remove_caps(cost):
            state.inventory.add_item(food)
            print(f"\n{Fore.GREEN}You bought a Döner (Special Meat) for {cost} caps.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}You don't have enough caps!{Style.RESET_ALL}")

    def _action_buy_doner_kebab(self, state):
        cost = 10
        food = create_item("doner_human")
        if not food:
            print(f"\n{Fore.RED}The Döner is unavailable.{Style.RESET_ALL}")
        elif not state.inventory.can_add_item(food):
            print(f"\n{Fore.RED}You don't have enough carry capacity.{Style.RESET_ALL}")
        elif state.inventory.remove_caps(cost):
            state.inventory.add_item(food)
            print(f"\n{Fore.GREEN}You bought a Döner for {cost} caps.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}You don't have enough caps!{Style.RESET_ALL}")

    def _initialize_dialogue(self):
        """Initialize dialogue trees from JSON"""
        data_path = os.path.join(os.path.dirname(__file__), "data", "dialogues.json")
        if not os.path.exists(data_path):
            print(f"Warning: Dialogue file not found at {data_path}")
            return

        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for tree_id, tree_data in data.items():
                tree = DialogueTree(tree_id, tree_data["npc_name"])

                for node_id, node_data in tree_data["nodes"].items():
                    node = DialogueNode(
                        node_id,
                        node_data.get("speaker", tree_data["npc_name"]),
                        node_data["text"],
                    )

                    for opt_data in node_data.get("options", []):
                        condition = None
                        if "condition" in opt_data:
                            cond_data = opt_data["condition"]
                            cond_params = cond_data.get("params", {})
                            if isinstance(cond_params, list):
                                # Special case for 'and' / 'or' conditions
                                condition = DialogueCondition(
                                    cond_data["type"], items=cond_params
                                )
                            else:
                                condition = DialogueCondition(
                                    cond_data["type"], **cond_params
                                )

                        action = None
                        if "action" in opt_data:
                            action_name = opt_data["action"]
                            action = self.action_handlers.get(action_name)
                            if action is None:
                                action = self._unavailable_action(action_name)

                        option = DialogueOption(
                            opt_data["text"],
                            opt_data.get("next_node"),
                            condition,
                            action,
                        )
                        option.end_dialogue = opt_data.get("end_dialogue", False)
                        node.add_option(option)

                    tree.add_node(node)

                # Set start node
                if "start_node" in tree_data:
                    tree.start_node = tree_data["start_node"]

                self.add_dialogue_tree(tree)

        except Exception as e:
            print(f"Error loading dialogues: {e}")
            import traceback

            traceback.print_exc()

    def get_dialogue_tree(self, npc_id: str) -> Optional[DialogueTree]:
        """Get dialogue tree for an NPC"""
        return self.dialogue_trees.get(npc_id)

    def add_dialogue_tree(self, tree: DialogueTree):
        """Add a dialogue tree"""
        self.dialogue_trees[tree.npc_id] = tree

    @staticmethod
    def _unavailable_action(action_name):
        def report_missing_content(_state):
            print(
                f"{Fore.RED}This dialogue action is unavailable: "
                f"'{action_name}' has no configured quest content.{Style.RESET_ALL}"
            )

        return report_missing_content

    def process_option(self, option: DialogueOption, engine: Any):
        """Process a selected dialogue option and update game state"""
        from fallout_berlin.engine_states import ExplorationState, DialogueState

        # Check for quest objectives (Hardcoded logic from old engine_states)
        if (
            option.next_node == "factions"
            and "first_steps" in engine.state.quests
        ):
            if engine.quest_manager.complete_objective(
                "first_steps", "learn_factions"
            ):
                print(f"{Fore.YELLOW}[Quest Updated: First Steps]{Style.RESET_ALL}")

        # Execute action if any
        if option.action and option.action(engine.state) == "open_shop":
            from fallout_berlin.barter_state import BarterState
            engine.change_state(
                BarterState(engine, engine.current_dialogue_tree.npc_id)
            )
            return

        # Move to next node or end dialogue
        if option.next_node:
            next_node = engine.current_dialogue_tree.get_node(option.next_node)
            engine.current_dialogue_node = next_node
            
            # Update the state with the new node
            if isinstance(engine.current_state, DialogueState):
                engine.current_state.current_node = next_node.node_id if next_node else ""
        else:
            engine.change_state(ExplorationState(engine))
            print("\n[End of conversation]")
