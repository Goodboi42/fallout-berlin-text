"""
Input Parser
Handles parsing of user input into structured commands.
Allows for natural language processing and context-aware parsing.
"""

from typing import List, Dict, Tuple, Optional
import difflib
from fallout_berlin.commands import (
    Command,
    MoveCommand,
    LookCommand,
    TakeCommand,
    UseCommand,
    TalkCommand,
    InventoryCommand,
    StatsCommand,
    QuestsCommand,
    HelpCommand,
    EquipCommand,
    CraftCommand,
    SneakCommand,
    CampCommand,
    RadioCommand,
    CompanionCommand,
    StealCommand,
    ScanCommand,
    MapCommand,
    SaveCommand,
    LoadCommand,
    QuitCommand,
    AttackCommand,
    CombatPlaceholderCommand,
    CutsceneCommand,
    SettingsCommand,
    PauseCommand,
    LootCommand,
)
from fallout_berlin.commands_extra import RecycleCommand


class InputParser:
    """Parses raw string input into Commands"""

    def __init__(self):
        self.verbs = {
            # Movement
            "go": ["move", "travel", "walk", "run"],
            "north": ["n"],
            "south": ["s"],
            "east": ["e"],
            "west": ["w"],
            "up": ["u"],
            "down": ["d"],
            # Interaction
            "look": ["examine", "l", "x", "inspect"],
            "take": ["get", "pickup", "grab"],
            "loot": [],
            "drop": ["discard", "remove"],
            "use": ["consume", "eat", "drink"],
            "equip": ["wear", "wield"],
            "unequip": ["remove"],
            "craft": ["make", "create", "build", "c"],
            "talk": ["speak", "chat", "say", "t"],
            "recycle": ["pfand", "return", "deposit"],
            # Combat
            "attack": ["fight", "hit", "kill", "shoot", "stab"],
            "flee": ["run", "escape"],
            "heal": ["medic"],
            "vats": ["target", "aim"],  # New mechanic
            # Stealth
            "sneak": ["stealth", "hide", "crouch"],
            "steal": ["pickpocket", "rob"],
            # Info
            "inventory": ["inv", "i", "items", "bag"],
            "stats": ["stat", "char", "character", "skills"],
            "quests": ["quest", "q", "journal", "log"],
            "scan": ["search", "scout", "detect"],
            "help": ["h", "?", "commands"],
            "map": ["m"],  # New mechanic
            # System
            "save": [],
            "load": [],
            "quit": ["exit", "leave"],
            "camp": ["rest", "sleep"],
            "radio": [],
            "companion": ["follower", "buddy", "pet"],
            "cutscene": [],
            "settings": ["options", "config"],
            "pause": ["menu", "esc"],
        }

        # Flatten verb synonyms for reverse lookup
        self.verb_map = {}
        for main_verb, synonyms in self.verbs.items():
            self.verb_map[main_verb] = main_verb
            for syn in synonyms:
                self.verb_map[syn] = main_verb

    def parse(self, input_str: str) -> Optional[Command]:
        """Parse a raw input string into a Command object"""
        if not input_str or not input_str.strip():
            return None

        parts = input_str.strip().lower().split()
        if not parts:
            return None

        raw_verb = parts[0]
        args = parts[1:]

        # Resolve verb
        verb = self.verb_map.get(raw_verb)
        if not verb:
            # Try fuzzy matching if no exact match
            all_verbs = list(self.verb_map.keys())
            matches = difflib.get_close_matches(raw_verb, all_verbs, n=1, cutoff=0.8)
            if matches:
                verb = self.verb_map[matches[0]]
            else:
                return None

        # NLP Processing: Handle prepositions (on, with, at, to)
        target = None
        indirect = None

        if args:
            prepositions = ["on", "with", "at", "to", "in"]
            split_index = -1

            for i, word in enumerate(args):
                if word in prepositions:
                    split_index = i
                    break

            if split_index != -1:
                target = " ".join(args[:split_index])
                indirect = " ".join(args[split_index + 1 :])
            else:
                target = " ".join(args)

        # Command Mapping
        if verb == "go":
            return MoveCommand(target if target else "north")  # Default fallback
        elif verb in ["north", "south", "east", "west", "up", "down"]:
            return MoveCommand(verb)
        elif verb == "look":
            return LookCommand(target)
        elif verb == "take":
            return TakeCommand(target)
        elif verb == "use":
            return UseCommand(target, indirect)
        elif verb == "talk":
            return TalkCommand(target)
        elif verb == "inventory":
            return InventoryCommand()
        elif verb == "stats":
            return StatsCommand()
        elif verb == "quests":
            return QuestsCommand()
        elif verb == "help":
            return HelpCommand()
        elif verb == "equip":
            return EquipCommand(target)
        elif verb == "craft":
            return CraftCommand(target)
        elif verb == "sneak":
            return SneakCommand()
        elif verb == "camp":
            return CampCommand()
        elif verb == "radio":
            return RadioCommand()
        elif verb == "companion":
            return CompanionCommand(args)
        elif verb == "steal":
            return StealCommand(args)
        elif verb == "scan":
            return ScanCommand()
        elif verb == "map":
            return MapCommand()
        elif verb == "save":
            return SaveCommand()
        elif verb == "load":
            return LoadCommand()
        elif verb == "quit":
            return QuitCommand()
        elif verb == "cutscene":
            return CutsceneCommand(target)
        elif verb == "settings":
            return SettingsCommand()
        elif verb == "pause":
            return PauseCommand()

        # Combat placeholder
        elif verb == "attack":
            return AttackCommand(target)
        elif verb in ["heal", "flee", "vats"]:
            return CombatPlaceholderCommand()

        return None

    def get_suggestions(self, input_str: str) -> List[str]:
        """Get command suggestions for invalid input"""
        if not input_str:
            return []
        parts = input_str.split()
        return difflib.get_close_matches(parts[0], list(self.verb_map.keys()), n=3)
