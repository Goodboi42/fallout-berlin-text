"""
NPC System
Base class for non-player characters.
"""

from typing import Dict, Any, Optional


class NPC:
    """Base class for all NPCs"""

    def __init__(self, name: str, description: str, dialogue_id: Optional[str] = None):
        self.name = name
        self.description = description
        self.dialogue_id = dialogue_id
        self.is_alive = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert NPC to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "dialogue_id": self.dialogue_id,
            "is_alive": self.is_alive,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPC":
        """Create NPC from dictionary"""
        npc = cls(data["name"], data["description"], data.get("dialogue_id"))
        npc.is_alive = data.get("is_alive", True)
        return npc
