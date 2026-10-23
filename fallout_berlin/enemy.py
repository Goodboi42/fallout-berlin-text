"""
Enemy System
Handles enemy creation, stats, and behavior
"""

import json
import os
import random
from typing import Dict, List, Optional, Any, TYPE_CHECKING, Tuple
from fallout_berlin.item import Item, create_item

if TYPE_CHECKING:
    from fallout_berlin.player import Player # For type hinting in methods


class Enemy:
    """Represents an enemy in the game"""
    
    def __init__(self, name: str, description: str, level: int, hp: int,
                 damage: int, xp_reward: int, loot_table: List[str] = None,
                 damage_resistance: int = 0, ai_profile: str = "Berserker",
                                 agility: int = 5, perception: int = 5, weapon_id: str = ""):
        self.name = name
        self.description = description
        self.level = level
        self.max_hp = hp
        self.hp = hp
        self.base_damage = damage # Renamed to base_damage
        self.damage_resistance = damage_resistance
        self.xp_reward = xp_reward
        self.loot_table = loot_table or []
        # self.is_alive = True  <-- Removed, now a property
        
        # Weapon
        self.weapon_id = weapon_id
        self.weapon = create_item(weapon_id) if weapon_id else None

        # AP System
        self.max_ap = 5 + agility # Based on player AP calc: 5 + Agility
        self.current_ap = self.max_ap
        self.has_cover = False # New: Enemy can take cover
        self.ai_profile = ai_profile # Berserker, Tactician, Coward
        self.active_effects: List[str] = [] # New: Active status effects

        # Add AI-relevant stats if not already present in base class
        self.agility = agility
        self.perception = perception

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int):
        """Take damage from an attack, factoring in DR"""
        actual_damage = max(1, amount - self.damage_resistance)
        self.hp -= actual_damage
        if self.hp <= 0:
            self.hp = 0

    def get_attack_damage(self) -> int:
        """Calculate attack damage, potentially modified by effects"""
        # Simple damage variation +/- 20%
        variance = int(self.base_damage * 0.2)
        damage = self.base_damage + random.randint(-variance, variance)

        # Apply any damage-modifying effects
        if "Weakened" in self.active_effects: # Example effect
            damage = int(damage * 0.75)

        return damage

    def get_damage_resistance(self) -> int:
        """Calculate effective damage resistance, considering cover and effects"""
        effective_dr = self.damage_resistance
        if self.has_cover:
            effective_dr += 15 # Cover provides a bonus to DR

        # Apply any DR-modifying effects
        if "Exposed" in self.active_effects: # Example effect
            effective_dr = max(0, effective_dr - 10)
            
        return effective_dr
    
    def get_hit_chance(self, player: "Player") -> int:
        """Calculate enemy's hit chance against the player"""
        # Simplified for enemies, could be expanded later
        base_hit_chance = 70 + (self.perception * 2)
        
        if "Crippled Arm" in self.active_effects:
            base_hit_chance -= 20

        # Reduce hit chance if player has cover (already handled in CombatManager.player_attack)
        # For now, just a direct return
        return max(5, min(95, base_hit_chance))

    def regenerate_ap(self):
        """Regenerate AP at end of turn"""
        # Formula: 2 + (Agility / 2)
        regen = 2 + (self.agility // 2)

        # Apply Stunned penalty (AP Regen reduced by 100%)
        if "Stunned" in self.active_effects:
            regen = 0
        # Apply Crippled Leg penalty (AP Regen reduced by 50%)
        elif "Crippled Leg" in self.active_effects:
            regen //= 2

        self.current_ap = min(self.max_ap, self.current_ap + regen)

    def spend_ap(self, amount: int) -> bool:
        """Spend Action Points."""
        if self.current_ap >= amount:
            self.current_ap -= amount
            return True
        return False

    def apply_status_effect(self, name: str):
        """Apply a status effect to the enemy"""
        if name not in self.active_effects:
            self.active_effects.append(name)

    def remove_status_effect(self, name: str):
        """Remove a status effect from the enemy"""
        if name in self.active_effects:
            self.active_effects.remove(name)

    def has_status_effect(self, name: str) -> bool:
        """Check if the enemy has a specific status effect"""
        return name in self.active_effects

    def tick_status_effects(self, player: "Player"): # Player needed for some effects
        """Process status effects at the end of the enemy's turn"""
        to_remove = []
        for effect in list(self.active_effects): # Iterate over a copy to allow modification
            if effect == "Bleeding":
                bleed_damage = 5 # As per design doc
                self.take_damage(bleed_damage)
                # A message should ideally be logged by CombatManager or UI
                # print(f"The {self.name} bleeds for {bleed_damage} damage.")
                
            # Example for timed effects (if durations were tracked)
            # if effect_data.get("duration") is not None:
            #     effect_data["duration"] -= 1
            #     if effect_data["duration"] <= 0:
            #         to_remove.append(effect)
        
        for effect in to_remove:
            self.remove_status_effect(effect)

        # Check for permanent effects that might require stat recalculation
        # For crippled limbs, we assume they persist until healed (e.g., via item or Doctor skill)
        # and affect stats directly or indirectly.
        if "Crippled Leg" in self.active_effects:
            pass # AP regen penalty handled in regenerate_ap
        if "Crippled Arm" in self.active_effects:
            pass # Accuracy penalty handled in get_hit_chance


    def gain_cover(self):
        """Enemy gains cover, increasing defense"""
        self.has_cover = True

    def lose_cover(self):
        """Enemy loses cover"""
        self.has_cover = False

    def decide_action(self, player: "Player") -> Tuple[str, int]:
        """
        Basic AI decision logic based on profile and state.
        Returns action type (str) and AP cost (int).
        """
        hp_percent = self.hp / self.max_hp
        actions_and_costs = [] # (action_name, ap_cost)

        # Action costs for AI
        ATTACK_COST = 5
        POWER_ATTACK_COST = 8
        HEAL_COST = 3 # Assuming a basic heal spell/item
        TAKE_COVER_COST = 3
        FLEE_COST = 4
        END_TURN_COST = 0

        # Prioritize actions based on AI profile
        if self.ai_profile == "Coward":
            if hp_percent < 0.2 and self.current_ap >= FLEE_COST:
                return "flee", FLEE_COST
            if self.hp < self.max_hp * 0.5 and self.current_ap >= HEAL_COST: # Try to heal if low
                return "heal", HEAL_COST
            if self.current_ap >= ATTACK_COST:
                return "attack", ATTACK_COST
            return "end_turn", END_TURN_COST

        if self.ai_profile == "Tactician":
            if not self.has_cover and self.current_ap >= TAKE_COVER_COST:
                return "take_cover", TAKE_COVER_COST
            if self.hp < self.max_hp * 0.5 and self.current_ap >= HEAL_COST:
                return "heal", HEAL_COST
            if self.current_ap >= POWER_ATTACK_COST and random.random() < 0.3: # Chance for power attack
                return "attack", POWER_ATTACK_COST
            if self.current_ap >= ATTACK_COST:
                return "attack", ATTACK_COST
            return "end_turn", END_TURN_COST

        if self.ai_profile == "Berserker":
            if self.current_ap >= POWER_ATTACK_COST: # Berserkers prioritize power attack
                return "attack", POWER_ATTACK_COST # Assuming 'attack' handles power for now
            if self.current_ap >= ATTACK_COST:
                return "attack", ATTACK_COST
            return "end_turn", END_TURN_COST

        # Default fallback (Mixed behavior)
        if self.current_ap >= ATTACK_COST:
            return "attack", ATTACK_COST
        return "end_turn", END_TURN_COST


    def get_loot(self) -> List[Item]:
        """Generate loot when defeated"""
        loot = []
        if not self.loot_table:
            return loot
            
        for item_key in self.loot_table:
            # Support for weighted drops: "item_name:chance"
            chance = 0.5 # Default 50%
            key = item_key
            
            if ":" in item_key:
                parts = item_key.split(":")
                if len(parts) == 2 and parts[1].isdigit():
                    key = parts[0]
                    chance = int(parts[1]) / 100.0

            if random.random() < chance:
                item = create_item(key)
                if item:
                    loot.append(item)
        return loot

    def to_dict(self) -> Dict[str, Any]:
        """Convert enemy to dictionary"""
        return {
            "name": self.name,
            "enemy_id": getattr(self, "enemy_id", ""),
            "description": self.description,
            "level": self.level,
            "max_hp": self.max_hp,
            "hp": self.hp,
            "base_damage": self.base_damage,
            "damage_resistance": self.damage_resistance,
            "xp_reward": self.xp_reward,
            "loot_table": self.loot_table,
            "is_alive": self.is_alive,
            "max_ap": self.max_ap,
            "current_ap": self.current_ap,
            "has_cover": self.has_cover, # New
            "ai_profile": self.ai_profile,
            "active_effects": self.active_effects, # New
            "agility": self.agility,
            "perception": self.perception,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Enemy':
        """Create enemy from dictionary"""
        enemy = cls(
            data["name"],
            data["description"],
            data["level"],
            data["max_hp"],
            data["base_damage"], # Changed to base_damage
            data["xp_reward"],
            data.get("loot_table", []),
            data.get("damage_resistance", 0),
            data.get("ai_profile", "Berserker"),
            data.get("agility", 5), # New
            data.get("perception", 5), # New
            data.get("weapon", "") # New: Weapon ID
        )
        enemy.enemy_id = data.get("enemy_id", "")
        enemy.hp = data["hp"]
        # enemy.is_alive = data["is_alive"] # derived from hp now
        enemy.max_ap = data.get("max_ap", enemy.max_ap) # Use initial max_ap if not found
        enemy.current_ap = data.get("current_ap", enemy.max_ap)
        enemy.has_cover = data.get("has_cover", False) # New
        enemy.active_effects = data.get("active_effects", []) # New
        return enemy

# Global enemy database
ENEMY_DATABASE = {}

def load_enemy_database():
    """Load enemies from JSON data file"""
    global ENEMY_DATABASE
    if ENEMY_DATABASE:
        return
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'enemies.json')
    if not os.path.exists(data_path):
        return
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            ENEMY_DATABASE = json.load(f)
    except Exception as e:
        print(f"Error loading enemy database: {e}")

# Initial load
load_enemy_database()

def create_enemy(enemy_key: str) -> Optional[Enemy]:
    """Create an enemy from the database"""
    if enemy_key not in ENEMY_DATABASE:
        load_enemy_database()
        if enemy_key not in ENEMY_DATABASE:
            return None
    
    data = ENEMY_DATABASE[enemy_key]
    enemy = Enemy(
        data['name'],
        data['description'],
        data['level'],
        data['hp'],
        data['damage'],
        data['xp_reward'],
        data.get('loot_table'),
        data.get('damage_resistance', 0),
        data.get('ai_profile', 'Berserker'),
        data.get('agility', 5), # New
        data.get('perception', 5), # New
        data.get('weapon', "") # New: Weapon ID
    )
    enemy.enemy_id = enemy_key
    return enemy
