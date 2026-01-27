"""
Enemy System
Handles enemy creation, stats, and behavior
"""

import json
import os
import random
from typing import Dict, List, Optional, Any
from item import Item, create_item

class Enemy:
    """Represents an enemy in the game"""
    
    def __init__(self, name: str, description: str, level: int, hp: int, 
                 damage: int, xp_reward: int, loot_table: List[str] = None):
        self.name = name
        self.description = description
        self.level = level
        self.max_hp = hp
        self.hp = hp
        self.damage = damage
        self.xp_reward = xp_reward
        self.loot_table = loot_table or []
        self.is_alive = True
    
    def take_damage(self, amount: int):
        """Take damage from an attack"""
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
    
    def attack(self) -> int:
        """Calculate attack damage"""
        # Simple damage variation +/- 20%
        variance = int(self.damage * 0.2)
        return self.damage + random.randint(-variance, variance)
    
    def get_loot(self) -> List[Item]:
        """Generate loot when defeated"""
        loot = []
        if not self.loot_table:
            return loot
            
        for item_key in self.loot_table:
            # 50% chance for each item in loot table
            if random.random() < 0.5:
                item = create_item(item_key)
                if item:
                    loot.append(item)
        return loot

    def to_dict(self) -> Dict[str, Any]:
        """Convert enemy to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'level': self.level,
            'max_hp': self.max_hp,
            'hp': self.hp,
            'damage': self.damage,
            'xp_reward': self.xp_reward,
            'loot_table': self.loot_table,
            'is_alive': self.is_alive
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Enemy':
        """Create enemy from dictionary"""
        enemy = cls(
            data['name'],
            data['description'],
            data['level'],
            data['max_hp'],
            data['damage'],
            data['xp_reward'],
            data.get('loot_table', [])
        )
        enemy.hp = data['hp']
        enemy.is_alive = data['is_alive']
        return enemy

# Global enemy database
ENEMY_DATABASE = {}

def load_enemy_database():
    """Load enemies from JSON data file"""
    global ENEMY_DATABASE
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
    return Enemy(
        data['name'],
        data['description'],
        data['level'],
        data['hp'],
        data['damage'],
        data['xp_reward'],
        data.get('loot_table')
    )
