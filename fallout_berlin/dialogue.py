"""
Dialogue System
Handles NPC dialogue trees and conversation management
"""

from typing import Dict, List, Optional, Callable, Any
from enum import Enum


class DialogueCondition:
    """Represents a condition that must be met for dialogue option"""
    
    def __init__(self, condition_type: str, **kwargs):
        self.condition_type = condition_type
        self.params = kwargs
    
    def check(self, game_state) -> bool:
        """Check if condition is met"""
        if self.condition_type == 'skill':
            skill = self.params.get('skill')
            min_value = self.params.get('min', 0)
            if game_state.player:
                return game_state.player.get_skill(skill) >= min_value
        elif self.condition_type == 'faction_rep':
            faction = self.params.get('faction')
            min_rep = self.params.get('min', 0)
            return game_state.get_faction_reputation(faction) >= min_rep
        elif self.condition_type == 'has_item':
            item_name = self.params.get('item')
            quantity = self.params.get('quantity', 1)
            if game_state.inventory:
                return game_state.inventory.has_item(item_name, quantity)
        elif self.condition_type == 'world_flag':
            flag = self.params.get('flag')
            value = self.params.get('value', True)
            return game_state.get_world_flag(flag) == value
        elif self.condition_type == 'quest_state':
            quest_id = self.params.get('quest')
            state = self.params.get('state')
            if quest_id in game_state.quests:
                return game_state.quests[quest_id].state == state
        elif self.condition_type == 'always':
            return True
        elif self.condition_type == 'never':
            return False
        
        return False


class DialogueOption:
    """A single dialogue option/response"""
    
    def __init__(self, text: str, next_node: Optional[str] = None,
                 condition: Optional[DialogueCondition] = None,
                 action: Optional[Callable] = None):
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
            'node_id': self.node_id,
            'speaker': self.speaker,
            'text': self.text,
            'options': [
                {
                    'text': opt.text,
                    'next_node': opt.next_node,
                    'condition': {
                        'type': opt.condition.condition_type,
                        'params': opt.condition.params
                    } if opt.condition else None
                }
                for opt in self.options
            ],
            'end_dialogue': self.end_dialogue
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
        self._initialize_dialogue()
    
    def _initialize_dialogue(self):
        """Initialize some example dialogue trees"""
        # Example: Trader at Checkpoint Charlie
        trader_tree = DialogueTree("trader_charlie", "Hans the Trader")
        
        # Start node
        start = DialogueNode("start", "Hans the Trader", 
            "Na, wat willste? This is Checkpoint Charlie Market. Don't just stand there like a tourist, buy somethin' or move on.")
        start.add_option(DialogueOption("What do you have for sale?", "shop"))
        start.add_option(DialogueOption("Tell me about this place.", "about_market"))
        start.add_option(DialogueOption("I'm looking for information.", "info"))
        start.add_option(DialogueOption("Tschüss. (Goodbye)", None))
        start.options[-1].end_dialogue = True
        trader_tree.add_node(start)
        
        # Shop node
        shop = DialogueNode("shop", "Hans the Trader",
            "I've got the usual junk. Stimpaks, some rusty ammo, and real Icy Currywurst if you've got the caps.")
        shop.add_option(DialogueOption("Show me your wares.", None))
        shop.add_option(DialogueOption("How much for a Currywurst?", "currywurst_price"))
        shop.add_option(DialogueOption("Never mind.", "start"))
        shop.options[0].end_dialogue = True  # Will trigger shop menu
        trader_tree.add_node(shop)
        
        # About market
        about = DialogueNode("about_market", "Hans the Trader",
            "Checkpoint Charlie is where the magic happens. We're between the Iron Curtain in the East and the Free Berliners in the West. "
            "The Broker keeps the peace. If you pull a gun, you're dead before you can say 'Currywurst'.")
        about.add_option(DialogueOption("Who is the Broker?", "broker"))
        about.add_option(DialogueOption("Interesting. Thanks.", "start"))
        trader_tree.add_node(about)
        
        # Broker info
        broker = DialogueNode("broker", "Hans the Trader",
            "The Broker? Some say he was a Stasi ghost, others say he's just a synth from the old world. "
            "All I know is his robots don't miss. Keep your nose clean and you'll be fine.")
        broker.add_option(DialogueOption("I see. Thanks.", "start"))
        trader_tree.add_node(broker)
        
        # Info node
        info = DialogueNode("info", "Hans the Trader",
            "Information ain't free, kid. But since I like your face... mostly. What's on your mind?")
        info.add_option(DialogueOption("Tell me about the factions.", "factions"))
        info.add_option(DialogueOption("Where can I find supplies?", "supplies"))
        info.add_option(DialogueOption("Never mind.", "start"))
        trader_tree.add_node(info)
        
        # Factions info
        factions = DialogueNode("factions", "Hans the Trader",
            "The Iron Curtain holds the Reichstag and most of the East. They're all about 'order' and 'discipline'. "
            "The Free Berliners in the West are just a bunch of chaotic punks, but they have the best Club-Mate. "
            "And don't even get me started on the Tunnel Rats in the U-Bahn.")
        factions.add_option(DialogueOption("Thanks for the info.", "start"))
        trader_tree.add_node(factions)
        
        # Supplies info
        supplies = DialogueNode("supplies", "Hans the Trader",
            "You want the good stuff? Go to Kotti, if you have the balls. Or try the Kreuzberg Bazaar. "
            "Just watch out for the rad-rabbits in Görli. They'll take a finger off if you're slow.")
        supplies.add_option(DialogueOption("Thanks.", "start"))
        trader_tree.add_node(supplies)
        
        # Currywurst price
        currywurst_price = DialogueNode("currywurst_price", "Hans the Trader",
            "A Currywurst will set you back 15 caps. It's the real deal, not that pre-war canned garbage.")
        currywurst_price.add_option(DialogueOption("I'll take one.", None))
        currywurst_price.add_option(DialogueOption("Too expensive.", "shop"))
        currywurst_price.options[0].end_dialogue = True  # Will trigger purchase
        trader_tree.add_node(currywurst_price)
        
        self.dialogue_trees["trader_charlie"] = trader_tree

    
    def get_dialogue_tree(self, npc_id: str) -> Optional[DialogueTree]:
        """Get dialogue tree for an NPC"""
        return self.dialogue_trees.get(npc_id)
    
    def add_dialogue_tree(self, tree: DialogueTree):
        """Add a dialogue tree"""
        self.dialogue_trees[tree.npc_id] = tree
