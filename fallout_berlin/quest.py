"""
Quest System
Handles quests, objectives, and quest tracking
"""

import json
import os
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

class QuestState(Enum):

    """Quest states"""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class QuestObjective:
    """A single objective within a quest"""

    def __init__(self, description: str, objective_id: str = None):
        self.objective_id = objective_id or description.lower().replace(" ", "_")
        self.description = description
        self.completed = False
        self.optional = False
        self.trigger_conditions: List[Dict[str, Any]] = [] # Conditions to automatically complete this objective

    def complete(self):
        """Mark objective as completed"""
        self.completed = True

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "objective_id": self.objective_id,
            "description": self.description,
            "completed": self.completed,
            "optional": self.optional,
            "trigger_conditions": self.trigger_conditions
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "QuestObjective":
        """Create from dictionary"""
        obj = cls(data["description"], data.get("objective_id"))
        obj.completed = data.get("completed", False)
        obj.optional = data.get("optional", False)
        obj.trigger_conditions = data.get("trigger_conditions", [])
        return obj


class Quest:
    """Represents a quest"""

    def __init__(self, quest_id: str, title: str, description: str):
        self.quest_id = quest_id
        self.title = title
        self.description = description
        self.state = QuestState.NOT_STARTED
        self.objectives: List[QuestObjective] = []
        self.rewards = {
            "experience": 0,
            "caps": 0,
            "items": [],
            "faction_rep": {}  # faction -> amount
        }
        self.giver: Optional[str] = None  # NPC ID who gave the quest
        self.notes: List[str] = []  # Additional quest notes
        self.start_conditions: List[Dict[str, Any]] = [] # Conditions to automatically start this quest

    def add_objective(self, objective: QuestObjective):
        """Add an objective to the quest"""
        self.objectives.append(objective)

    def start(self):
        """Start the quest"""
        self.state = QuestState.ACTIVE

    def complete(self):
        """Complete the quest"""
        # Check if all required objectives are complete
        required_objectives = [obj for obj in self.objectives if not obj.optional]
        if all(obj.completed for obj in required_objectives):
            self.state = QuestState.COMPLETED
            return True
        return False

    def fail(self):
        """Fail the quest"""
        self.state = QuestState.FAILED

    def get_progress(self) -> str:
        """Get quest progress as string"""
        if self.state == QuestState.NOT_STARTED:
            return "Not started"
        elif self.state == QuestState.COMPLETED:
            return "Completed"
        elif self.state == QuestState.FAILED:
            return "Failed"
        else:
            completed = sum(1 for obj in self.objectives if obj.completed)
            total = len(self.objectives)
            return f"{completed}/{total} objectives completed"

    def get_objectives_display(self) -> str:
        """Get formatted objectives display"""
        lines = [f"Objectives:"]
        for obj in self.objectives:
            status = "[x]" if obj.completed else "[ ]"
            optional = " (Optional)" if obj.optional else ""
            lines.append(f"  {status} {obj.description}{optional}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Convert quest to dictionary"""
        return {
            "quest_id": self.quest_id,
            "title": self.title,
            "description": self.description,
            "state": self.state.value,
            "objectives": [obj.to_dict() for obj in self.objectives],
            "rewards": self.rewards,
            "giver": self.giver,
            "notes": self.notes,
            "start_conditions": self.start_conditions
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Quest":
        """Create quest from dictionary"""
        quest = cls(
            data["quest_id"],
            data["title"],
            data["description"]
        )
        quest.state = QuestState(data.get("state", "not_started"))
        quest.objectives = [QuestObjective.from_dict(obj_data)
                          for obj_data in data.get("objectives", [])]
        quest.rewards = data.get("rewards", {})
        quest.giver = data.get("giver")
        quest.notes = data.get("notes", [])
        quest.start_conditions = data.get("start_conditions", [])
        return quest


class QuestManager:
    """Manages all quests"""

    def __init__(self):
        self.quests: Dict[str, Quest] = {}
        self._initialize_quests()

    def _initialize_quests(self):
        """Initialize quests from JSON data"""
        data_path = os.path.join(os.path.dirname(__file__), "data", "quests.json")
        if not os.path.exists(data_path):
            # Fallback to minimal hardcoded if file missing
            first_steps = Quest("first_steps", "First Steps", "Learn to survive.")
            first_steps.add_objective(QuestObjective("Explore Checkpoint Charlie"))
            self.quests["first_steps"] = first_steps
            return

        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for q_id, q_data in data.items():
                    quest = Quest(q_id, q_data["title"], q_data["description"])
                    for obj_data in q_data.get("objectives", []):
                        obj = QuestObjective(obj_data["description"], obj_data.get("id"))
                        obj.optional = obj_data.get("optional", False)
                        obj.trigger_conditions = obj_data.get("trigger_conditions", []) # Load objective conditions
                        quest.add_objective(obj)
                    quest.rewards = q_data.get("rewards", {})
                    quest.start_conditions = q_data.get("start_conditions", []) # Load quest start conditions
                    self.add_quest(quest)
        except Exception as e:
            print(f"Error loading quests: {e}")

    def reset(self):
        """Resets all quests to their initial state."""
        self.quests = {}
        self._initialize_quests()

    def evaluate_condition(self, condition: Dict[str, Any], game_state: Any) -> bool:
        """Evaluates a single condition dictionary against the current game state."""
        condition_type = condition.get("type")
        params = condition.get("params", {})

        if condition_type == "has_item":
            item_id = params.get("item")
            min_quantity = params.get("min_quantity", 1)
            return game_state.inventory.has_item(item_id, min_quantity)
        elif condition_type == "at_location":
            location_id = params.get("location")
            return game_state.current_location == location_id
        elif condition_type == "world_flag_set":
            flag = params.get("flag")
            expected_value = params.get("value", True)
            return game_state.get_world_flag(flag) == expected_value
        elif condition_type == "talked_to_npc":
            npc_id = params.get("npc")
            # This would require tracking NPC dialogue states in game_state,
            # for now, we can assume a flag is set when an NPC has been talked to.
            return game_state.check_world_flag(f"talked_to_{npc_id}")
        elif condition_type == "killed_creature":
            creature_id = params.get("creature")
            min_count = params.get("min_count", 1)
            killed_count = sum(
                count
                for killed_id, count in game_state.killed_creatures.items()
                if killed_id == creature_id or killed_id.startswith(f"{creature_id}_")
            )
            return killed_count >= min_count
        elif condition_type == "reputation_level":
            faction = params.get("faction")
            min_rep = params.get("min_reputation", 0)
            return game_state.get_faction_reputation(faction) >= min_rep
        elif condition_type == "quest_state":
            quest_id = params.get("quest")
            state = params.get("state")
            quest = self.get_quest(quest_id)
            return quest and quest.state.value == state
        elif condition_type == "enemy_present_in_location":
            enemy_name = params.get("enemy")
            location_id = params.get("location")
            location = game_state.location_manager.get_location(location_id)
            return location and location.find_enemy(enemy_name)
        elif condition_type == "and":
            return all(self.evaluate_condition(sub_cond, game_state) for sub_cond in params.get("conditions", []))
        elif condition_type == "or":
            return any(self.evaluate_condition(sub_cond, game_state) for sub_cond in params.get("conditions", []))
        elif condition_type == "not":
            return not self.evaluate_condition(params.get("condition", {}), game_state)
        # Add more condition types as needed
        return False

    def check_quest_triggers(self, game_state: Any):
        """
        Checks for quest triggers (start conditions, objective completions)
        based on the current game state.
        """
        for quest_id, quest in self.quests.items():
            if quest.state == QuestState.NOT_STARTED:
                if self.evaluate_condition({"type": "and", "params": {"conditions": quest.start_conditions}}, game_state):
                    self.start_quest(quest_id)
            elif quest.state == QuestState.ACTIVE:
                for objective in quest.objectives:
                    if not objective.completed and objective.trigger_conditions:
                        if self.evaluate_condition({"type": "and", "params": {"conditions": objective.trigger_conditions}}, game_state):
                            self.complete_objective(quest_id, objective.objective_id)

    def is_enemy_critical(self, enemy_name: str, location_id: str) -> bool:
        """
        Checks if an enemy is essential for narrative progression (e.g., quest giver, main antagonist).
        This directly affects game mechanics like stealth to reinforce story flow.
        """
        critical_enemies = {
            "charlottenburg_palace": ["stasi_commander", "von_stahl_proxy"],
            # Add other key location enemies from Narrative Audit (Mother Renate fight, etc.)
        }

        key_enemies = critical_enemies.get(location_id, [])

        # Case-insensitive match
        return any(enemy_name.lower() in key.lower() for key in key_enemies)

    def on_location_enter(self, event):
        """Handle location entry events for quest updates.
        game_state is passed via event.data['game_state'] to keep the
        EventManager dispatch signature (single-arg callbacks) correct.
        """
        game_state = event.data.get("game_state") if event.data else None
        if game_state:
            self.check_quest_triggers(game_state)


    def add_quest(self, quest: Quest):
        """Add a quest"""
        self.quests[quest.quest_id] = quest

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get a quest by ID"""
        return self.quests.get(quest_id)

    def get_active_quests(self) -> List[Quest]:
        """Get all active quests"""
        return [q for q in self.quests.values() if q.state == QuestState.ACTIVE]

    def get_completed_quests(self) -> List[Quest]:
        """Get all completed quests"""
        return [q for q in self.quests.values() if q.state == QuestState.COMPLETED]

    def start_quest(self, quest_id: str) -> bool:
        """Start a quest"""
        quest = self.get_quest(quest_id)
        if quest and quest.state == QuestState.NOT_STARTED:
            quest.start()
            # Show quest discovery animation
            from fallout_berlin.art_master import ArtEffects
            ArtEffects.quest_discovery_splash(quest.title).play()
            return True
        return False

    def complete_objective(self, quest_id: str, objective_id: str) -> bool:
        """Complete a quest objective"""
        quest = self.get_quest(quest_id)
        if not quest or quest.state != QuestState.ACTIVE:
            return False

        for obj in quest.objectives:
            if obj.objective_id == objective_id:
                obj.complete()
                # Check if quest is complete
                if quest.complete():
                    from fallout_berlin.art_master import ArtEffects
                    # Custom completion animations
                    if quest_id == "lost_currywurst":
                        ArtEffects.narrative_moment_splash("THE CURRYWURST SECURED", "Hans will be pleased. The spice must flow.").play()
                    elif quest_id == "the_theft_of_berlin":
                        ArtEffects.narrative_moment_splash("MUSEUM HEIST COMPLETE", "The Nefertiti Bust is yours. A masterpiece reclaimed.").play()
                    else:
                        print(ArtEffects.quest_complete())
                return True
        return False

    def get_quests_display(self, game_state) -> str:
        """Get formatted display of all quests"""
        active = self.get_active_quests()
        completed = self.get_completed_quests()

        lines = ["=== QUESTS ==="]

        if active:
            lines.append("\nActive Quests:")
            for quest in active:
                lines.append(f"\n{quest.title}")
                lines.append(f"  {quest.description}")
                lines.append(f"  {quest.get_progress()}")
                lines.append(quest.get_objectives_display())
        else:
            lines.append("\nNo active quests.")

        if completed:
            lines.append("\n\nCompleted Quests:")
            for quest in completed:
                lines.append(f"  [x] {quest.title}")

        return "\n".join(lines)
