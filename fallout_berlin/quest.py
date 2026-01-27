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
        self.objective_id = objective_id or description.lower().replace(' ', '_')
        self.description = description
        self.completed = False
        self.optional = False
    
    def complete(self):
        """Mark objective as completed"""
        self.completed = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'objective_id': self.objective_id,
            'description': self.description,
            'completed': self.completed,
            'optional': self.optional
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QuestObjective':
        """Create from dictionary"""
        obj = cls(data['description'], data.get('objective_id'))
        obj.completed = data.get('completed', False)
        obj.optional = data.get('optional', False)
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
            'experience': 0,
            'caps': 0,
            'items': [],
            'faction_rep': {}  # faction -> amount
        }
        self.giver: Optional[str] = None  # NPC ID who gave the quest
        self.notes: List[str] = []  # Additional quest notes
    
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
            status = "✓" if obj.completed else "○"
            optional = " (Optional)" if obj.optional else ""
            lines.append(f"  {status} {obj.description}{optional}")
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        """Convert quest to dictionary"""
        return {
            'quest_id': self.quest_id,
            'title': self.title,
            'description': self.description,
            'state': self.state.value,
            'objectives': [obj.to_dict() for obj in self.objectives],
            'rewards': self.rewards,
            'giver': self.giver,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Quest':
        """Create quest from dictionary"""
        quest = cls(
            data['quest_id'],
            data['title'],
            data['description']
        )
        quest.state = QuestState(data.get('state', 'not_started'))
        quest.objectives = [QuestObjective.from_dict(obj_data) 
                          for obj_data in data.get('objectives', [])]
        quest.rewards = data.get('rewards', {})
        quest.giver = data.get('giver')
        quest.notes = data.get('notes', [])
        return quest


class QuestManager:
    """Manages all quests"""
    
    def __init__(self):
        self.quests: Dict[str, Quest] = {}
        self._initialize_quests()
    
    def _initialize_quests(self):
        """Initialize quests from JSON data"""
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'quests.json')
        if not os.path.exists(data_path):
            # Fallback to minimal hardcoded if file missing
            first_steps = Quest("first_steps", "First Steps", "Learn to survive.")
            first_steps.add_objective(QuestObjective("Explore Checkpoint Charlie"))
            self.quests["first_steps"] = first_steps
            return

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for q_id, q_data in data.items():
                    quest = Quest(q_id, q_data['title'], q_data['description'])
                    for obj_data in q_data.get('objectives', []):
                        obj = QuestObjective(obj_data['description'], obj_data.get('id'))
                        obj.optional = obj_data.get('optional', False)
                        quest.add_objective(obj)
                    quest.rewards = q_data.get('rewards', {})
                    self.add_quest(quest)
        except Exception as e:
            print(f"Error loading quests: {e}")

    
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
                quest.complete()
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
                lines.append(f"  ✓ {quest.title}")
        
        return "\n".join(lines)
