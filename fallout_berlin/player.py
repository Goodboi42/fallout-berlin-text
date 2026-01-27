"""
Player Character System
Handles S.P.E.C.I.A.L. stats, skills, and character creation
"""

from typing import Dict, Any, Optional
import random


class Player:
    """Player character with S.P.E.C.I.A.L. stats and skills"""
    
    # Skill list based on Fallout
    SKILLS = [
        'Small Guns', 'Big Guns', 'Energy Weapons', 'Unarmed', 'Melee Weapons',
        'Throwing', 'First Aid', 'Doctor', 'Sneak', 'Lockpick', 'Steal',
        'Traps', 'Science', 'Repair', 'Speech', 'Barter', 'Gambling',
        'Outdoorsman'
    ]
    
    # Origins for character creation
    ORIGINS = {
        'vault_dweller': {
            'name': 'Vault 17 Survivor',
            'description': 'You grew up in Vault 17-Berlin, hidden beneath the Brandenburg Gate.',
            'bonuses': {'Science': 15, 'Repair': 10, 'First Aid': 10},
            'starting_items': ['Vault Suit', 'Pip-Boy', 'Stimpak x3']
        },
        'wastelander': {
            'name': 'Kiez Survivor',
            'description': 'You survived the streets of Neukölln and Kreuzberg, learning to adapt to the chaos.',
            'bonuses': {'Outdoorsman': 15, 'Sneak': 10, 'First Aid': 10},
            'starting_items': ['Leather Armor', '10mm Pistol', 'RadAway x2']
        },
        'ghoul': {
            'name': 'Charité Remnant',
            'description': 'A former medical researcher at the Charité who was too close to the blast. You have seen centuries of Berlin history.',
            'bonuses': {'Radiation Resistance': 50, 'Outdoorsman': 10},
            'starting_items': ['Tattered Clothes', 'Pipe Pistol', 'RadAway x5'],
            'special': 'Radiation immunity, long lifespan, some prejudice'
        },
        'raider': {
            'name': 'U-Bahn Raider',
            'description': 'You were part of the Tunnel Rats, a gang that controls the U1 line.',
            'bonuses': {'Small Guns': 15, 'Melee Weapons': 10, 'Sneak': 10},
            'starting_items': ['Raider Armor', '10mm Pistol', 'Knife']
        },
        'trader': {
            'name': 'Späti Mogul',
            'description': 'Your family ran the most successful underground trade network in the Mitte Ruins.',
            'bonuses': {'Barter': 20, 'Speech': 15, 'Outdoorsman': 10},
            'starting_items': ['Leather Armor', 'Pipe Pistol', 'Caps x200', 'Späti Token']
        },
        'scientist': {
            'name': 'Siemens Technician',
            'description': 'A descendant of the engineers who tried to keep Berlin\'s power grid alive.',
            'bonuses': {'Science': 20, 'Repair': 15, 'Doctor': 10},
            'starting_items': ['Lab Coat', 'Tool Kit', 'Stimpak x2']
        }
    }

    
    def __init__(self, name: str = "Player"):
        self.name = name
        self.origin = None
        
        # S.P.E.C.I.A.L. stats (1-10 each, start at 5)
        self.strength = 5
        self.perception = 5
        self.endurance = 5
        self.charisma = 5
        self.intelligence = 5
        self.agility = 5
        self.luck = 5
        
        # Skills (0-200, start at base values)
        self.skills = {skill: self._calculate_base_skill(skill) for skill in self.SKILLS}
        
        # Derived stats
        self.hit_points = 0
        self.max_hit_points = 0
        self.radiation = 0
        self.max_radiation = 0
        self.action_points = 0
        self.carry_weight = 0
        
        # Equipment
        from fallout_berlin.item import Weapon, Armor
        self.equipped_weapon: Optional[Weapon] = None
        self.equipped_armor: Optional[Armor] = None

        
        # Status effects
        self.status_effects = []
        
        # Experience
        self.level = 1
        self.experience = 0
        self.experience_to_next = 1000
        
        # Starting items will be added during creation
        self._calculate_derived_stats()
    
    def _calculate_base_skill(self, skill: str) -> int:
        """Calculate base skill value from S.P.E.C.I.A.L."""
        skill_map = {
            'Small Guns': 'agility',
            'Big Guns': 'strength',
            'Energy Weapons': 'perception',
            'Unarmed': 'strength',
            'Melee Weapons': 'strength',
            'Throwing': 'agility',
            'First Aid': 'intelligence',
            'Doctor': 'intelligence',
            'Sneak': 'agility',
            'Lockpick': 'perception',
            'Steal': 'agility',
            'Traps': 'perception',
            'Science': 'intelligence',
            'Repair': 'intelligence',
            'Speech': 'charisma',
            'Barter': 'charisma',
            'Gambling': 'luck',
            'Outdoorsman': 'endurance'
        }
        
        primary_stat = getattr(self, skill_map.get(skill, 'intelligence'))
        return primary_stat * 2 + 5
    
    def _calculate_derived_stats(self):
        """Calculate derived stats from S.P.E.C.I.A.L."""
        # Hit Points = 15 + (Endurance * 2) + (Level * 2)
        self.max_hit_points = 15 + (self.endurance * 2) + (self.level * 2)
        if self.hit_points == 0:
            self.hit_points = self.max_hit_points
        
        # Max Radiation = Endurance * 10
        self.max_radiation = self.endurance * 10
        
        # Action Points = 5 + (Agility / 2)
        self.action_points = 5 + (self.agility // 2)
        
        # Carry Weight = 25 + (Strength * 25)
        self.carry_weight = 25 + (self.strength * 25)
    
    def set_origin(self, origin_key: str):
        """Set character origin and apply bonuses"""
        if origin_key not in self.ORIGINS:
            return False
        
        self.origin = origin_key
        origin_data = self.ORIGINS[origin_key]
        
        # Apply skill bonuses
        for skill, bonus in origin_data.get('bonuses', {}).items():
            if skill in self.skills:
                self.skills[skill] += bonus
            elif skill == 'Radiation Resistance':
                # Special handling for ghoul radiation resistance
                pass
        
        return True
    
    def get_origin_data(self) -> Optional[Dict]:
        """Get origin data"""
        if self.origin:
            return self.ORIGINS[self.origin]
        return None
    
    def set_special(self, stat: str, value: int):
        """Set a S.P.E.C.I.A.L. stat (1-10)"""
        if stat.lower() in ['strength', 'perception', 'endurance', 'charisma', 
                           'intelligence', 'agility', 'luck']:
            setattr(self, stat.lower(), max(1, min(10, value)))
            self._calculate_derived_stats()
            # Recalculate skills affected by this stat
            self._recalculate_skills()
    
    def _recalculate_skills(self):
        """Recalculate skills based on current S.P.E.C.I.A.L."""
        for skill in self.SKILLS:
            base = self._calculate_base_skill(skill)
            # Preserve bonuses from origin
            if self.origin:
                origin_data = self.ORIGINS[self.origin]
                bonus = origin_data.get('bonuses', {}).get(skill, 0)
                self.skills[skill] = base + bonus
            else:
                self.skills[skill] = base
    
    def get_skill(self, skill: str) -> int:
        """Get skill value"""
        return self.skills.get(skill, 0)
    
    def modify_skill(self, skill: str, amount: int):
        """Modify skill value"""
        if skill in self.skills:
            self.skills[skill] = max(0, min(200, self.skills[skill] + amount))
    
    def get_skill_check_result(self, skill: str, difficulty: int = 50) -> bool:
        """Perform a skill check (returns True if successful)"""
        skill_value = self.get_skill(skill)
        # Roll 1-100, add skill value, compare to difficulty
        roll = random.randint(1, 100)
        total = roll + skill_value
        return total >= difficulty
    
    def take_damage(self, amount: int):
        """Take damage"""
        self.hit_points = max(0, self.hit_points - amount)
        return self.hit_points <= 0  # Returns True if dead
    
    def heal(self, amount: int):
        """Heal damage"""
        self.hit_points = min(self.max_hit_points, self.hit_points + amount)
    
    def take_radiation(self, amount: int):
        """Take radiation damage"""
        self.radiation = min(self.max_radiation, self.radiation + amount)
        # Radiation reduces max HP
        if self.radiation >= self.max_radiation:
            return True  # Death by radiation
        return False
    
    def cure_radiation(self, amount: int):
        """Reduce radiation"""
        self.radiation = max(0, self.radiation - amount)
    
    def add_experience(self, amount: int):
        """Add experience points"""
        self.experience += amount
        print(f"[+] Gained {amount} XP")
        while self.experience >= self.experience_to_next:
            self.level_up()
    
    def level_up(self):
        """Level up the player"""
        self.experience -= self.experience_to_next
        self.level += 1
        self.experience_to_next = int(self.experience_to_next * 1.5)
        self._calculate_derived_stats()
        # Full heal on level up
        self.hit_points = self.max_hit_points
        print(f"\n[!!!] LEVEL UP! You are now Level {self.level}!")
        
        # Perk-like stat increase
        print("Your survival skills improve. Choose a stat to increase:")
        stats = ['strength', 'perception', 'endurance', 'charisma', 'intelligence', 'agility', 'luck']
        for i, s in enumerate(stats, 1):
            print(f"{i}. {s.capitalize()}")
            
        while True:
            try:
                choice = input("Choice (1-7): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(stats):
                    stat = stats[idx]
                    current = getattr(self, stat)
                    if current < 10:
                        self.set_special(stat, current + 1)
                        print(f"Your {stat.capitalize()} increased to {current + 1}!")
                        break
                    else:
                        print("That stat is already at maximum (10).")
                else:
                    print("Invalid choice.")
            except (ValueError, EOFError):
                # Default to luck if input fails in non-interactive
                self.set_special('luck', min(10, self.luck + 1))
                break
        
        return True

    
    def to_dict(self) -> Dict[str, Any]:
        """Convert player to dictionary for saving"""
        return {
            'name': self.name,
            'origin': self.origin,
            'strength': self.strength,
            'perception': self.perception,
            'endurance': self.endurance,
            'charisma': self.charisma,
            'intelligence': self.intelligence,
            'agility': self.agility,
            'luck': self.luck,
            'skills': self.skills,
            'hit_points': self.hit_points,
            'max_hit_points': self.max_hit_points,
            'radiation': self.radiation,
            'max_radiation': self.max_radiation,
            'level': self.level,
            'experience': self.experience,
            'experience_to_next': self.experience_to_next,
            'status_effects': self.status_effects,
            'equipped_weapon': self.equipped_weapon.to_dict() if self.equipped_weapon else None,
            'equipped_armor': self.equipped_armor.to_dict() if self.equipped_armor else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Player':
        """Create player from dictionary"""
        from fallout_berlin.item import Weapon, Armor
        player = cls(data.get('name', 'Player'))
        player.origin = data.get('origin')
        player.strength = data.get('strength', 5)
        player.perception = data.get('perception', 5)
        player.endurance = data.get('endurance', 5)
        player.charisma = data.get('charisma', 5)
        player.intelligence = data.get('intelligence', 5)
        player.agility = data.get('agility', 5)
        player.luck = data.get('luck', 5)
        player.skills = data.get('skills', {})
        player.hit_points = data.get('hit_points', player.max_hit_points)
        player.max_hit_points = data.get('max_hit_points', player.max_hit_points)
        player.radiation = data.get('radiation', 0)
        player.max_radiation = data.get('max_radiation', player.max_radiation)
        player.level = data.get('level', 1)
        player.experience = data.get('experience', 0)
        player.experience_to_next = data.get('experience_to_next', 1000)
        player.status_effects = data.get('status_effects', [])
        
        if data.get('equipped_weapon'):
            player.equipped_weapon = Weapon.from_dict(data['equipped_weapon'])
        if data.get('equipped_armor'):
            player.equipped_armor = Armor.from_dict(data['equipped_armor'])
            
        player._calculate_derived_stats()
        return player

    
    def get_stat_summary(self) -> str:
        """Get a summary of player stats"""
        return f"""
=== {self.name} ===
Origin: {self.ORIGINS[self.origin]['name'] if self.origin else 'None'}
Level: {self.level} | XP: {self.experience}/{self.experience_to_next}

S.P.E.C.I.A.L.:
  Strength: {self.strength}     Perception: {self.perception}
  Endurance: {self.endurance}   Charisma: {self.charisma}
  Intelligence: {self.intelligence}  Agility: {self.agility}
  Luck: {self.luck}

Health: {self.hit_points}/{self.max_hit_points} HP
Radiation: {self.radiation}/{self.max_radiation} rads
Carry Weight: {self.carry_weight} lbs
"""
